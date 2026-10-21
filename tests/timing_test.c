#include <assert.h>
#include <stdio.h>
#include "timing.h"
int main(void) {
    const unsigned rates[]={30,60,120};
    for (unsigned r=0;r<3;++r) {
        NoticeClock c={0}; unsigned hz=rates[r];
        assert(notice_hold(&c,1,1,0,0)==0);
        assert(notice_hold(&c,1,3,1,1000)==1);
        for (unsigned f=1;f<hz*8;++f)
            assert(notice_hold(&c,1,3,1,1000+(uint64_t)f*1000/hz)==1);
        assert(notice_hold(&c,1,3,1,9000)==2);
        assert(notice_hold(&c,1,4,90,9016)==0);
        assert(notice_hold(&c,1,3,1,9032)==1); /* reused slot */
        assert(notice_hold(&c,0,3,1,9048)==0); /* custom EXP card */
    }
    NoticeClock c={0};
    notice_hold(&c,1,3,1,1000);
    assert(notice_hold(&c,1,3,0,61000)==1 && c.elapsed==0); /* paused */
    assert(notice_hold(&c,1,3,1,61016)==1 && c.elapsed==16);
    assert(notice_hold(&c,1,0,0,61032)==0 && !c.holding); /* cleared */
    puts("PASS: 8-second timing at 30/60/120 Hz, pause, slot reuse, custom cards, clear.");
}
