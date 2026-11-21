#include "render_profile.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    volatile xtreme_render_history_t ring={0};
    ring.magic=XTREME_RENDER_HISTORY_MAGIC;
    ring.version=1;
    for(uint32_t i=1;i<=66;i++){
        const xtreme_render_sample_t sample={
            .frame=i,.scene_begin_ms=1,.stage_ms=20,
            .actor_ms=3,.flush_ms=8,.stage_faces_tested=460,
            .stage_visibility_skipped=80,.stage_lod_skipped=25,
            .stage_submitted=305,.marker_submitted=8,
            .actor_submitted=90,.total_submitted=403,
            .total_flushed=390,.painter_culled=11,.painter_clipped=2,
        };
        xtreme_render_history_append(&ring,&sample);
    }
    assert(ring.count==64);
    assert(ring.next==66);
    assert(ring.samples[1].frame==66);
    assert(ring.samples[2].frame==3);
    assert(ring.samples[1].total_submitted==
           ring.samples[1].stage_submitted+
           ring.samples[1].marker_submitted+
           ring.samples[1].actor_submitted);
    assert(sizeof(ring)==16u+64u*15u*4u);
    puts("render profile ring ok");
    return 0;
}
