/* Jade Gully movement prototype. SDK owns the painter and VDP1. */
#include <saturn/app.h>
#include <saturn/color.h>
#include <saturn/scene.h>
#include "greybox.h"
#include "collision.h"
#include "controller.h"
#ifdef XTREME_HAS_SONIC
#include "sonic_actor.h"
#endif
#include "debug_clock.h"
#include <saturn/time.h>
#include <saturn/follow_camera3d.h>
#include <saturn/hud.h>
#include <saturn/fmt.h>
#include <saturn/vdp1.h>

#define WIDTH 320u
#define HEIGHT 224u
#ifdef XTREME_HAS_SONIC
#include "sonic.h"
#define CHARACTER_FACES SONIC_FACE_COUNT
#else
#define CHARACTER_FACES 2u
#endif
#define CAPACITY (STAGE_FACE_COUNT + 2u * STAGE_ENTITY_COUNT + CHARACTER_FACES)
#define FX(n) ((sat_fx16_t)((n) * 65536))
_Static_assert(CAPACITY <= 1024u, "scene capacity exceeded");

static sat_scene_t scene;
static sat_scene3d_face_t faces[CAPACITY];
static uint32_t keys[CAPACITY];
static uint16_t order[CAPACITY];
static sat_camera3d_t camera;
static sat_follow_camera3d_t chase;
static uint8_t chase_snap=1;
static sat_vec3_t chase_eye,chase_target;
static xtreme_player_t player;
static sat_mesh_t ground = {
    collision_vertices, collision_indices,
    COLLISION_VERTEX_COUNT, COLLISION_VERTEX_COUNT,
    COLLISION_FACE_COUNT, COLLISION_FACE_COUNT
};
static uint8_t viewer;
enum { DBG_OFF, DBG_COMPACT, DBG_PHYSICS, DBG_CAMERA, DBG_RENDER, DBG_MEMORY, DBG_COUNT };
static unsigned page=DBG_COMPACT, vectors;
static xtreme_clock_t sim_clock;
static sat_ascii_font_t debug_font;
static sat_hud_t debug_hud;
/* Versioned 32-bit big-endian words; raw positions/velocities Q16.16. */
typedef struct {
    uint32_t magic,version,bytes,frames,ticks,ticks_frame,dropped_ms;
    int32_t error,hud_error;
    uint32_t page,geometry,viewer,grounded,respawns;
    int32_t pos[3],vel[3],normal[3],eye[3],target[3];
    int32_t input_x,input_z;
    uint32_t held,pressed,analog_valid,analog_x,analog_y,jump_pending;
    uint32_t ray_valid,ray_hit,ray_face;
    int32_t ray_origin[3],ray_point[3],ray_normal[3],ray_length,ray_distance;
    uint32_t frame_ms,submit_x10,sim_ms,camera_ms,scene_ms,flush_ms,hud_ms;
    uint32_t submitted,flushed,culled,clipped,skipped,rejected,blocked;
    uint32_t world_commands,command_capacity,hud_reserved,hud_used;
    uint32_t frame_stats_valid,late_swaps,draw_waits,draw_timeouts,vram_free;
    uint32_t paused,steps,ray_tick,ray_sampled;
    uint32_t sweep_queries,sweep_hits,jumps,landings,snapshot_begin,snapshot_end;
} xtreme_debug_t;
volatile xtreme_debug_t xtreme_debug;
static xtreme_debug_t debug_live;
/* The probe reads the last completed frame, never the live state. */
static void publish_debug(uint32_t serial) {
    xtreme_debug.snapshot_begin=0;
    debug_live.snapshot_begin=0;debug_live.snapshot_end=serial;
    xtreme_debug=debug_live;
    xtreme_debug.snapshot_begin=serial;
}
#define xtreme_debug debug_live
static uint32_t rate_start,rate_frames;
static void debug_vec(volatile int32_t d[3],const sat_vec3_t* v){
    d[0]=v->x;d[1]=v->y;d[2]=v->z;
}
volatile uint32_t xtreme_ticks;
volatile uint32_t xtreme_dropped_ms;
volatile uint32_t xtreme_grounded;
volatile int32_t xtreme_player_x,xtreme_player_y,xtreme_player_z;
/* The fork overlaps vertically. A grounded player should follow the
 * continuation of the surface under its feet, not automatically climb
 * onto whichever branch happens to be highest inside the step-up window.
 * Broad phase is XZ-only for these vertical casts; exact finite face
 * intersection and normal remain the SDK's responsibility. */
