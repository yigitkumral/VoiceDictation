#include "Gesture.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    VDGesture g = {0};
    VDPoint p[] = {{1,.2,.5},{2,.4,.5},{3,.6,.5},{4,.8,.5},{5,.9,.5}};
    assert(!VDFeed(&g, 1, p, 4, false));
    assert(VDFeed(&g, 1.1, p, 0, false));
    assert(!VDFeed(&g, 1.12, p, 0, false)); // release tekrar etmez
    VDFeed(&g, 2, p, 3, false); assert(!VDFeed(&g, 2.1, p, 0, false)); // uc parmak gunluk hareket
    VDFeed(&g, 3, p, 5, false); assert(!VDFeed(&g, 3.1, p, 0, false));
    VDFeed(&g, 4, p, 4, false); p[0].x=.3;
    VDFeed(&g, 4.1, p, 4, false); assert(!VDFeed(&g, 4.15, p, 0, false)); p[0].x=.2;
    VDFeed(&g, 5, p, 4, false); VDFeed(&g, 5.1, p, 4, true);
    assert(!VDFeed(&g, 5.15, p, 0, false)); // modifier/tiklama iptali
    VDFeed(&g, 6, p, 4, false); assert(!VDFeed(&g, 6.8, p, 0, false)); // uzun basma/bosluk
    VDFeed(&g, 7, p, 1, false); VDFeed(&g, 7.04, p, 2, false); VDFeed(&g, 7.06, p, 3, false);
    VDFeed(&g, 7.08, p, 4, false); assert(VDFeed(&g, 7.15, p, 0, false));
    VDFeed(&g, 8, p, 4, false); p[0].id=6;
    VDFeed(&g, 8.1, p, 4, false); assert(!VDFeed(&g, 8.15, p, 0, false)); p[0].id=1;
    VDFeed(&g, 9, p, 4, false); p[0].x=NAN;
    VDFeed(&g, 9.1, p, 4, false); assert(!VDFeed(&g, 9.15, p, 0, false)); p[0].x=.2;
    VDFeed(&g, 10, p, 4, false); assert(!VDFeed(&g, 9.9, p, 0, false));
    VDFeed(&g, 11, p, 1, false); VDFeed(&g, 11.15, p, 4, false);
    assert(VDFeed(&g, 11.45, p, 0, false)); // dogal parmak yerlesimi + basma
    VDFeed(&g, 12, p, 1, false); VDFeed(&g, 12.3, p, 4, false);
    assert(!VDFeed(&g, 12.4, p, 0, false)); assert(g.lastReject == 5);
    VDFeed(&g, 13, p, 2, false); assert(!VDFeed(&g, 13.1, p, 0, false));
    puts("gesture: 13 scenarios passed");
}
