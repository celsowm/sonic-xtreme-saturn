#include <assert.h>
#include "debug_clock.h"
int main(void){
    xtreme_clock_t c={0};
    unsigned ticks=0;
    for(int i=0;i<1000;++i)ticks+=xtreme_clock_frame(&c,1,0,0,0);
    assert(ticks==60 && c.remainder==0);
    assert(xtreme_clock_frame(&c,15,0,0,0)==0);
    assert(xtreme_clock_frame(&c,90,1,0,0)==0 && c.paused);
    assert(xtreme_clock_frame(&c,500,0,0,0)==0);
    assert(xtreme_clock_frame(&c,500,0,1,0)==1);
    assert(xtreme_clock_frame(&c,500,0,1,1)==0);
    assert(xtreme_clock_frame(&c,500,1,1,0)==0 && !c.paused);
    assert(xtreme_clock_frame(&c,200,0,0,0)==6 && c.dropped_ms==100);
    assert(xtreme_clock_frame(&c,15,0,0,0)==0);
    assert(xtreme_clock_frame(&c,50,0,0,1)==0 && c.remainder==0);
    assert(xtreme_clock_frame(&c,17,0,0,0)==1);
    return 0;
}
