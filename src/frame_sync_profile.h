#ifndef XTREME_FRAME_SYNC_PROFILE_H
#define XTREME_FRAME_SYNC_PROFILE_H
#include <stdint.h>

/* XSW1 v1: completed-frame instrumentation of BOTH app calls.
 * SDK control 08e39e9: sat_app_frame_begin() calls sat_wait_vblank()
 * (including the VDP1 swap-request wait) before begin_frame; frame_end()
 * calls sat_end_frame() / VDP1 list submit, and is not the VBlank wait.
 * These are call durations, NOT separate VBlank vs swap waiting times.
 *
 * All fields are big-endian uint32 on Saturn WRAM-H. 64-frame ring,
 * independent of XTDB v3, XFP1 and XRH1 binary contracts.
 */
#define XTREME_SYNC_MAGIC 0x58535731u /* "XSW1" */
#define XTREME_SYNC_CAPACITY 64u
#define XTREME_SYNC_WORDS 16u

typedef struct xtreme_sync_sample {
    uint32_t frame;
    uint32_t frame_interval_ms;      /* begin-completion to begin-completion */
    uint32_t begin_ms;               /* entire sat_app_frame_begin call */
    uint32_t end_ms;                 /* entire sat_app_frame_end call */
    uint32_t prior_end_gap_ms;       /* previous end-return to begin-call entry */
    uint32_t active_work_ms;         /* begin-return to end-call entry */
    uint32_t field_before_begin;
    uint32_t field_after_begin;
    uint32_t field_before_end;
    uint32_t field_after_end;
    uint32_t draw_waits_begin_delta;
    uint32_t draw_waits_end_delta;
    uint32_t late_swaps_begin_delta;
    uint32_t late_swaps_end_delta;
    uint32_t draw_timeouts_begin_delta;
    uint32_t draw_timeouts_end_delta;
} xtreme_sync_sample_t;

typedef struct xtreme_sync_history {
    uint32_t magic,version,count,next;
    xtreme_sync_sample_t samples[XTREME_SYNC_CAPACITY];
} xtreme_sync_history_t;

_Static_assert(sizeof(xtreme_sync_sample_t)==XTREME_SYNC_WORDS*4u,
               "XSW1 sample ABI changed");
_Static_assert(sizeof(xtreme_sync_history_t)==16u+
               XTREME_SYNC_CAPACITY*XTREME_SYNC_WORDS*4u,
               "XSW1 history ABI changed");

/* The emulator snapshots once a completed game frame has been committed.
 * Write the record before advancing the ring cursor/count. */
static inline void xtreme_sync_history_append(
    volatile xtreme_sync_history_t* history,
    const xtreme_sync_sample_t* sample) {
    const uint32_t idx=history->next%XTREME_SYNC_CAPACITY;
    history->samples[idx]=*sample;
    ++history->next;
    if(history->count<XTREME_SYNC_CAPACITY)++history->count;
}
#endif
