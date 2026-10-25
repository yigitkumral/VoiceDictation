// VoiceDictation: donanimdan bagimsiz, kaydirmayi reddeden dort-parmak tap algilayici.
// Uc parmak gunluk macOS hareketlerinde cok kullanildigi icin hedef dort parmaktir.
#ifndef VD_GESTURE_H
#define VD_GESTURE_H
#include <stdbool.h>
#include <math.h>
#include <string.h>

#define VD_FINGERS 4

typedef struct { int id; double x, y; } VDPoint;
typedef struct {
    bool active, invalid, full;
    double start, last, lastFire;
    int ids[VD_FINGERS], seen;
    int reason, lastReject;
    double x[VD_FINGERS], y[VD_FINGERS];
} VDGesture;

static void VDReset(VDGesture *g) {
    double lastFire = g->lastFire;
    int lastReject = g->lastReject;
    memset(g, 0, sizeof(*g));
    g->lastFire = lastFire;
    g->lastReject = lastReject;
}

static void VDReject(VDGesture *g, int reason) {
    g->invalid = true;
    if (!g->reason) g->reason = reason;
}

// Her frame: yalniz fiziksel temaslar. Tamamen kalkinca en fazla bir kez true.
static bool VDFeed(VDGesture *g, double t, const VDPoint *p, int count, bool blocked) {
    if (!isfinite(t) || count < 0 || count > 16) { VDReset(g); return false; }
    if (g->active && (t < g->last || t - g->last > 0.65)) VDReject(g, 6);
    g->last = t;
    if (count == 0) {
        bool fire = g->active && !g->invalid && !blocked && g->full &&
                    t - g->start >= 0.03 && t - g->start <= 0.60 && t - g->lastFire >= 0.10;
        if (g->active && !fire) g->lastReject = g->reason ? g->reason : (!g->full ? 2 : (blocked ? 4 : 3));
        VDReset(g);
        if (fire) g->lastFire = t;
        return fire;
    }
    if (!g->active) { g->active = true; g->start = t; }
    if (blocked) VDReject(g, 4);
    if (count > VD_FINGERS) VDReject(g, 2);
    if (t - g->start > 0.60) VDReject(g, 3);
    if (!g->full && t - g->start > 0.20) VDReject(g, 5);
    if (count == VD_FINGERS) g->full = true;
    for (int i = 0; i < count && i < 16; i++) {
        if (!isfinite(p[i].x) || !isfinite(p[i].y) || p[i].x < 0 || p[i].x > 1 || p[i].y < 0 || p[i].y > 1) {
            VDReject(g, 6); continue;
        }
        int slot = 0;
        while (slot < g->seen && g->ids[slot] != p[i].id) slot++;
        if (slot == g->seen) {
            if (g->seen == VD_FINGERS) { VDReject(g, 2); continue; }
            g->ids[slot] = p[i].id; g->x[slot] = p[i].x; g->y[slot] = p[i].y; g->seen++;
        } else if (hypot(p[i].x - g->x[slot], p[i].y - g->y[slot]) > 0.035) VDReject(g, 1);
    }
    return false;
}
#endif
