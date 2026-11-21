/* Native Sonic R presentation using the repository's generated LibSaturn
 * skeletal C asset. All buffers are caller-owned, no allocations in frames.
 * Motion is gameplay-controller driven; clip root motion is intentionally
 * ignored. No file copying or asset publication in this module. */
#include "sonic_actor.h"
#include "sonic.h"
#include <saturn/character3d.h>
#include <saturn/mesh3d.h>
#include <saturn/model3d.h>
#include <saturn/skin3d.h>
#include <saturn/skeleton3d.h>
#include <saturn/time.h>
#include <saturn/texture_memory.h>
#include <stdint.h>

/* The stock texture registry has 64 handles; this imported model bakes
 * one indexed texture per triangle (148 in the current 159-face LOD).
 * Override the SDK's default table only in the character build.
 * Keep storage in WRAM-L and use a power-of-two hash table. */
#define SONIC_TEXTURE_SLOTS (SONIC_TEXTURE_COUNT + 16u)
static sat_texture_slot_t sonic_texture_slots[SONIC_TEXTURE_SLOTS]
    __attribute__((section(".wram_l")));
static sat_texture_region_slot_t sonic_region_slots[16]
    __attribute__((section(".wram_l")));
static uint16_t sonic_texture_buckets[512]
    __attribute__((section(".wram_l")));
SAT_TEXTURE_MEMORY(sonic_texture_slots,sonic_region_slots,sonic_texture_buckets);

#define SONIC_MAX_JOINTS 32u
#define SONIC_DELTA (SAT_FX16_ONE/60)
#define SONIC_MARGIN (SAT_FX16_ONE/32)
enum {
    SONIC_IDLE, SONIC_RUN, SONIC_JUMP, SONIC_FALLING,
    SONIC_LANDING, SONIC_BRAKE, SONIC_LEFT, SONIC_RIGHT
};
static const sat_skeleton_clip_t* const clips[] = {
    &sonic_clip_idle, &sonic_clip_highspeed, &sonic_clip_jump,
    &sonic_clip_falling, &sonic_clip_landing, &sonic_clip_brake,
    &sonic_clip_turn_left, &sonic_clip_turn_right
};

typedef struct {
    sat_skeleton_instance_t skeleton;
    sat_transform3d_node_t nodes[SONIC_MAX_JOINTS];
    uint16_t scratch[SONIC_MAX_JOINTS];
    sat_skeleton_pose_joint_t pose[SONIC_MAX_JOINTS];
    sat_mat4_t joint_world[SONIC_MAX_JOINTS],world;
    sat_skel_clip_player_t animation;
    sat_mesh_t mesh;
    sat_vec3_t vertices[SONIC_VERTEX_COUNT], world_vertices[SONIC_VERTEX_COUNT];
    sat_projected_vertex_t projected[SONIC_VERTEX_COUNT];
    uint16_t indices[SONIC_FACE_COUNT*4u];
    sat_texture_t textures[SONIC_TEXTURE_COUNT];
    sat_vdp1_texture_t native_textures[SONIC_TEXTURE_COUNT];
    sat_scene3d_material_t materials[SONIC_TEXTURE_COUNT];
    sat_scene3d_instance_t instance;
    sat_scene3d_instance_binding_t immutable_binding;
    sat_aabb3_t bounds;
    uint8_t current_clip,ready,was_grounded,landing_ticks;
} sonic_actor_t;
static sonic_actor_t actor;

/* Stable, source-independent WRAM symbol readable by the Ymir probe.
 * magic = 'SXAC', v3. Independent of the game's XTDB v3 layout. */
typedef struct {
    uint32_t magic,version,enabled,ready,error;
    uint32_t vertices,faces,textures,joints,clip,ticks,draws;
    uint32_t animation_ms,skin_ms,draw_ms;
    int32_t pos_x,pos_y,pos_z;
    uint32_t registry_capacity,init_stage,vram_free;
    uint32_t clip_mask,clip_changes,takeoffs,landings,ground_ticks,air_ticks;
} sonic_debug_state_t;
/* Ymir reads only this completed-frame snapshot, not animation work in progress. */
volatile sonic_debug_state_t xtreme_sonic_debug;
static sonic_debug_state_t sonic_debug_live;

