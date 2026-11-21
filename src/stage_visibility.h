#ifndef XTREME_STAGE_VISIBILITY_H
#define XTREME_STAGE_VISIBILITY_H

#include <stdint.h>

/* Cheap X/Z half-space gate for the authored Adventure mesh. Units are Q16.16
 * metres in the SDK's Y-up coordinate system, with camera looking mostly
 * toward -Z. This deliberately OVERestimates the 320x224 horizontal FOV to
 * keep adjacent terrain patches present during camera movement.
 *
 * It is not a general frustum culler or a substitute for correct near clip.
 * Called only for render geometry; collision mesh is never filtered.
 */
typedef struct {
    int32_t lo_x, hi_x, lo_z, hi_z;
} xtreme_stage_aabb_t;

static inline int xtreme_stage_aabb_visible(const xtreme_stage_aabb_t *b,
                                             int32_t eye_x, int32_t eye_z) {
    const int64_t far_forward=(int64_t)eye_z-b->lo_z;
    const int64_t near_forward=(int64_t)eye_z-b->hi_z;

    /* The first visible valley patch extends behind the camera at spawn.
     * The back margin is wide enough to keep those polygons fully covered.
     * The far limit intentionally excludes high-cost unseen future sectors;
     * still pending real Ymir screenshots / terrain pop tests.
     */
    if(far_forward < -(int64_t)(8*65536) ||
       near_forward > (int64_t)(64*65536))
        return 0;

    /* Wide angle: radius = 12m + 0.75*far depth, with no trig or division
     * and generous slack for sideways actor velocity / camera smoothing.
     * Compare the FULL face bounds rather than center, including long
     * landscape strips that overlap the view boundary.
     */
    const int64_t positive_far=far_forward>0?far_forward:0;
    const int64_t radius=(int64_t)(12*65536)+(positive_far*3)/4;
    if((int64_t)b->hi_x<(int64_t)eye_x-radius ||
       (int64_t)b->lo_x>(int64_t)eye_x+radius)
        return 0;
    return 1;
}

#endif
