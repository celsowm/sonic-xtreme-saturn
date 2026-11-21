#include "stage_visibility.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#define M(n) ((int32_t)((n)*65536))

int main(void) {
    xtreme_stage_aabb_t underfoot={M(-5),M(5),M(-4),M(4)};
    assert(xtreme_stage_aabb_visible(&underfoot,0,M(7)));
    /* Top of the authored start valley at z=12 is 5m behind eye z=7. */
    xtreme_stage_aabb_t opening={M(-45),M(45),M(11),M(12)};
    assert(xtreme_stage_aabb_visible(&opening,0,M(7)));
    xtreme_stage_aabb_t far={M(-10),M(10),M(-120),M(-110)};
    assert(!xtreme_stage_aabb_visible(&far,0,M(7)));
    xtreme_stage_aabb_t behind={M(-8),M(8),M(25),M(40)};
    assert(!xtreme_stage_aabb_visible(&behind,0,M(7)));
    xtreme_stage_aabb_t offside={M(60),M(80),M(-10),M(-5)};
    assert(!xtreme_stage_aabb_visible(&offside,0,M(7)));
    xtreme_stage_aabb_t edge={M(15),M(70),M(-14),M(-12)};
    assert(xtreme_stage_aabb_visible(&edge,0,M(7)));
    xtreme_stage_aabb_t offroad={M(25),M(33),M(-7),M(1)};
    assert(xtreme_stage_aabb_visible(&offroad,M(28),M(7)));
    /* Huge face must not disappear just because its center is remote. */
    xtreme_stage_aabb_t wide={M(-48),M(48),M(-23),M(-12)};
    assert(xtreme_stage_aabb_visible(&wide,0,M(7)));
    puts("stage visibility gate ok");
    return 0;
}
