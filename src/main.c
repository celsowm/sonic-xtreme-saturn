/* SDK smoke test, not gameplay. Original geometric marker only. */
#include <saturn/app.h>
#include <saturn/color.h>
#include <saturn/vdp1.h>

int main(void) {
    if (sat_app_init_default() != SAT_OK) return 1;
    for (;;) {
        sat_pad_state_t pad = {0};
        if (sat_app_frame_begin(SAT_COLOR_BLUE, SAT_COLOR_BLACK, &pad) != SAT_OK)
            return 1;
        if (sat_draw_rect_screen(140, 92, 40, 40, SAT_COLOR_RED) != SAT_OK)
            return 1;
        if (sat_app_frame_end() != SAT_OK) return 1;
        if (pad.pressed & SAT_PAD_START) break;
    }
    return 0;
}
