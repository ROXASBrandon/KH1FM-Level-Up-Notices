#ifndef KH1_NOTICE_TIMING_H
#define KH1_NOTICE_TIMING_H
#include <stdint.h>
#include <string.h>
typedef struct { uint64_t last, elapsed; int holding; } NoticeClock;
/* Called after the native frame. A positive native timer proves that the
 * card actually advanced. Frozen/paused cards do not consume display time. */
static int notice_hold(NoticeClock *c, int vanilla, unsigned state,
                       int timer, uint64_t now) {
    if (!vanilla || state != 3) { memset(c,0,sizeof(*c)); return 0; }
    if (!c->holding) { c->holding=1; c->last=now; c->elapsed=0; }
    else {
        if (timer>0 && now>=c->last) c->elapsed+=now-c->last;
        c->last=now;
    }
    return c->elapsed<8000 ? 1 : 2;
}
#endif
