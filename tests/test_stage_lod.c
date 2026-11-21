#include "stage_lod.h"
#include <assert.h>
#include <stdio.h>
#define M(n) ((int32_t)((n)*65536))

int main(void) {
    assert(xtreme_stage_lod_choose_near(M(0),M(0),M(0),M(0)));
    assert(xtreme_stage_lod_choose_near(M(27),M(0),M(0),M(0)));
    assert(!xtreme_stage_lod_choose_near(M(28),M(0),M(0),M(0)));
    assert(xtreme_stage_lod_choose_near(M(-20),M(-25),M(0),M(0)));
    assert(!xtreme_stage_lod_choose_near(M(-20),M(-28),M(0),M(0)));
    /* No overflow in signed 32-bit inputs at large fixed-point distances. */
    assert(!xtreme_stage_lod_choose_near(M(-100),M(120),M(100),M(-120)));
    puts("whole-tree stage LOD ok");
    return 0;
}
