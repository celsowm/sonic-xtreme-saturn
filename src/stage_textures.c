/* Actual Kenney CC0 Retro Textures Fantasy art, offline-converted to a
 * shared indexed8 palette. Material data is emitted by
 * tools/bake_stage_textures.py from committed 64x64 source PNGs.
 * No invented runtime noise, no per-frame uploads, no dynamic allocation.
 */
#include "stage_textures.h"
#include "stage_texture_data.h"
#include <saturn/vdp1.h>

static sat_vdp1_texture_t stage_textures[XTREME_STAGE_TEXTURE_COUNT];
static sat_scene3d_material_t stage_materials[XTREME_STAGE_TEXTURE_COUNT];
static uint8_t stage_ready;

sat_result_t xtreme_stage_textures_init(void) {
    if (stage_ready) return SAT_OK;
    /* CRAM bank 0: HUD; Sonic uses the managed character palette.
     * The eight 64x64 textures share a separate immutable palette bank 7.
     */
    sat_result_t rc=sat_tex_upload_indexed8(
        &stage_textures[0],stage_pixels[0],
        XTREME_STAGE_TEXTURE_SIZE,XTREME_STAGE_TEXTURE_SIZE,
        stage_palette,XTREME_STAGE_TEXTURE_PALETTE_BANK);
    if(rc!=SAT_OK)return rc;
    for(uint8_t i=1;i<XTREME_STAGE_TEXTURE_COUNT;++i) {
        rc=sat_tex_upload_indexed8_pixels(&stage_textures[i],stage_pixels[i],
                XTREME_STAGE_TEXTURE_SIZE,XTREME_STAGE_TEXTURE_SIZE,
                XTREME_STAGE_TEXTURE_PALETTE_BANK);
        if(rc!=SAT_OK)return rc;
    }
    for(uint8_t i=0;i<XTREME_STAGE_TEXTURE_COUNT;++i) {
        sat_scene3d_material_t* m=&stage_materials[i];
        *m=(sat_scene3d_material_t){0};
        m->kind=SAT_SCENE3D_INDEXED_TEXTURED;
        m->texture=&stage_textures[i];
        m->rgb555=stage_fallback_rgb[i];
        m->color_calc_slot=255u;
        m->sprite_flags=SAT_SPRITE_FLAG_HIGH_SPEED_SHRINK;
    }
    stage_ready=1u;
    return SAT_OK;
}
const sat_scene3d_material_t* xtreme_stage_texture_material(uint8_t id) {
    if(!stage_ready || id>=XTREME_STAGE_TEXTURE_COUNT)return 0;
    return &stage_materials[id];
}
uint32_t xtreme_stage_texture_vram_bytes(void) {
    return XTREME_STAGE_TEXTURE_COUNT*
           XTREME_STAGE_TEXTURE_SIZE*XTREME_STAGE_TEXTURE_SIZE;
}
