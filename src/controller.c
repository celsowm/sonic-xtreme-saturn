#include "controller.h"

#define F(n) SAT_FX16(n)
static sat_fx16_t absolute(sat_fx16_t n) { return n < 0 ? -n : n; }
static sat_fx16_t approach(sat_fx16_t v, sat_fx16_t target, sat_fx16_t delta) {
    if (v < target) return target-v < delta ? target : v+delta;
    if (v > target) return v-target < delta ? target : v-delta;
    return v;
}
static sat_fx16_t mul(sat_fx16_t a,sat_fx16_t b) {
    return (sat_fx16_t)(((int64_t)a*b)/65536);
}
void xtreme_reset(xtreme_player_t* p, const sat_vec3_t* spawn) {
    const sat_vec3_t saved = *spawn;
    p->spawn = p->feet = saved;
    p->velocity = (sat_vec3_t){0,0,0};
    p->ground_normal = (sat_vec3_t){0,F(1),0};
    p->grounded = 0;
}
void xtreme_tick(xtreme_player_t* p, xtreme_input_t in, xtreme_ground_fn query, void* ctx) {
    int32_t x = SAT_CLAMP((int32_t)in.x,-127,127);
    int32_t z = SAT_CLAMP((int32_t)in.z,-127,127);
    /* Approximate circular input clamp without a square root. */
    int32_t ax = x < 0 ? -x : x, az = z < 0 ? -z : z;
    int32_t m = SAT_MAX(ax,az) + SAT_MIN(ax,az)*3/8;
    if (m > 127) { x=x*127/m; z=z*127/m; }
    const sat_fx16_t accel = p->grounded ? F(.024) : F(.009);
    if (x || z) {
        p->velocity.x = approach(p->velocity.x, F(.48)*x/127, accel);
        p->velocity.z = approach(p->velocity.z, F(.48)*z/127, accel);
    } else if (p->grounded) {
        p->velocity.x = approach(p->velocity.x,0,F(.010));
        p->velocity.z = approach(p->velocity.z,0,F(.010));
    }
    if (p->grounded) {
        /* Static friction: shallow slopes must not generate motion from rest. */
        const int stopped = !x && !z && absolute(p->velocity.x)<F(.018) &&
                            absolute(p->velocity.z)<F(.018) && p->ground_normal.y>=F(.85);
        if (stopped) {
            p->velocity.x=0;p->velocity.z=0;
        } else {
        /* Positive horizontal components of the upward normal point downhill. */
        p->velocity.x += mul(p->ground_normal.x,F(.016));
        p->velocity.z += mul(p->ground_normal.z,F(.016));
        }
        p->velocity.y = 0;
    }
    p->velocity.x = SAT_CLAMP(p->velocity.x,-F(.75),F(.75));
    p->velocity.z = SAT_CLAMP(p->velocity.z,-F(.75),F(.75));
    sat_fx16_t hi = SAT_MAX(absolute(p->velocity.x),absolute(p->velocity.z));
    sat_fx16_t lo = SAT_MIN(absolute(p->velocity.x),absolute(p->velocity.z));
    sat_fx16_t speed = hi + lo*3/8;
    if (speed > F(.75)) {
        p->velocity.x = (sat_fx16_t)((int64_t)p->velocity.x*F(.75)/speed);
        p->velocity.z = (sat_fx16_t)((int64_t)p->velocity.z*F(.75)/speed);
    }
    if (p->grounded && in.jump) {
        p->grounded=0;
        p->velocity.y=F(.24);
    }
    if (!p->grounded) {
        p->velocity.y -= F(.012);
        if (p->velocity.y < -F(.85)) p->velocity.y=-F(.85);
    }
    const sat_vec3_t before=p->feet;
    sat_vec3_t next={before.x+p->velocity.x,before.y+p->velocity.y,before.z+p->velocity.z};
    if (p->velocity.y <= 0) {
        const sat_fx16_t step=p->grounded ? F(.65) : F(.03);
        const sat_fx16_t drop=p->grounded ? F(.85) : -p->velocity.y+F(.03);
        const sat_vec3_t origin={next.x,before.y+step,next.z};
        sat_vec3_t hit,normal;
        if (query && query(ctx,&origin,step+drop,&hit,&normal) &&
            normal.y >= F(.5) && hit.y <= origin.y &&
            hit.y >= before.y-drop && (p->grounded || next.y <= hit.y)) {
            next.y=hit.y;
            p->velocity.y=0;
            p->ground_normal=normal;
            p->grounded=1;
        } else {
            if(p->grounded) next.y=before.y-F(.012);
            p->grounded=0;
        }
    }
    p->feet=next;
    if (p->feet.y < -F(30) || absolute(p->feet.x)>F(220) || absolute(p->feet.z)>F(220))
        xtreme_reset(p,&p->spawn);
}