static int support_raycast(const sat_mesh_t* mesh,const sat_ray3_t* ray,sat_hit3_t* best) {
    const sat_vec3_t* p=&ray->origin;
    int64_t expected=player.feet.y;
    if(player.grounded&&player.ground_normal.y>FX(.5)){
        const int64_t h=(int64_t)player.ground_normal.x*(p->x-player.feet.x)
                       +(int64_t)player.ground_normal.z*(p->z-player.feet.z);
        expected-=h/player.ground_normal.y;
    }
    int found=0;
    int64_t best_score=0;
    for(uint16_t i=0;i<mesh->face_count;++i){
        sat_quad3_t q;
        for(unsigned j=0;j<4;++j)q.v[j]=mesh->vertices[mesh->indices[4u*i+j]];
        sat_fx16_t lx=q.v[0].x,hx=lx,lz=q.v[0].z,hz=lz;
        for(unsigned j=1;j<4;++j){
            if(q.v[j].x<lx)lx=q.v[j].x;
            if(q.v[j].x>hx)hx=q.v[j].x;
            if(q.v[j].z<lz)lz=q.v[j].z;
            if(q.v[j].z>hz)hz=q.v[j].z;
        }
        if(p->x<lx-2||p->x>hx+2||p->z<lz-2||p->z>hz+2)continue;
        sat_hit3_t hit;
        if(!sat_raycast_quad3(&q,ray,&hit))continue;
        if(hit.normal.y<0){hit.normal.x=-hit.normal.x;hit.normal.y=-hit.normal.y;hit.normal.z=-hit.normal.z;}
        if(hit.normal.y<FX(.5))continue;
        int64_t score=hit.t;
        if(player.grounded){
            score=(int64_t)hit.point.y-expected;
            if(score<0)score=-score;
        }
        if(!found||score<best_score||(score==best_score&&hit.t<best->t)){
            hit.face=i; *best=hit; best_score=score;found=1;
        }
    }
    return found;
}
static int ground_query(void* ctx,const sat_vec3_t* origin,sat_fx16_t length,
                        sat_vec3_t* point,sat_vec3_t* normal) {
    sat_mesh_t* mesh=ctx;
    sat_ray3_t ray={*origin,{0,-SAT_FX16_ONE,0},length};
    sat_hit3_t hit;
    xtreme_debug.ray_valid=1;xtreme_debug.ray_sampled=1;xtreme_debug.ray_tick=xtreme_ticks+1u;xtreme_debug.ray_hit=0;xtreme_debug.ray_face=0xffffu;
    debug_vec(xtreme_debug.ray_origin,origin);xtreme_debug.ray_length=length;
    if (!support_raycast(mesh,&ray,&hit)) {
        /* Expensive edge recovery is useful only while maintaining support.
         * Ordinary airborne misses are expected, not a reason to sweep. */
        if(!player.grounded)return 0;
        /* Recover a missed seam within 12 cm; downward support cast only. */
        const sat_fx16_t radius=FX(0.12);
        const sat_sphere_t sphere={{origin->x,origin->y+radius,origin->z},radius};
        const sat_vec3_t displacement={0,-length,0};
        sat_sphere_mesh_hit_t sh;
        uint8_t found=0;
        ++xtreme_debug.sweep_queries;
        const sat_result_t sr=sat_sphere_cast_mesh(mesh,&sphere,&displacement,&sh,&found);
        if(sr!=SAT_OK){xtreme_debug.error=sr;return 0;}
        if(!found||sh.normal.y<FX(.5))return 0;
        const int64_t horizontal=(int64_t)sh.normal.x*(origin->x-sh.point.x)
                                +(int64_t)sh.normal.z*(origin->z-sh.point.z);
        const int64_t y=(int64_t)sh.point.y-horizontal/sh.normal.y;
        if(y>origin->y||y<(int64_t)origin->y-length)return 0;
        hit.point=(sat_vec3_t){origin->x,(sat_fx16_t)y,origin->z};
        hit.normal=sh.normal;hit.face=sh.face;
        ++xtreme_debug.sweep_hits;
    }
    xtreme_debug.ray_hit=1;xtreme_debug.ray_face=hit.face;
    xtreme_debug.ray_distance=origin->y-hit.point.y;
    debug_vec(xtreme_debug.ray_point,&hit.point);
    *point=hit.point;
    *normal=hit.normal;
    if (normal->y<0) {
        normal->x=-normal->x; normal->y=-normal->y; normal->z=-normal->z;
    }
    debug_vec(xtreme_debug.ray_normal,normal);
    return 1;
}
static sat_result_t chase_step(void) {
    const sat_vec3_t eye={0,FX(5),FX(10)};
    const sat_vec3_t target={player.velocity.x*4,FX(1),-FX(4)+player.velocity.z*4};
    sat_result_t rc=sat_follow_camera3d_set_offsets(&chase,&eye,&target);
    if(rc!=SAT_OK)return rc;
    rc=sat_follow_camera3d_step(&chase,&player.feet,chase_snap,&chase_eye,&chase_target);
    chase_snap=0;
    return rc;
}
static sat_result_t follow_player(void) {
    if(chase_snap){sat_result_t rc=chase_step();if(rc!=SAT_OK)return rc;}
    const sat_vec3_t up={0,FX(1),0};
    return sat_camera3d_init(&camera,&chase_eye,&chase_target,&up,FX(65),
        sat_fx16_div(FX(WIDTH),FX(HEIGHT)),FX(1),FX(240));
}
static xtreme_input_t sample_input(const sat_pad_state_t* pad) {
    xtreme_input_t in={0,0,0};
    in.x=127*(!!(pad->held&SAT_PAD_RIGHT)-!!(pad->held&SAT_PAD_LEFT));
    in.z=127*(!!(pad->held&SAT_PAD_DOWN)-!!(pad->held&SAT_PAD_UP));
    sat_analog_state_t analog={0};
    xtreme_debug.analog_valid=0;
    if (sat_pad_analog(0,0,&analog)==SAT_OK && analog.axis_count>=2) {
        xtreme_debug.analog_valid=1;xtreme_debug.analog_x=analog.x;xtreme_debug.analog_y=analog.y;
        int x=(int)analog.x-128,z=(int)analog.y-128;
        if (x>12 || x<-12 || z>12 || z<-12) {
            in.x=(int16_t)x; in.z=(int16_t)z;
        }
    }
    xtreme_debug.input_x=in.x;xtreme_debug.input_z=in.z;
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
#ifdef XTREME_HAS_SONIC
    return xtreme_sonic_submit(&scene,&player);
#else
    const sat_vec3_t p={player.feet.x,player.feet.y+FX(1),player.feet.z};
    const sat_fx16_t r=FX(1)/2;
    sat_quad3_t q={{{p.x,p.y+r,p.z},{p.x+r,p.y,p.z},
                    {p.x,p.y-r,p.z},{p.x-r,p.y,p.z}}};
    sat_result_t rc=submit(&q,SAT_RGB555(3,10,31));
    if (rc!=SAT_OK) return rc;
    q.v[1]=(sat_vec3_t){p.x,p.y,p.z+r};
    q.v[3]=(sat_vec3_t){p.x,p.y,p.z-r};
    return submit(&q,SAT_RGB555(5,18,31));
#endif
}
/* One glyph can consume one command. Reserve worst-case rows, not estimates. */
#define DMAX 38u
static const uint8_t debug_rows[DBG_COUNT]={0,6,16,9,12,7};
static unsigned debug_row;
static uint16_t debug_budget(void){
    return (uint16_t)(debug_rows[page]*(DMAX+1u)+(vectors?3u:0u));
}
#define DTRY(e) do{sat_result_t st=(e);if(st!=SAT_OK)return st;}while(0)
static sat_result_t dline(const char* s){
    unsigned n=0;
    while(s[n]){if(n>=DMAX)return SAT_ERR_CAPACITY;++n;}
    if(debug_row>=debug_rows[page])return SAT_ERR_CAPACITY;
    const int y=4+10*(int)debug_row++;
    DTRY(sat_draw_rect_screen(3,y-1,(uint16_t)(n*8+2),9,SAT_RGB555(2,3,5)));
    return sat_hud_text(&debug_hud,s,4,y);
}
static int dappend(char* buf,unsigned* n,const char* s){
    while(*s){if(*n>=DMAX)return 0;buf[(*n)++]=*s++;}
    buf[*n]=0;return 1;
}
static sat_result_t dpair(const char* a,uint32_t av,const char* b,uint32_t bv){
    char buf[DMAX+1],num[SAT_FMT_U32_MAX];unsigned n=0;
    if(!dappend(buf,&n,a)||sat_fmt_u32(av,num,sizeof(num),0)!=SAT_OK||!dappend(buf,&n,num))return SAT_ERR_CAPACITY;
    if(b&&(!dappend(buf,&n,b)||sat_fmt_u32(bv,num,sizeof(num),0)!=SAT_OK||!dappend(buf,&n,num)))return SAT_ERR_CAPACITY;
    return dline(buf);
}
static sat_result_t dsigned(const char* label,int32_t v){
    char buf[DMAX+1],num[SAT_FMT_I32_MAX];unsigned n=0;
    if(sat_fmt_i32(v,num,sizeof(num),0)!=SAT_OK||!dappend(buf,&n,label)||!dappend(buf,&n,num))return SAT_ERR_CAPACITY;
    return dline(buf);
}
static sat_result_t dvec(const char* label,const volatile int32_t v[3],int scale){
    char buf[DMAX+1],num[SAT_FMT_FX16_MAX];unsigned n=0;
    if(!dappend(buf,&n,label))return SAT_ERR_CAPACITY;
    for(unsigned i=0;i<3;++i){
        int64_t raw=(int64_t)v[i]*scale;
        if(raw>INT32_MAX)raw=INT32_MAX;
        if(raw<INT32_MIN)raw=INT32_MIN;
        if(sat_fmt_fx16((int32_t)raw,1,num,sizeof(num),0)!=SAT_OK||(i&&!dappend(buf,&n," "))||!dappend(buf,&n,num))return SAT_ERR_CAPACITY;
    }
    return dline(buf);
}
static sat_vec3_t dload(const volatile int32_t v[3]){return(sat_vec3_t){v[0],v[1],v[2]};}
static sat_result_t dsegment(const sat_vec3_t* a,const sat_vec3_t* b,uint16_t color){
    int16_t x0,y0,x1,y1;
    if(sat_project_to_screen(&camera.view_proj,a->x,a->y,a->z,320,224,&x0,&y0)!=SAT_OK||
       sat_project_to_screen(&camera.view_proj,b->x,b->y,b->z,320,224,&x1,&y1)!=SAT_OK)return SAT_OK;
    if(x0<0||x0>=320||x1<0||x1>=320||y0<0||y0>=224||y1<0||y1>=224)return SAT_OK;
    const sat_line_cmd_t cmd={x0-160,y0-112,x1-160,y1-112,color,0};
    return sat_vdp1_draw_line(&cmd);
}
static sat_result_t dgeometry(void){
    sat_vec3_t a,b;
    if(xtreme_debug.ray_valid){
        a=dload(xtreme_debug.ray_origin);b=a;b.y-=xtreme_debug.ray_length;
        if(xtreme_debug.ray_hit)b=dload(xtreme_debug.ray_point);
        DTRY(dsegment(&a,&b,SAT_RGB555(31,4,4)));
        if(xtreme_debug.ray_hit){
            a=b;b.x+=xtreme_debug.ray_normal[0];b.y+=xtreme_debug.ray_normal[1];b.z+=xtreme_debug.ray_normal[2];
            DTRY(dsegment(&a,&b,SAT_RGB555(5,31,10)));
        }
    }
    a=dload(xtreme_debug.pos);a.y+=SAT_FX16_ONE;b=a;
    b.x+=xtreme_debug.vel[0]*4;b.y+=xtreme_debug.vel[1]*4;b.z+=xtreme_debug.vel[2]*4;
    return dsegment(&a,&b,SAT_RGB555(31,25,4));
}
#define DV(a,v) DTRY(dpair(a,v,0,0))
#define DP(a,v,b,w) DTRY(dpair(a,v,b,w))
static sat_result_t draw_debug(void){
    if(!page&&!vectors)return SAT_OK;
    DTRY(sat_vdp1_overlay_begin());
    if(vectors)DTRY(dgeometry());
    if(!page)return SAT_OK;
    debug_row=0;
    switch(page){
    case DBG_COMPACT:
        DTRY(dline("XTREME DEBUG  Y:NEXT Z:VECTORS"));
        DTRY(dline(viewer?"VIEWER":(sim_clock.paused?"PAUSED L:RUN R:STEP":(player.grounded?"GROUNDED":"AIRBORNE"))));
        DV("TICK ",xtreme_debug.ticks);
        DP("MS ",xtreme_debug.frame_ms," SUB/S X10 ",xtreme_debug.submit_x10);
        DTRY(dvec("VEL M/S ",xtreme_debug.vel,60));
        DTRY(dsigned("ERROR ",xtreme_debug.hud_error?xtreme_debug.hud_error:xtreme_debug.error));
        break;
    case DBG_PHYSICS:
        DTRY(dline("PHYSICS  Y:NEXT Z:VECTORS"));
        DTRY(dline(player.grounded?"GROUNDED":"AIRBORNE"));
        DTRY(dline(sim_clock.paused?"PAUSED L:RUN R:STEP":"RUNNING L:PAUSE"));
        DTRY(dvec("POS M ",xtreme_debug.pos,1));
        DTRY(dvec("VEL M/S ",xtreme_debug.vel,60));
        DTRY(dvec("NORMAL ",xtreme_debug.normal,1));
        DTRY(dline(!xtreme_debug.ray_valid?"RAY NOT SAMPLED":(xtreme_debug.ray_hit?"LAST RAY HIT":"LAST RAY MISS")));
        DP("RAY TICK ",xtreme_debug.ray_tick," NEW ",xtreme_debug.ray_sampled);
        if(xtreme_debug.ray_valid&&xtreme_debug.ray_hit){
            DV("FACE ",xtreme_debug.ray_face);
            DTRY(dvec("HIT M ",xtreme_debug.ray_point,1));
            DV("DIST MM ",(uint32_t)(((int64_t)xtreme_debug.ray_distance*1000)/65536));
        }else DTRY(dline("FACE/DIST N/A"));
        DP("TICK ",xtreme_debug.ticks," FRAME ",xtreme_debug.ticks_frame);
        DP("JUMP ",xtreme_debug.jump_pending," RESET ",xtreme_debug.respawns);
        DV("DROPPED MS ",xtreme_debug.dropped_ms);
        DP("SWEEP ",xtreme_debug.sweep_hits," / ",xtreme_debug.sweep_queries);
        DP("JUMPS ",xtreme_debug.jumps," LAND ",xtreme_debug.landings);
        break;
    case DBG_CAMERA:
        DTRY(dline("CAMERA / INPUT"));
        DTRY(dline(viewer?"MODE VIEWER":"MODE CHASE"));
        DTRY(dvec("EYE ",xtreme_debug.eye,1));DTRY(dvec("TARGET ",xtreme_debug.target,1));
        DP("HELD ",xtreme_debug.held," PRESS ",xtreme_debug.pressed);
        if(xtreme_debug.analog_valid){DP("ANALOG X ",xtreme_debug.analog_x," Y ",xtreme_debug.analog_y);}
        else DTRY(dline("ANALOG N/A"));
        DTRY(dsigned("INPUT X ",xtreme_debug.input_x));DTRY(dsigned("INPUT Z ",xtreme_debug.input_z));
        DTRY(dline("OCCLUSION N/A"));break;
    case DBG_RENDER:
        DTRY(dline("RENDER / TIMING"));
        DP("MS ",xtreme_debug.frame_ms," SUB/S X10 ",xtreme_debug.submit_x10);
        DP("FACES ",xtreme_debug.submitted," FLUSH ",xtreme_debug.flushed);
        DP("CULLED ",xtreme_debug.culled," CLIP ",xtreme_debug.clipped);
        DP("SKIP ",xtreme_debug.skipped," REJECT ",xtreme_debug.rejected);
        DV("BUDGET BLOCK ",xtreme_debug.blocked);
        DP("WORLD CMD ",xtreme_debug.world_commands," CAP ",xtreme_debug.command_capacity);
        DP("HUD RES ",xtreme_debug.hud_reserved," PREV USED ",xtreme_debug.hud_used);
        DP("SIM MS ",xtreme_debug.sim_ms," CAM ",xtreme_debug.camera_ms);
        DP("SCENE MS ",xtreme_debug.scene_ms," FLUSH ",xtreme_debug.flush_ms);
        DV("PREV HUD MS ",xtreme_debug.hud_ms);
        if(xtreme_debug.frame_stats_valid){DP("LATE ",xtreme_debug.late_swaps," TIMEOUT ",xtreme_debug.draw_timeouts);}
        else { DTRY(dline("FRAME STATS N/A")); }
        break;
    case DBG_MEMORY:
        DTRY(dline("MEMORY / ASSETS"));
        DV("VDP1 TEX FREE B ",xtreme_debug.vram_free);
        DP("RENDER ",STAGE_FACE_COUNT," COLL ",COLLISION_FACE_COUNT);
        DV("ENTITIES ",STAGE_ENTITY_COUNT);
        DTRY(dline("WRAM-H/L N/A"));DTRY(dline("VDP2/SCSP N/A"));DTRY(dline("SECTOR/LOD/STREAM N/A"));break;
    default:return SAT_ERR_INVALID_ARG;
    }
    return SAT_OK;
}
static int fail(sat_result_t status) {
    xtreme_error = (int32_t)status;
    xtreme_debug.error=status;
    return 1;
}
int main(void) {
    sat_result_t rc = sat_app_init_default();
    if (rc != SAT_OK) return fail(rc);
    xtreme_debug.magic=0x58544442u;xtreme_debug.version=3;
    xtreme_debug.bytes=sizeof(xtreme_debug);
    rc=sat_hud_init_default(&debug_hud,&debug_font);
    if(rc!=SAT_OK)return fail(rc);
    rc = sat_scene_init(&scene,faces,keys,order,CAPACITY);
    if (rc != SAT_OK) return fail(rc);
#ifdef XTREME_HAS_SONIC
    rc=xtreme_sonic_init();
    if(rc!=SAT_OK)return fail(rc);
#endif
    for (unsigned i=0;i<STAGE_ENTITY_COUNT;++i)
        if (stage_entities[i].kind==0) xtreme_reset(&player,&stage_entities[i].pos);
    rc=sat_follow_camera3d_init(&chase,&player.feet,4,6,4);
    if(rc!=SAT_OK)return fail(rc);
    rc=follow_player();
    if (rc!=SAT_OK) return fail(rc);
    uint32_t last=sat_time_ms();
    rate_start=last;
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
        xtreme_debug.frame_ms=elapsed;
        if(now-rate_start>=1000u){
            xtreme_debug.submit_x10=(uint32_t)(((uint64_t)(xtreme_frames-rate_frames)*10000u)/(now-rate_start));
            rate_start=now;rate_frames=xtreme_frames;
        }
        if(pad.pressed&SAT_PAD_Y)page=(page+1u)%DBG_COUNT;
        if(pad.pressed&SAT_PAD_Z)vectors^=1u;
        xtreme_debug.page=page;xtreme_debug.geometry=vectors;
        xtreme_debug.held=pad.held;xtreme_debug.pressed=pad.pressed;
        xtreme_debug.ticks_frame=0;xtreme_debug.sim_ms=0;xtreme_debug.ray_sampled=0;
        xtreme_debug.analog_valid=0;xtreme_debug.input_x=0;xtreme_debug.input_z=0;
        if (pad.pressed&SAT_PAD_X) {
            viewer^=1;
            if(!viewer)chase_snap=1;
            xtreme_clock_clear(&sim_clock); jump_pending=0; elapsed=0;
            if (viewer) { rc=set_view(1); if(rc!=SAT_OK) return fail(rc); }
        }
        uint32_t camera_start=sat_time_ms();
        if (viewer) rc=navigate(&pad);
        else {
            if (pad.pressed&SAT_PAD_B) {
                xtreme_reset(&player,&player.spawn);
                ++xtreme_debug.respawns;chase_snap=1;
                xtreme_clock_clear(&sim_clock); jump_pending=0; elapsed=0;
                xtreme_debug.ray_valid=0;
            }
            if (pad.pressed&(SAT_PAD_A|SAT_PAD_C)) jump_pending=1;
            const int toggle=(pad.pressed&SAT_PAD_L)!=0u;
            const int step=(pad.pressed&SAT_PAD_R)!=0u;
            if(toggle)jump_pending=0;
            const unsigned ticks=xtreme_clock_frame(&sim_clock,elapsed,toggle,step,0);
            if(sim_clock.paused&&ticks)++xtreme_debug.steps;
            xtreme_dropped_ms=sim_clock.dropped_ms;
            xtreme_input_t in=sample_input(&pad);
            const uint32_t sim_start=sat_time_ms();
            for(unsigned tick=0;tick<ticks;++tick) {
                in.jump=jump_pending;
                jump_pending=0;
                const sat_vec3_t before=player.feet;
                const uint8_t was_grounded=player.grounded;
                xtreme_tick(&player,in,ground_query,&ground);
#ifdef XTREME_HAS_SONIC
                rc=xtreme_sonic_tick(&player);if(rc!=SAT_OK)return fail(rc);
#endif
                if(player.feet.x==player.spawn.x&&player.feet.y==player.spawn.y&&player.feet.z==player.spawn.z&&
                   (before.x!=player.spawn.x||before.y!=player.spawn.y||before.z!=player.spawn.z)&&!player.grounded)
                    {++xtreme_debug.respawns;xtreme_debug.ray_valid=0;chase_snap=1;}
                else {
                    if(was_grounded&&!player.grounded&&in.jump&&player.velocity.y>0)++xtreme_debug.jumps;
                    if(!was_grounded&&player.grounded)++xtreme_debug.landings;
                }
                rc=chase_step();if(rc!=SAT_OK)return fail(rc);
                ++xtreme_debug.ticks_frame;
                ++xtreme_ticks;
            }
            xtreme_grounded=player.grounded;
            xtreme_player_x=player.feet.x;xtreme_player_y=player.feet.y;xtreme_player_z=player.feet.z;
            xtreme_debug.sim_ms=sat_time_ms()-sim_start;
            camera_start=sat_time_ms();
            rc=follow_player();
        }
        if (rc != SAT_OK) return fail(rc);
        xtreme_debug.camera_ms=sat_time_ms()-camera_start;
        xtreme_debug.viewer=viewer;xtreme_debug.grounded=player.grounded;xtreme_debug.paused=sim_clock.paused;
        xtreme_debug.ticks=xtreme_ticks;xtreme_debug.dropped_ms=xtreme_dropped_ms;xtreme_debug.jump_pending=jump_pending;
        debug_vec(xtreme_debug.pos,&player.feet);debug_vec(xtreme_debug.vel,&player.velocity);
        debug_vec(xtreme_debug.normal,&player.ground_normal);
        debug_vec(xtreme_debug.eye,&camera.eye);debug_vec(xtreme_debug.target,&camera.target);
        const uint32_t scene_start=sat_time_ms();
        const uint16_t reserved=debug_budget();
        xtreme_debug.hud_reserved=reserved;
        rc = sat_scene_begin(&scene,&camera,camera.near_z,WIDTH,HEIGHT,reserved);
        if (rc != SAT_OK) return fail(rc);
        rc = draw_stage();
        if (rc != SAT_OK) return fail(rc);
        rc=draw_player();
        if (rc!=SAT_OK) return fail(rc);
        const uint32_t flush_start=sat_time_ms();
        xtreme_debug.scene_ms=flush_start-scene_start;
        rc=sat_scene_flush(&scene);
        xtreme_debug.flush_ms=sat_time_ms()-flush_start;
        if(rc!=SAT_OK&&rc!=SAT_ERR_CAPACITY)return fail(rc);
        if(rc!=SAT_OK){xtreme_debug.error=rc;xtreme_error=rc;}
        xtreme_world_commands=scene.world_commands;
        xtreme_debug.world_commands=scene.world_commands;
        xtreme_debug.submitted=scene.submitted_faces;xtreme_debug.flushed=scene.flushed_faces;
        xtreme_debug.culled=scene.culled_faces;xtreme_debug.clipped=scene.clipped_faces;
        xtreme_debug.skipped=scene.skipped_faces;xtreme_debug.rejected=scene.rejected_faces;
        xtreme_debug.blocked=scene.budget_blocked_faces;xtreme_debug.command_capacity=scene.commands_capacity;
        xtreme_debug.vram_free=sat_vdp1_vram_free_bytes();
        sat_vdp1_frame_stats_t fs={0};
        xtreme_debug.frame_stats_valid=sat_vdp1_frame_stats(&fs)==SAT_OK;
        if(xtreme_debug.frame_stats_valid){
            xtreme_debug.late_swaps=fs.late_swaps;xtreme_debug.draw_waits=fs.draw_waits;xtreme_debug.draw_timeouts=fs.draw_timeouts;
        }
        sat_vdp1_command_stats_t pre={0},post={0};
        const int pre_ok=sat_vdp1_command_stats(&pre)==SAT_OK;
        const uint32_t hud_start=sat_time_ms();
        rc=draw_debug();
        if(rc!=SAT_OK)xtreme_debug.hud_error=rc;
        if(sat_vdp1_command_stats(&post)==SAT_OK&&pre_ok&&post.used>=pre.used)
            xtreme_debug.hud_used=post.used-pre.used;
        xtreme_debug.hud_ms=sat_time_ms()-hud_start;
        rc = sat_app_frame_end();
        if (rc != SAT_OK) return fail(rc);
        ++xtreme_frames;
        xtreme_debug.frames=xtreme_frames;
        publish_debug(xtreme_frames);
    }
    (void)sat_shutdown();
    return 0;
}
