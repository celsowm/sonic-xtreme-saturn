#include "ring_frame_clock.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    assert(xtreme_ring_frame_index(0)==0);
    assert(xtreme_ring_frame_index(1)==0);
    assert(xtreme_ring_frame_index(2)==1);
    assert(xtreme_ring_frame_index(3)==1);
    assert(xtreme_ring_frame_index(30)==15);
    assert(xtreme_ring_frame_index(32)==0);
    assert(xtreme_ring_frame_index(64)==0);
    assert(xtreme_ring_frame_index(0xFFFFFFFFu)==15);
    puts("authored ring frame clock ok");
    return 0;
}
