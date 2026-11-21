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
    int32_t lo_y, hi_y;
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

/* Conservative, camera-orientation-aware early rejection for faces ENTIRELY
 * behind the eye. LibSaturn's quad projector computes clip-space w for four
 * corners, then append() increments culled_faces if all w <= 0.
 * For a rectangular world AABB the maximum forward dot product occurs at
 * one support corner: pick upper/lower coordinate independently according to
 * the sign of the camera forward component.
 *
 * All numbers are Q16.16; their products are Q32.32 in signed int64.
 * Keep a full 1-metre safety band behind the eye, since projection-matrix
 * rounding and near-plane fallback differ near w == 0. Never discard a
 * partially-front face: the painter still handles clipping/visibility.
 * This rejects no geometry which can have positive clip-w when forward and
 * view matrix describe the same camera. It does NOT perform screen/FOV culling.
 */
static inline int xtreme_stage_aabb_may_be_in_front(
    const xtreme_stage_aabb_t* b,
    int32_t eye_x,int32_t eye_y,int32_t eye_z,
    int32_t forward_x,int32_t forward_y,int32_t forward_z) {
    if(!forward_x && !forward_y && !forward_z)return 1;
    const int64_t x=(int64_t)(forward_x>=0?b->hi_x:b->lo_x)-eye_x;
    const int64_t y=(int64_t)(forward_y>=0?b->hi_y:b->lo_y)-eye_y;
    const int64_t z=(int64_t)(forward_z>=0?b->hi_z:b->lo_z)-eye_z;
    const int64_t max_depth=x*forward_x+y*forward_y+z*forward_z;
    return max_depth> -((int64_t)65536*65536);
}


/* Plane-budgeted conservative frustum gate for authored static face groups.
 * Uses the identical ROW-MAJOR view-projection matrix that LibSaturn uses
 * for sat_project_vertices(). For an OpenGL clip-space point, visible implies
 *  -w <= x <= w, -w <= y <= w. A quad lies entirely outside a side
 * if even the most favourable AABB support corner has a NEGATIVE (w +/- x/y).
 *
 * All coefficients/positions are signed Q16.16. Accumulate their products
 * in int64_t (Q32.32). The -2-world-unit homogeneous margin intentionally
 * retains geometry near boundaries and differences from fixed-point rounding.
 * Do NOT use the box center: terrain quads span long camera seams.
 * No depth/far-plane clipping here, so near terrain and near-clip fallbacks
 * are unchanged. Caller must bypass the gate in panorama/debug viewer mode.
 */
typedef struct xtreme_stage_frustum {
    int32_t planes[4][4]; /* left, right, bottom, top; x,y,z,constant */
    uint8_t valid;
} xtreme_stage_frustum_t;

/* Eight consecutive authored faces share one conservative world bounds.
 * Grouping keeps clip-plane tests O(face_count/8) instead of paying 4x3
 * signed 64-bit multiplies for every near-camera face on the SH-2.
 * A mixed/large group is kept, never reduced: only wholly off-screen groups
 * can be rejected. No run-time allocation, terrain or collider changes. */
#define XTREME_STAGE_FRUSTUM_GROUP_SIZE 8u
static inline void xtreme_stage_aabb_merge(
    xtreme_stage_aabb_t* dst,const xtreme_stage_aabb_t* src) {
    if(src->lo_x<dst->lo_x)dst->lo_x=src->lo_x;
    if(src->hi_x>dst->hi_x)dst->hi_x=src->hi_x;
    if(src->lo_y<dst->lo_y)dst->lo_y=src->lo_y;
    if(src->hi_y>dst->hi_y)dst->hi_y=src->hi_y;
    if(src->lo_z<dst->lo_z)dst->lo_z=src->lo_z;
    if(src->hi_z>dst->hi_z)dst->hi_z=src->hi_z;
}

static inline void xtreme_stage_frustum_prepare(
    xtreme_stage_frustum_t* out,const int32_t* view_proj) {
    if(!out)return;
    out->valid=0u;
    if(!view_proj)return;
    for(unsigned plane=0;plane<4u;++plane) {
        const unsigned axis=plane<2u?0u:1u;
        const int sign=(plane&1u)?-1:1;
        for(unsigned i=0;i<4u;++i) {
            const int64_t coefficient=
                (int64_t)view_proj[12u+i]+sign*(int64_t)view_proj[axis*4u+i];
            if(coefficient>INT32_MAX || coefficient<INT32_MIN)return;
            out->planes[plane][i]=(int32_t)coefficient;
        }
    }
    out->valid=1u;
}

static inline int xtreme_stage_aabb_frustum_relevant(
    const xtreme_stage_aabb_t* b,const xtreme_stage_frustum_t* frustum) {
    if(!frustum || !frustum->valid)return 1;
    /* Margin is larger than per-product Q16 rounding error. The extra
     * world unit also protects near-FOV edge texture/polygon coverage. */
    const int64_t margin=2LL*65536*65536;
    for(unsigned plane=0;plane<4u;++plane) {
        const int32_t* p=frustum->planes[plane];
        const int64_t max_plane=
            (int64_t)p[0]*(p[0]>=0?b->hi_x:b->lo_x)+
            (int64_t)p[1]*(p[1]>=0?b->hi_y:b->lo_y)+
            (int64_t)p[2]*(p[2]>=0?b->hi_z:b->lo_z)+
            (int64_t)p[3]*65536;
        if(max_plane< -margin)return 0;
    }
    return 1;
}

#endif
