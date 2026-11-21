#include "frame_sync_profile.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

int main(void) {
    volatile xtreme_sync_history_t history={
        .magic=XTREME_SYNC_MAGIC,.version=1u
    };
    for(uint32_t n=1;n<=66u;++n) {
        xtreme_sync_sample_t s={
            .frame=n,.frame_interval_ms=n%7u==0u?50u:33u,
            .begin_ms=10u,.end_ms=1u,.prior_end_gap_ms=0u,
            .active_work_ms=23u,
            .field_before_begin=n,.field_after_begin=n+1u,
            .field_before_end=n+1u,.field_after_end=n+1u,
            .draw_waits_begin_delta=1u,.draw_waits_end_delta=0u
        };
        xtreme_sync_history_append(&history,&s);
    }
    assert(history.magic==XTREME_SYNC_MAGIC);
    assert(history.count==64u);
    assert(history.next==66u);
    assert(history.samples[1].frame==66u);
    assert(history.samples[2].frame==3u);
    assert(history.samples[1].begin_ms==10u);
    assert(history.samples[1].draw_waits_begin_delta==1u);
    assert(sizeof(history)==16u+64u*16u*4u);
    puts("frame sync XSW1 ring ok");
    return 0;
}
