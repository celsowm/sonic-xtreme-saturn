#ifndef XTREME_SONIC_ACTOR_H
#define XTREME_SONIC_ACTOR_H
#include <saturn/scene.h>
#include "controller.h"

/* Optional animated Sonic presentation built from versioned
 * assets/sonic-r/lod-160/{sonic.c,sonic.h}. The legacy blue-proxy stage
 * remains buildable when the optional character source is absent.
 * See assets/sonic-r/ATTRIBUTION.md for third-party rights. */
sat_result_t xtreme_sonic_init(void);
sat_result_t xtreme_sonic_tick(const xtreme_player_t* player);
/* Publish only the complete character state once per completed video frame. */
void xtreme_sonic_publish_debug(void);
sat_result_t xtreme_sonic_submit(sat_scene_t* scene, const xtreme_player_t* player);
#endif
