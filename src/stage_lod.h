#ifndef XTREME_STAGE_LOD_H
#define XTREME_STAGE_LOD_H
#include <stdint.h>

/* One near/far decision PER TREE, not per polygon.
 * Max-axis XZ metric is intentional: avoids a target-side 64-bit square/sqrt
 * and preserves coherent canopy+bark selection for each named LOD group.
 * Distances are Q16.16 metres.
 */
static inline uint8_t xtreme_stage_lod_choose_near(
    int32_t center_x, int32_t center_z,
    int32_t actor_x, int32_t actor_z) {
    int64_t dx=(int64_t)center_x-actor_x;
    int64_t dz=(int64_t)center_z-actor_z;
    if(dx<0)dx=-dx;
    if(dz<0)dz=-dz;
    const int64_t threshold=(int64_t)(27*65536);
    return (uint8_t)(dx<=threshold && dz<=threshold);
}
#endif
