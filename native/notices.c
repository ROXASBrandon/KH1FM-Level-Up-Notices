#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "timing.h"
typedef uint64_t (__cdecl *FrameProc)(void *);
static uintptr_t game;
static FrameProc original_frame;
static NoticeClock clocks[3][5];
static volatile LONG64 lease;
static int enabled, failed;
__declspec(dllexport) volatile uint32_t notices_status;
__declspec(dllexport) volatile uint32_t notices_extended;
static int readable(uintptr_t p,size_t n) {
    MEMORY_BASIC_INFORMATION m;
    return p && p+n>=p && VirtualQuery((void *)p,&m,sizeof(m)) &&
        m.State==MEM_COMMIT && !(m.Protect&(PAGE_GUARD|PAGE_NOACCESS)) &&
        p+n<=(uintptr_t)m.BaseAddress+m.RegionSize;
}
static int match(uintptr_t rva,const unsigned char *bytes,size_t n) {
    return readable(game+rva,n) && !memcmp((void *)(game+rva),bytes,n);
}
static int supported(void) {
    return game && match(0x4698D2,(const unsigned char[]){106},1) &&
        match(0x3EA388,(const unsigned char[]){0x58,0x20,0x3A,0x20},4) &&
        match(0x26E20C,(const unsigned char[]){9},1) &&
        match(0x27304E,(const unsigned char[]){0xFF,0x43,0xFC,0x83,0x7B,0xFC,0x5A,0x7E,0x34},9) &&
        match(0x272623,(const unsigned char[]){0xC7,0x03,1,0,0,0,0x44,0x89,0x4B,0x0C},10) &&
        readable(game+0x283B390,3*0x3A20);
}
static uint64_t __cdecl on_frame(void *context) {
    uint64_t result=original_frame(context), now=GetTickCount64();
    int active=now-(uint64_t)InterlockedCompareExchange64(&lease,0,0)<2000;
    for (unsigned slot=0;slot<3;++slot) {
        unsigned count=*(uint32_t *)(game+0x283B380+slot*4);
        for (unsigned q=0;q<5;++q) {
            uintptr_t b=game+0x283B390+slot*0x3A20+q*0xBA0;
            unsigned state=*(uint32_t *)b;
            int32_t *timer=(int32_t *)(b+0xC);
            uintptr_t color=*(uintptr_t *)(b+0xB88);
            int vanilla=active && count<=5 && q<count &&
                color>=game+0x527A10 && color<=game+0x527A40 &&
                !((color-(game+0x527A10))%0x10);
            int was=clocks[slot][q].holding;
            int action=notice_hold(&clocks[slot][q],vanilla,state,*timer,now);
            if (action) {
                if (!was) ++notices_extended;
                *timer=action==1 ? 0 : 90;
            }
        }
    }
    return result;
}
__declspec(dllexport) int __cdecl kh1_notices_bootstrap(void *lua_state) {
    (void)lua_state;
    InterlockedExchange64(&lease,(LONG64)GetTickCount64());
    if (enabled || failed) return 0;
    game=(uintptr_t)GetModuleHandleW(L"KINGDOM HEARTS FINAL MIX.exe");
    if (!supported()) {
        failed=1; notices_status=2;
        puts("[Level Up Notices] Unsupported executable/timer; disabled."); return 0;
    }
    uintptr_t app=*(uintptr_t *)(game+0x21AAF18);
    if (!readable(app,8) || !readable(*(uintptr_t *)app,40)) return 0;
    FrameProc *slot=(FrameProc *)(*(uintptr_t *)app+32), prior=*slot;
    MEMORY_BASIC_INFORMATION m;
    if (!prior || prior==on_frame || !VirtualQuery((void *)(uintptr_t)prior,&m,sizeof(m)) ||
        !(m.Protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY))) return 0;
    HMODULE pinned;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
        (LPCWSTR)(uintptr_t)on_frame,&pinned)) return 0;
    DWORD old,unused;
    if (!VirtualProtect(slot,8,PAGE_READWRITE,&old)) return 0;
    original_frame=prior;
    FrameProc observed=(FrameProc)InterlockedCompareExchangePointer((PVOID volatile *)slot,
        (PVOID)(uintptr_t)on_frame,(PVOID)(uintptr_t)prior);
    VirtualProtect(slot,8,old,&unused);
    if (observed!=prior) return 0;
    enabled=1; notices_status=1;
    puts("[Level Up Notices] Ready: native cards hold for 8 seconds."); fflush(stdout);
    return 0;
}
