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
        &underfoot,0,0,M(7),0,0,M(-1)));
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
    /* Canonical row-major fixed-point camera, facing -Z, with a 90-degree
     * clip-space cone: x and y in [-w,+w], w=-z. The production camera
     * uses a tighter FOV, but the plane/AABB proof is the same. */
    const int32_t camera_forward[16]={
        M(1),0,0,0,
        0,M(1),0,0,
        0,0,M(1),0,
        0,0,-M(1),0
    };
    xtreme_stage_frustum_t frustum={0};
    xtreme_stage_frustum_prepare(&frustum,camera_forward);
    assert(frustum.valid);
    xtreme_stage_aabb_t in_front=BOX(-3,3,-14,-8);
    assert(xtreme_stage_aabb_frustum_relevant(&in_front,&frustum));

    /* Entirely outside the field of view (by >2m safety distance). */
    xtreme_stage_aabb_t right_of_screen=BOX(18,25,-12,-10);
    xtreme_stage_aabb_t left_of_screen=BOX(-25,-18,-12,-10);
    assert(!xtreme_stage_aabb_frustum_relevant(&right_of_screen,&frustum));
    assert(!xtreme_stage_aabb_frustum_relevant(&left_of_screen,&frustum));
    xtreme_stage_aabb_t high=BOX(-3,3,-8,-6);
    high.lo_y=M(12);high.hi_y=M(20);
    xtreme_stage_aabb_t low=BOX(-3,3,-8,-6);
    low.lo_y=M(-20);low.hi_y=M(-12);
    assert(!xtreme_stage_aabb_frustum_relevant(&high,&frustum));
    assert(!xtreme_stage_aabb_frustum_relevant(&low,&frustum));
    /* Retain huge floor pieces crossing the edge and all near-camera art. */
    xtreme_stage_aabb_t wide_cross=BOX(-3,35,-11,-9);
    assert(xtreme_stage_aabb_frustum_relevant(&wide_cross,&frustum));
    xtreme_stage_aabb_t on_edge=BOX(10,11,-10,-9);
    assert(xtreme_stage_aabb_frustum_relevant(&on_edge,&frustum));
    assert(xtreme_stage_aabb_frustum_relevant(&straddles,&frustum));

    /* A whole authored block is rejected only when every constituent
     * quad is off-screen. If ONE quad crosses the FOV, the enlarged AABB
     * must keep the entire group; no contiguous terrain holes. */
    xtreme_stage_aabb_t group=right_of_screen;
    assert(!xtreme_stage_aabb_frustum_relevant(&group,&frustum));
    xtreme_stage_aabb_merge(&group,&in_front);
    assert(group.lo_x<=in_front.lo_x && group.hi_x>=right_of_screen.hi_x);
    assert(group.lo_z<=in_front.lo_z && group.hi_z>=right_of_screen.hi_z);
    assert(xtreme_stage_aabb_frustum_relevant(&group,&frustum));
    /* Camera in the middle of a large strip: no center-only rejection. */
    xtreme_stage_aabb_t panorama=BOX(-80,80,-13,-8);
    xtreme_stage_aabb_merge(&group,&panorama);
    assert(xtreme_stage_aabb_frustum_relevant(&group,&frustum));
    assert(XTREME_STAGE_FRUSTUM_GROUP_SIZE==8u);

    /* Camera turned 90 degrees: optical axis +X, screen right = -Z.
     * Culling must adapt instead of reusing spawn's fixed negative-Z view. */
    const int32_t yawed[16]={
        0,0,-M(1),0,
        0,M(1),0,0,
        0,0,M(1),0,
        M(1),0,0,0
    };
    xtreme_stage_frustum_prepare(&frustum,yawed);
    assert(xtreme_stage_aabb_frustum_relevant(&right_of_screen,&frustum));
    xtreme_stage_aabb_t yawed_offside=BOX(8,10,-33,-30);
    assert(!xtreme_stage_aabb_frustum_relevant(&yawed_offside,&frustum));
    assert(xtreme_stage_aabb_frustum_relevant(&wide_cross,&frustum));

    /* Overflow/invalid matrix disables the optimization, not the scenery. */
    int32_t broken[16]={0};
    broken[12]=INT32_MAX;broken[0]=INT32_MAX;
    xtreme_stage_frustum_prepare(&frustum,broken);
    assert(!frustum.valid);
    assert(xtreme_stage_aabb_frustum_relevant(&right_of_screen,&frustum));
    xtreme_stage_frustum_prepare(&frustum,0);
    assert(!frustum.valid);

    /* Deterministic random AABBs: any box with a corner inside all
     * canonical clip half-spaces MUST survive the conservative gate.
     * This detects sign errors and aggressive center-only culling. */
    xtreme_stage_frustum_prepare(&frustum,camera_forward);
    uint32_t seed=0x23A11E53u;
    for(unsigned n=0;n<12000u;++n) {
        int32_t coords[3],half[3];
        for(unsigned k=0;k<3u;++k) {
            seed=seed*1664525u+1013904223u;
            coords[k]=M((int32_t)(seed%127u)-63);
            seed=seed*1664525u+1013904223u;
            half[k]=M((int32_t)(seed%15u));
        }
        xtreme_stage_aabb_t aabb={
            .lo_x=coords[0]-half[0],.hi_x=coords[0]+half[0],
            .lo_y=coords[1]-half[1],.hi_y=coords[1]+half[1],
            .lo_z=coords[2]-half[2],.hi_z=coords[2]+half[2]
        };
        int any_inside=0;
        for(unsigned mask=0;mask<8u;++mask) {
            const int32_t x=mask&1u?aabb.hi_x:aabb.lo_x;
            const int32_t y=mask&2u?aabb.hi_y:aabb.lo_y;
            const int32_t z=mask&4u?aabb.hi_z:aabb.lo_z;
            if(z<0 && x>=z && x<=-z && y>=z && y<=-z)
                any_inside=1;
        }
        if(any_inside)
            assert(xtreme_stage_aabb_frustum_relevant(&aabb,&frustum));
    }
    puts("stage visibility gate ok");
    return 0;
}
