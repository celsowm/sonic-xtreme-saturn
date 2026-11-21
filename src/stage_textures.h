#ifndef XTREME_STAGE_TEXTURES_H
#define XTREME_STAGE_TEXTURES_H

#include <stdint.h>
#include <saturn/core.h>
#include <saturn/scene3d_faces.h>

/* Versioned 64x64 indexed8 materials for Jade Gully Adventure.
 * Palette entries and pixel bytes are checked into the repository.
 * The stock-Saturn VDP1 consumes these as real textured polygons. */
#define XTREME_STAGE_TEXTURE_COUNT 8u
#define XTREME_STAGE_TEXTURE_SIZE 64u
#define XTREME_STAGE_TEXTURE_PALETTE_BANK 7u

sat_result_t xtreme_stage_textures_init(void);
const sat_scene3d_material_t* xtreme_stage_texture_material(uint8_t id);
uint32_t xtreme_stage_texture_vram_bytes(void);

#endif
