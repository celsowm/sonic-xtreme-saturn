#include <assert.h>
#include "controller.h"

static int flat(void* unused,const sat_vec3_t* o,sat_fx16_t length,sat_vec3_t* p,sat_vec3_t* n) {
    (void)unused;
    if (o->y < 0 || o->y > length || o->z < -SAT_FX16(60)) return 0;
    *p=(sat_vec3_t){o->x,0,o->z};
    *n=(sat_vec3_t){0,SAT_FX16_ONE,0};
    return 1;
}
static int slope(void* unused,const sat_vec3_t* o,sat_fx16_t length,sat_vec3_t* p,sat_vec3_t* n){
    (void)unused;
    sat_fx16_t y=o->z/4;
    if(o->y<y||o->y-y>length)return 0;
    *p=(sat_vec3_t){o->x,y,o->z};
    *n=(sat_vec3_t){0,SAT_FX16(.97),-SAT_FX16(.24)};
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
    for(int i=0;i<120;++i)xtreme_tick(&p,(xtreme_input_t){0,0,0},slope,0);
    assert(p.grounded&&p.feet.z==0&&p.velocity.z==0);
    for(int i=0;i<20;++i)xtreme_tick(&p,(xtreme_input_t){0,-127,0},slope,0);
    assert(p.grounded&&p.feet.z<0&&p.velocity.z<0);
    xtreme_reset(&p,&start);
    int left=0, respawned=0;
    for(int i=0;i<300;++i) {
        xtreme_tick(&p,(xtreme_input_t){0,-127,0},flat,0);
        if (p.feet.z < -SAT_FX16(60)) left=1;
        if (left && p.feet.z==0 && p.feet.y==start.y) { respawned=1; break; }
    }
    assert(left && respawned);
    return 0;
}
