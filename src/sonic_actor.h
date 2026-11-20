#ifndef XTREME_SONIC_ACTOR_H
#define XTREME_SONIC_ACTOR_H
#include <saturn/scene.h>
#include "controller.h"

/* Optional, locally built character presentation. Only compiled when the
 * private generated sonic.c/sonic.h are present. No proprietary files live
 * in Git and the greybox build remains independent of this module. */
sat_result_t xtreme_sonic_init(void);
sat_result_t xtreme_sonic_tick(const xtreme_player_t* player);
sat_result_t xtreme_sonic_submit(sat_scene_t* scene, const xtreme_player_t* player);
#endif
