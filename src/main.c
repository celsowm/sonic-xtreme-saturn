/* Jade Gully movement prototype. SDK owns the painter and VDP1. */
#include <saturn/app.h>
#include <saturn/color.h>
#include <saturn/scene.h>
#include "greybox.h"
#include "collision.h"
#include "controller.h"
#include <saturn/time.h>

#define WIDTH 320u
#define HEIGHT 224u
#define CAPACITY (STAGE_FACE_COUNT + 2u * STAGE_ENTITY_COUNT + 2u)
#define FX(n) ((sat_fx16_t)((n) * 65536))
_Static_assert(CAPACITY <= 384u, "greybox face budget exceeded");

static sat_scene_t scene;
static sat_scene3d_face_t faces[CAPACITY];
static uint32_t keys[CAPACITY];
static uint16_t order[CAPACITY];
static sat_camera3d_t camera;
static xtreme_player_t player;
static sat_mesh_t ground = {
    collision_vertices, collision_indices,
    COLLISION_VERTEX_COUNT, COLLISION_VERTEX_COUNT,
    COLLISION_FACE_COUNT, COLLISION_FACE_COUNT
};
static uint8_t viewer;
volatile uint32_t xtreme_ticks;
volatile uint32_t xtreme_dropped_ms;
volatile uint32_t xtreme_grounded;
volatile int32_t xtreme_player_x,xtreme_player_y,xtreme_player_z;
static int ground_query(void* ctx,const sat_vec3_t* origin,sat_fx16_t length,
                        sat_vec3_t* point,sat_vec3_t* normal) {
    sat_mesh_t* mesh=ctx;
    sat_ray3_t ray={*origin,{0,-SAT_FX16_ONE,0},length};
    sat_hit3_t hit;
    if (!sat_raycast_mesh(mesh,&ray,&hit)) return 0;
    *point=hit.point;
    *normal=hit.normal;
    if (normal->y<0) {
        normal->x=-normal->x; normal->y=-normal->y; normal->z=-normal->z;
    }
    return 1;
}
static sat_result_t follow_player(void) {
    const sat_vec3_t p=player.feet;
    const sat_vec3_t eye={p.x,p.y+FX(5),p.z+FX(10)};
    const sat_vec3_t target={p.x,p.y+FX(1),p.z-FX(4)};
    const sat_vec3_t up={0,FX(1),0};
    return sat_camera3d_init(&camera,&eye,&target,&up,FX(65),
        sat_fx16_div(FX(WIDTH),FX(HEIGHT)),FX(1),FX(240));
}
static xtreme_input_t sample_input(const sat_pad_state_t* pad) {
    xtreme_input_t in={0,0,0};
    in.x=127*(!!(pad->held&SAT_PAD_RIGHT)-!!(pad->held&SAT_PAD_LEFT));
    in.z=127*(!!(pad->held&SAT_PAD_DOWN)-!!(pad->held&SAT_PAD_UP));
    sat_analog_state_t analog={0};
    if (sat_pad_analog(0,0,&analog)==SAT_OK && analog.axis_count>=2) {
        int x=(int)analog.x-128,z=(int)analog.y-128;
        if (x>12 || x<-12 || z>12 || z<-12) {
            in.x=(int16_t)x; in.z=(int16_t)z;
        }
    }
    return in;
}
/* Inspectable, not a frame-rate claim. */
volatile uint32_t xtreme_frames;
volatile int32_t xtreme_error;
volatile uint32_t xtreme_world_commands;

static const uint16_t colors[] = {
    SAT_RGB555(9,21,7), SAT_RGB555(21,16,6), SAT_RGB555(16,14,12),
    SAT_RGB555(5,15,5), SAT_RGB555(16,11,4)
};
static const uint16_t marker_colors[] = {
    SAT_RGB555(4,12,31), SAT_RGB555(31,26,2), SAT_RGB555(31,4,4),
    SAT_RGB555(3,25,28), SAT_RGB555(22,5,20), SAT_RGB555(31,31,31),
    SAT_RGB555(13,20,31), SAT_RGB555(18,18,18)
};

