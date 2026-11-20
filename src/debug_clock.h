#ifndef XTREME_DEBUG_CLOCK_H
#define XTREME_DEBUG_CLOCK_H
#include <stdint.h>
/* Independent of rendering and pad hardware. Time units = ms * 60.
 * Pausing/resuming discards backlog, not player state or tick count.
 * Each step request while paused yields exactly one tick. */
typedef struct {
    uint32_t remainder,dropped_ms;
    uint8_t paused;
} xtreme_clock_t;
static inline void xtreme_clock_clear(xtreme_clock_t* c){c->remainder=0;}
static inline unsigned xtreme_clock_frame(xtreme_clock_t* c,uint32_t elapsed,
                                         int toggle,int step,int suspended){
    if(toggle){c->paused^=1u;c->remainder=0;elapsed=0;}
    if(suspended){c->remainder=0;return 0;}
    if(c->paused){c->remainder=0;return step&&!toggle?1u:0u;}
    if(elapsed>100u){c->dropped_ms+=elapsed-100u;elapsed=100u;}
    c->remainder+=elapsed*60u;
    unsigned ticks=c->remainder/1000u;
    c->remainder%=1000u;
    return ticks;
}
#endif
