#include <assert.h>
#include "controller.h"

static int flat(void* unused,const sat_vec3_t* o,sat_fx16_t length,sat_vec3_t* p,sat_vec3_t* n) {
    (void)unused;
    if (o->y < 0 || o->y > length || o->z < -SAT_FX16(30)) return 0;
    *p=(sat_vec3_t){o->x,0,o->z};
    *n=(sat_vec3_t){0,SAT_FX16_ONE,0};
    return 1;
}
int main(void) {
    xtreme_player_t p;
    const sat_vec3_t start={0,SAT_FX16(1),0};
    xtreme_reset(&p,&start);
    for(int i=0;i<60;++i) xtreme_tick(&p,(xtreme_input_t){0,0,0},flat,0);
    assert(p.grounded && p.feet.y==0);
    for(int i=0;i<20;++i) xtreme_tick(&p,(xtreme_input_t){0,-127,0},flat,0);
    assert(p.velocity.z<0 && p.feet.z<0 && p.grounded);
    sat_fx16_t v=p.velocity.z;
    xtreme_tick(&p,(xtreme_input_t){0,0,1},flat,0);
    assert(!p.grounded && p.feet.y>0 && p.velocity.z==v+SAT_FX16(.010));
    for(int i=0;i<70;++i) xtreme_tick(&p,(xtreme_input_t){0,0,0},flat,0);
    assert(p.grounded && p.feet.y==0);
    xtreme_reset(&p,&start);
    for(int i=0;i<200;++i) xtreme_tick(&p,(xtreme_input_t){0,-127,0},flat,0);
    /* Eventually leaves the platform, falls and respawns. */
    assert(p.feet.y >= -SAT_FX16(30));
    return 0;
}
