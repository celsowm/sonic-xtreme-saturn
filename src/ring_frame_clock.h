#ifndef XTREME_RING_FRAME_CLOCK_H
#define XTREME_RING_FRAME_CLOCK_H
#include <stdint.h>

/* Original mod.ini: FrameIncrement=2. Game physics runs fixed 60 Hz, and
 * the sprite animation is not coupled to the current render cadence.
 */
static inline uint8_t xtreme_ring_frame_index(uint32_t physics_ticks) {
    return (uint8_t)((physics_ticks/2u)&15u);
}
#endif
