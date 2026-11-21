#ifndef XTREME_RENDER_PROFILE_H
#define XTREME_RENDER_PROFILE_H
#include <stdint.h>

/* XRH1 v1: stable big-endian 32-bit fields read from Saturn WRAM-H.
 * A separate ring avoids changing the existing XTDB v3 and XFP1 contracts.
 * One record per *completed* scene frame. Profiling uses sat_time_ms() on
 * stage boundaries, not a claim of GPU time or independently measured FPS.
 */
#define XTREME_RENDER_HISTORY_CAPACITY 64u
#define XTREME_RENDER_HISTORY_MAGIC 0x58524831u /* "XRH1" */

typedef struct xtreme_render_sample {
    uint32_t frame;
    uint32_t scene_begin_ms;
    uint32_t stage_ms;
    uint32_t actor_ms;
    uint32_t flush_ms;
    uint32_t stage_faces_tested;
    uint32_t stage_visibility_skipped;
    uint32_t stage_lod_skipped;
    uint32_t stage_submitted;
    uint32_t marker_submitted;
    uint32_t actor_submitted;
    uint32_t total_submitted;
    uint32_t total_flushed;
    uint32_t painter_culled;
    uint32_t painter_clipped;
} xtreme_render_sample_t;

typedef struct xtreme_render_history {
    uint32_t magic, version, count, next;
    xtreme_render_sample_t samples[XTREME_RENDER_HISTORY_CAPACITY];
} xtreme_render_history_t;

_Static_assert(sizeof(xtreme_render_sample_t)==15u*4u,
               "XRH1 sample word layout changed");
_Static_assert(sizeof(xtreme_render_history_t)==16u+64u*15u*4u,
               "XRH1 ring layout changed");

/* Copy the final sample before committing the ring's next/count values.
 * The Ymir harness reads only after stopping an entire emulated frame. */
static inline void xtreme_render_history_append(
    volatile xtreme_render_history_t* ring, const xtreme_render_sample_t* frame) {
    const uint32_t slot=ring->next%XTREME_RENDER_HISTORY_CAPACITY;
    ring->samples[slot]=*frame;
    ring->next++;
    if(ring->count<XTREME_RENDER_HISTORY_CAPACITY)ring->count++;
}
#endif
