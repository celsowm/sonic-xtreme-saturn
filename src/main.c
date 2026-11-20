/* Jade Gully authoring viewer, not gameplay. SDK owns the painter and VDP1. */
#include <saturn/app.h>
#include <saturn/color.h>
#include <saturn/scene.h>
#include "greybox.h"

#define WIDTH 320u
#define HEIGHT 224u
#define CAPACITY (STAGE_FACE_COUNT + 2u * STAGE_ENTITY_COUNT)
#define FX(n) ((sat_fx16_t)((n) * 65536))
_Static_assert(CAPACITY <= 384u, "greybox face budget exceeded");

static sat_scene_t scene;
static sat_scene3d_face_t faces[CAPACITY];
static uint32_t keys[CAPACITY];
static uint16_t order[CAPACITY];
static sat_camera3d_t camera;
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
static int fail(sat_result_t status) {
    xtreme_error = (int32_t)status;
    return 1;
}
int main(void) {
    sat_result_t rc = sat_app_init_default();
    if (rc != SAT_OK) return fail(rc);
    rc = sat_scene_init(&scene,faces,keys,order,CAPACITY);
    if (rc != SAT_OK) return fail(rc);
    rc = set_view(0);
    if (rc != SAT_OK) return fail(rc);
    for (;;) {
        sat_pad_state_t pad = {0};
        rc = sat_app_frame_begin(SAT_RGB555(10,19,27),SAT_RGB555(10,19,27),&pad);
        if (rc != SAT_OK) return fail(rc);
        if (pad.pressed & SAT_PAD_START) {
            rc = sat_app_frame_end();
            if (rc != SAT_OK) return fail(rc);
            break;
        }
        rc = navigate(&pad);
        if (rc != SAT_OK) return fail(rc);
        rc = sat_scene_begin(&scene,&camera,camera.near_z,WIDTH,HEIGHT,0u);
        if (rc != SAT_OK) return fail(rc);
        rc = draw_stage();
        if (rc != SAT_OK) return fail(rc);
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