void xtreme_sonic_publish_debug(void) {
    xtreme_sonic_debug=sonic_debug_live;
}

static sat_result_t fail(sat_result_t rc) {
    sonic_debug_live.error=(uint32_t)rc;
    /* Preserve diagnostics even if boot fails before the first completed frame. */
    xtreme_sonic_publish_debug();
    return rc;
}
sat_result_t xtreme_sonic_init(void) {
    sonic_debug_live.magic=0x53584143u; /* SXAC */
    sonic_debug_live.version=3u;
    sonic_debug_live.init_stage=1u;
    sonic_debug_live.enabled=1u;
    sonic_debug_live.vertices=SONIC_VERTEX_COUNT;
    sonic_debug_live.faces=SONIC_FACE_COUNT;
    sonic_debug_live.textures=SONIC_TEXTURE_COUNT;
    sonic_debug_live.joints=sonic_skeleton.joint_count;
    /* Fail with an explicit capacity result before uploading anything.
     * No hidden temporary upload or texture table expansion at runtime. */
    sonic_debug_live.registry_capacity=sat_texture_capacity();
    if(sat_texture_capacity()<SONIC_TEXTURE_COUNT)
        return fail(SAT_ERR_CAPACITY);
    if(sonic_skeleton.joint_count==0 ||
       sonic_skeleton.joint_count>SONIC_MAX_JOINTS ||
       sat_skin_vertex_count(&sonic_skin)!=SONIC_VERTEX_COUNT)
        return fail(SAT_ERR_CAPACITY);
    sat_result_t rc=sat_model_validate(&sonic_asset);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.init_stage=2u;
    rc=sat_skeleton_validate(&sonic_skeleton);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.init_stage=3u;
    rc=sat_skin_validate(&sonic_skin);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_skeleton_instance_init(&actor.skeleton,&sonic_skeleton,
                                  actor.nodes,SONIC_MAX_JOINTS,
                                  actor.scratch,SONIC_MAX_JOINTS);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_skeleton_rest_pose(&sonic_skeleton,actor.pose,SONIC_MAX_JOINTS);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_skel_clip_player_init(&actor.animation,&sonic_clip_idle);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.init_stage=4u;
    rc=sat_mesh_init(&actor.mesh,actor.vertices,SONIC_VERTEX_COUNT,
                     actor.indices,SONIC_FACE_COUNT);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_model_copy_to_mesh(&sonic_asset,&actor.mesh);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_skin_validate_mesh(&sonic_skin,&actor.mesh);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.init_stage=5u;
    rc=sat_character_materials_upload(&sonic_asset,actor.textures,
                                      actor.native_textures,actor.materials,
                                      SONIC_TEXTURE_COUNT);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.init_stage=6u;
    sonic_debug_live.vram_free=sat_vdp1_vram_free_bytes();
    actor.instance=(sat_scene3d_instance_t){0};
    actor.instance.mesh=&actor.mesh;
    actor.instance.materials=actor.materials;
    actor.instance.material_count=SONIC_TEXTURE_COUNT;
    actor.instance.face_materials=sonic_asset.face_texture_indices;
    actor.instance.cull_backfaces=1u;
    actor.instance.world=&actor.world;
    actor.instance.bounds=&actor.bounds;
    /* Faces, indices and all indexed8 materials remain immutable for the
     * lifetime of the character. Validate that binding once at load rather
     * than inspecting 281 material descriptors on every frame. Geometry and
     * bounds remain animated and are updated independently each frame. */
    rc=sat_scene3d_instance_binding_init(&actor.immutable_binding,
        &actor.mesh,actor.materials,SONIC_TEXTURE_COUNT,
        sonic_asset.face_texture_indices);
    if(rc!=SAT_OK)return fail(rc);
    actor.instance.validated_binding=&actor.immutable_binding;
    actor.ready=1u;
    sonic_debug_live.ready=1u;
    sonic_debug_live.init_stage=7u;
    xtreme_sonic_publish_debug();
    return SAT_OK;
}

