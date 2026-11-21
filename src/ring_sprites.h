#ifndef XTREME_RING_SPRITES_H
#define XTREME_RING_SPRITES_H
#include <stdint.h>
#include "ring_frame_clock.h"
#include <saturn/scene3d_faces.h>
#include <saturn/core.h>

#define XTREME_RING_FRAME_COUNT 16u
#define XTREME_RING_TEXTURE_SIDE 32u
#define XTREME_RING_PALETTE_BANK 6u

sat_result_t xtreme_ring_sprites_init(void);
const sat_scene3d_material_t* xtreme_ring_sprite_material(uint32_t physics_ticks);
uint32_t xtreme_ring_sprite_vram_bytes(void);

#endif
