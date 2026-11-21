#include "stage_visibility.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#define M(n) ((int32_t)((n)*65536))
#define BOX(xlo,xhi,zlo,zhi) { .lo_x=M(xlo),.hi_x=M(xhi), .lo_z=M(zlo),.hi_z=M(zhi), .lo_y=M(-2),.hi_y=M(2) }

int main(void) {
    xtreme_stage_aabb_t underfoot=BOX(-5,5,-4,4);
    assert(xtreme_stage_aabb_visible(&underfoot,0,M(7)));
    /* Top of the authored start valley at z=12 is 5m behind eye z=7. */
    xtreme_stage_aabb_t opening=BOX(-45,45,11,12);
    assert(xtreme_stage_aabb_visible(&opening,0,M(7)));
    xtreme_stage_aabb_t far=BOX(-10,10,-120,-110);
    assert(!xtreme_stage_aabb_visible(&far,0,M(7)));
    xtreme_stage_aabb_t behind=BOX(-8,8,25,40);
    assert(!xtreme_stage_aabb_visible(&behind,0,M(7)));
    xtreme_stage_aabb_t offside=BOX(60,80,-10,-5);
    assert(!xtreme_stage_aabb_visible(&offside,0,M(7)));
    xtreme_stage_aabb_t edge=BOX(15,70,-14,-12);
    assert(xtreme_stage_aabb_visible(&edge,0,M(7)));
    xtreme_stage_aabb_t offroad=BOX(25,33,-7,1);
    assert(xtreme_stage_aabb_visible(&offroad,M(28),M(7)));
    /* Huge face must not disappear just because its center is remote. */
    xtreme_stage_aabb_t wide=BOX(-48,48,-23,-12);
    assert(xtreme_stage_aabb_visible(&wide,0,M(7)));
    /* The support-corner test must never cut a partly visible polygon. */
    assert(xtreme_stage_aabb_may_be_in_front(
        &far,0,0,M(7),0,0,M(-1)));
    assert(!xtreme_stage_aabb_may_be_in_front(
        &behind,0,0,M(7),0,0,M(-1)));
    assert(xtreme_stage_aabb_may_be_in_front(
        &opening,0,0,M(7),0,0,M(-1)));
    xtreme_stage_aabb_t straddles=BOX(-5,5,-1,1);
    assert(xtreme_stage_aabb_may_be_in_front(
        &straddles,0,0,0,0,0,M(-1)));
    /* Sideways view: use full X extrema, not center or guessed -Z. */
    xtreme_stage_aabb_t side=BOX(22,29,-5,5);
    assert(xtreme_stage_aabb_may_be_in_front(
        &side,0,0,0,M(1),0,0));
    assert(!xtreme_stage_aabb_may_be_in_front(
        &side,0,0,0,M(-1),0,0));
    /* Upward view must use the Y extrema too. */
    xtreme_stage_aabb_t upper=BOX(-2,2,-2,2);
    upper.lo_y=M(8);upper.hi_y=M(12);
    assert(xtreme_stage_aabb_may_be_in_front(
        &upper,0,0,0,0,M(1),0));
    assert(!xtreme_stage_aabb_may_be_in_front(
        &upper,0,0,0,0,M(-1),0));
    assert(xtreme_stage_aabb_may_be_in_front(
        &behind,0,0,0,0,0,0));
    /* One-metre safety threshold: anything near the eye is retained. */
    xtreme_stage_aabb_t close=BOX(-1,1,0,1);
    assert(xtreme_stage_aabb_may_be_in_front(
        &close,0,0,0,0,0,M(-1)));
    puts("stage visibility gate ok");
    return 0;
}