sat_result_t xtreme_sonic_tick(const xtreme_player_t* player) {
    if(!player||!actor.ready)return fail(SAT_ERR_INVALID_ARG);
    uint8_t next=SONIC_IDLE;
    if(actor.was_grounded&&!player->grounded&&player->velocity.y>0)
        ++sonic_debug_live.takeoffs;
    if(!actor.was_grounded&&player->grounded)
        ++sonic_debug_live.landings;
    if(player->grounded)++sonic_debug_live.ground_ticks;
    else ++sonic_debug_live.air_ticks;
    if(!player->grounded)next=player->velocity.y>0?SONIC_JUMP:SONIC_FALLING;
    else {
        const sat_fx16_t vx=player->velocity.x;
        const sat_fx16_t vz=player->velocity.z;
        if(vx> SAT_FX16_ONE/8 || vx<-SAT_FX16_ONE/8 ||
           vz> SAT_FX16_ONE/8 || vz<-SAT_FX16_ONE/8)
            next=SONIC_RUN;
        else if(actor.was_grounded==0u && actor.landing_ticks==0u)
            actor.landing_ticks=8u;
        if(actor.landing_ticks){next=SONIC_LANDING;--actor.landing_ticks;}
    }
    actor.was_grounded=player->grounded;
    sonic_debug_live.clip_mask|=1u<<next;
    if(actor.current_clip!=next){
        sat_result_t rc=sat_skel_clip_player_set_clip(&actor.animation,clips[next],0);
        if(rc!=SAT_OK)return fail(rc);
        actor.current_clip=next;
        ++sonic_debug_live.clip_changes;
    }
    sat_clip_event_t events[4];
    uint16_t count=0;
    sat_vec3_t root={0,0,0};
    sat_result_t rc=sat_skel_clip_player_advance(&actor.animation,
                 SONIC_DELTA,events,4,&count,&root);
    if(rc!=SAT_OK)return fail(rc);
    ++sonic_debug_live.ticks;
    sonic_debug_live.clip=actor.current_clip;
    return SAT_OK;
}

sat_result_t xtreme_sonic_submit(sat_scene_t* scene,const xtreme_player_t* player) {
    if(!scene||!player||!actor.ready)return fail(SAT_ERR_INVALID_ARG);
    const uint32_t start=sat_time_ms();
    sat_result_t rc=sat_skel_clip_player_sample(&actor.animation,actor.pose,SONIC_MAX_JOINTS);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_skeleton_evaluate(&actor.skeleton,actor.pose,sonic_skeleton.joint_count);
    if(rc!=SAT_OK)return fail(rc);
    rc=sat_skeleton_world_matrices(&actor.skeleton,actor.joint_world,SONIC_MAX_JOINTS);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.animation_ms=sat_time_ms()-start;
    const uint32_t skin_start=sat_time_ms();
    rc=sat_skin_update_mesh(&sonic_skin,actor.joint_world,sonic_skeleton.joint_count,
                            &actor.mesh,SONIC_MARGIN,&actor.bounds);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.skin_ms=sat_time_ms()-skin_start;
    /* The generated bind minimum anchors the feet to the ground, rather than
     * assuming an origin at the soles of this particular GLB. */
    const sat_vec3_t where={
        player->feet.x,
        player->feet.y-sonic_bind_min.y,
        player->feet.z
    };
    rc=sat_mat4_translate(&actor.world,where.x,where.y,where.z);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.pos_x=where.x;
    sonic_debug_live.pos_y=where.y;
    sonic_debug_live.pos_z=where.z;
    const uint32_t draw_start=sat_time_ms();
    rc=sat_scene_submit_instance(scene,&actor.instance,SAT_SCENE3D_SLOT_INHERIT,
                                  actor.projected,actor.world_vertices);
    if(rc!=SAT_OK)return fail(rc);
    sonic_debug_live.draw_ms=sat_time_ms()-draw_start;
    ++sonic_debug_live.draws;
    return SAT_OK;
}