static sat_vec3_t vec(int x, int y, int z) {
    return (sat_vec3_t){FX(x),FX(y),FX(z)};
}
static sat_result_t set_view(int overview) {
    const sat_vec3_t eye = overview ? vec(75,95,-35) : vec(0,24,14);
    const sat_vec3_t target = overview ? vec(0,3,-66) : vec(0,5,-28);
    const sat_vec3_t up = vec(0,1,0);
    return sat_camera3d_init(&camera,&eye,&target,&up,FX(65),
        sat_fx16_div(FX(WIDTH),FX(HEIGHT)),FX(1),FX(240));
}
static void pan_axis(sat_fx16_t* eye, sat_fx16_t* target,
                     sat_fx16_t delta, sat_fx16_t low, sat_fx16_t high) {
    sat_fx16_t next = *eye + delta;
    if (next >= low && next <= high) {
        *eye = next;
        *target += delta;
    }
}
static sat_result_t navigate(const sat_pad_state_t* pad) {
    if (pad->pressed & SAT_PAD_B) return set_view(0);
    if (pad->pressed & SAT_PAD_A) return set_view(1);
    const sat_fx16_t dx = FX(1) * (!!(pad->held & SAT_PAD_RIGHT) - !!(pad->held & SAT_PAD_LEFT));
    const sat_fx16_t dz = FX(1) * (!!(pad->held & SAT_PAD_DOWN) - !!(pad->held & SAT_PAD_UP));
    const sat_fx16_t dy = FX(1) * (!!(pad->held & SAT_PAD_R) - !!(pad->held & SAT_PAD_L));
    pan_axis(&camera.eye.x,&camera.target.x,dx,FX(-100),FX(100));
    pan_axis(&camera.eye.z,&camera.target.z,dz,FX(-150),FX(50));
    pan_axis(&camera.eye.y,&camera.target.y,dy,FX(4),FX(110));
    return sat_camera3d_update(&camera);
}
static sat_result_t submit(const sat_quad3_t* q, uint16_t rgb) {
    const sat_scene3d_material_t material = {
        .kind = SAT_SCENE3D_RGB, .rgb555 = rgb, .color_calc_slot = 255u
    };
    return sat_scene_submit_quad(&scene,q,&material,0u);
}
static sat_result_t draw_stage(void) {
    sat_result_t rc;
    for (unsigned i=0; i<STAGE_FACE_COUNT; ++i) {
        const stage_face_t* f = &stage_faces[i];
        sat_quad3_t quad;
        for (unsigned k=0;k<4;++k) quad.v[k] = stage_vertices[f->v[k]];
        rc = submit(&quad, colors[f->color]);
        if (rc != SAT_OK) return rc;
    }
    for (unsigned i=0;i<STAGE_ENTITY_COUNT;++i) {
        const stage_entity_t* e = &stage_entities[i];
        const sat_vec3_t p = e->pos;
        const sat_fx16_t r = e->kind == 1 ? FX(1)/2 : FX(1);
        /* Two crossed diamonds, diagnostic markers only. */
        sat_quad3_t q = {{{p.x,p.y+r,p.z},{p.x+r,p.y,p.z},
                          {p.x,p.y-r,p.z},{p.x-r,p.y,p.z}}};
        rc = submit(&q,marker_colors[e->kind]);
        if (rc != SAT_OK) return rc;
        q.v[1] = (sat_vec3_t){p.x,p.y,p.z+r};
        q.v[3] = (sat_vec3_t){p.x,p.y,p.z-r};
        rc = submit(&q,marker_colors[e->kind]);
        if (rc != SAT_OK) return rc;
    }
    return SAT_OK;
}
static sat_result_t draw_player(void) {
    const sat_vec3_t p={player.feet.x,player.feet.y+FX(1),player.feet.z};
    const sat_fx16_t r=FX(1)/2;
    sat_quad3_t q={{{p.x,p.y+r,p.z},{p.x+r,p.y,p.z},
                    {p.x,p.y-r,p.z},{p.x-r,p.y,p.z}}};
    sat_result_t rc=submit(&q,SAT_RGB555(3,10,31));
    if (rc!=SAT_OK) return rc;
    q.v[1]=(sat_vec3_t){p.x,p.y,p.z+r};
    q.v[3]=(sat_vec3_t){p.x,p.y,p.z-r};
    return submit(&q,SAT_RGB555(5,18,31));
}
static int fail(sat_result_t status) {
    xtreme_error = (int32_t)status;
    return 1;
}
int main(void) {
    sat_result_t rc = sat_app_init_default();
    if (rc != SAT_OK) return fail(rc);
    rc = sat_scene_init(&scene,faces,keys,order,CAPACITY);
    if (rc != SAT_OK) return fail(rc);
    for (unsigned i=0;i<STAGE_ENTITY_COUNT;++i)
        if (stage_entities[i].kind==0) xtreme_reset(&player,&stage_entities[i].pos);
    rc=follow_player();
    if (rc!=SAT_OK) return fail(rc);
    uint32_t last=sat_time_ms(), accumulator=0;
    uint8_t jump_pending=0;
    for (;;) {
        sat_pad_state_t pad = {0};
        rc = sat_app_frame_begin(SAT_RGB555(10,19,27),SAT_RGB555(10,19,27),&pad);
        if (rc != SAT_OK) return fail(rc);
        if (pad.pressed & SAT_PAD_START) {
            rc = sat_app_frame_end();
            if (rc != SAT_OK) return fail(rc);
            break;
        }
        const uint32_t now=sat_time_ms();
        uint32_t elapsed=now-last;
        last=now;
        if (pad.pressed&SAT_PAD_X) {
            viewer^=1;
            accumulator=0; jump_pending=0; elapsed=0;
            if (viewer) { rc=set_view(1); if(rc!=SAT_OK) return fail(rc); }
        }
        if (viewer) rc=navigate(&pad);
        else {
            if (pad.pressed&SAT_PAD_B) {
                xtreme_reset(&player,&player.spawn);
                accumulator=0; jump_pending=0; elapsed=0;
            }
            if (pad.pressed&(SAT_PAD_A|SAT_PAD_C)) jump_pending=1;
            if (elapsed>100u) { xtreme_dropped_ms+=elapsed-100u; elapsed=100u; }
            accumulator+=elapsed*60u;
            xtreme_input_t in=sample_input(&pad);
            while(accumulator>=1000u) {
                in.jump=jump_pending;
                jump_pending=0;
                xtreme_tick(&player,in,ground_query,&ground);
                accumulator-=1000u;
                ++xtreme_ticks;
            }
            xtreme_grounded=player.grounded;
            xtreme_player_x=player.feet.x;xtreme_player_y=player.feet.y;xtreme_player_z=player.feet.z;
            rc=follow_player();
        }
        if (rc != SAT_OK) return fail(rc);
        rc = sat_scene_begin(&scene,&camera,camera.near_z,WIDTH,HEIGHT,0u);
        if (rc != SAT_OK) return fail(rc);
        rc = draw_stage();
        if (rc != SAT_OK) return fail(rc);
        rc=draw_player();
        if (rc!=SAT_OK) return fail(rc);
        rc = sat_scene_flush(&scene);
        if (rc != SAT_OK) return fail(rc);
        xtreme_world_commands = scene.world_commands;
        rc = sat_app_frame_end();
        if (rc != SAT_OK) return fail(rc);
        ++xtreme_frames;
    }
    (void)sat_shutdown();
    return 0;
}
