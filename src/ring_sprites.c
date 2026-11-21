/* Source sprites: SADX GameBanana #537401, Mr. Malfunction, derived from
 * Sonic X-treme prototype. Not Kenney CC0. User-provided art at build time;
 * offline packing and palette quantization only. No runtime decompression.
 */
#include "ring_sprites.h"
#include "ring_texture_data.h"
#include <saturn/vdp1.h>

static sat_vdp1_texture_t ring_textures[XTREME_RING_FRAME_COUNT];
static sat_scene3d_material_t ring_materials[XTREME_RING_FRAME_COUNT];
static uint8_t ring_ready;

sat_result_t xtreme_ring_sprites_init(void) {
    if(ring_ready)return SAT_OK;
    /* Dedicate one 256-entry CRAM bank and sixteen resident INDEX8 pages.
     * Bank 7 belongs to Jade Gully, so never mutate it at runtime. */
    sat_result_t rc=sat_tex_upload_indexed8(
        &ring_textures[0],xtreme_ring_pixels[0],32u,32u,
        xtreme_ring_palette,XTREME_RING_PALETTE_BANK);
    if(rc!=SAT_OK)return rc;
    for(uint8_t i=1u;i<XTREME_RING_FRAME_COUNT;++i) {
        rc=sat_tex_upload_indexed8_pixels(
            &ring_textures[i],xtreme_ring_pixels[i],32u,32u,
            XTREME_RING_PALETTE_BANK);
        if(rc!=SAT_OK)return rc;
    }
    for(uint8_t i=0u;i<XTREME_RING_FRAME_COUNT;++i) {
        sat_scene3d_material_t* const mat=&ring_materials[i];
        *mat=(sat_scene3d_material_t){0};
        mat->kind=SAT_SCENE3D_INDEXED_TEXTURED;
        mat->texture=&ring_textures[i];
        mat->rgb555=SAT_RGB555(31,27,2); /* near-clip fallback, no blue boxes */
        mat->color_calc_slot=SAT_INDEXED_SOLID_OPAQUE;
        mat->sprite_flags=SAT_SPRITE_FLAG_HIGH_SPEED_SHRINK;
    }
    ring_ready=1u;
    return SAT_OK;
}

const sat_scene3d_material_t* xtreme_ring_sprite_material(uint32_t physics_ticks) {
    if(!ring_ready)return 0;
    return &ring_materials[xtreme_ring_frame_index(physics_ticks)];
}
uint32_t xtreme_ring_sprite_vram_bytes(void) {
    return XTREME_RING_FRAME_COUNT*32u*32u;
}
