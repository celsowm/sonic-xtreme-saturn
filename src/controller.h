#ifndef XTREME_CONTROLLER_H
#define XTREME_CONTROLLER_H
#include <saturn/math3d.h>
#include <stdint.h>

/* World metres, RH Y-up, velocity metres per 1/60 s tick.
 * Ground query supplies the highest supporting surface below origin.
 * The physics core knows nothing about input hardware or rendering. */
typedef struct xtreme_player {
    sat_vec3_t feet, velocity, ground_normal, spawn;
    uint8_t grounded;
} xtreme_player_t;
typedef struct xtreme_input {
    int16_t x, z; /* -127..127, world axes */
    uint8_t jump;
} xtreme_input_t;
typedef int (*xtreme_ground_fn)(void*, const sat_vec3_t*, sat_fx16_t,
                                sat_vec3_t*, sat_vec3_t*);
void xtreme_reset(xtreme_player_t*, const sat_vec3_t*);
void xtreme_tick(xtreme_player_t*, xtreme_input_t, xtreme_ground_fn, void*);
#endif
