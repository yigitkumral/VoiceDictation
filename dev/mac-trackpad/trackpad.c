// VoiceDictation surecine yuklenen algilayici; UI, ag, dosya veya tus enjeksiyonu yok.
#include <CoreFoundation/CoreFoundation.h>
#include <ApplicationServices/ApplicationServices.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdint.h>
#include "Gesture.h"

typedef const void *Device;
typedef struct { float x, y; } VDNativePoint;
typedef struct { VDNativePoint position, velocity; } Vector;
typedef struct {
    int32_t frame; double timestamp;
    int32_t path, stage, finger, hand;
    Vector normalized;
    float total, pressure, angle, major, minor;
    Vector absolute;
    int32_t reserved1, reserved2;
    float density;
} Contact;
_Static_assert(sizeof(Contact) == 96, "Unexpected MultitouchSupport ABI");
typedef void (*FrameCallback)(Device, Contact *, size_t, double, size_t, void *);
static CFArrayRef (*createList)(void);
static bool (*builtIn)(Device);
static bool (*registerFrame)(Device, FrameCallback, void *);
static void (*unregisterFrame)(Device, FrameCallback);
static int (*startDevice)(Device, int);
static int (*stopDevice)(Device);
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static VDGesture gesture;
static CFArrayRef devices;
static Device device;
static void *library;
static void (*tapCallback)(void);
static bool enabled;
static unsigned long frameCount, tapCount;
static unsigned long rejected[7];
static unsigned long fullRejected[7];

static void contacts(Device dev, Contact *input, size_t count, double timestamp, size_t frame, void *ref) {
    if (count > 16 || (count && !input)) return;
    VDPoint points[16]; int n = 0;
    for (size_t i = 0; i < count; i++) {
        if (input[i].stage == 3 || input[i].stage == 4)
            points[n++] = (VDPoint){input[i].path, input[i].normalized.position.x, input[i].normalized.position.y};
    }
    CGEventFlags flags = CGEventSourceFlagsState(kCGEventSourceStateCombinedSessionState);
    bool blocked = (flags & (kCGEventFlagMaskShift | kCGEventFlagMaskControl | kCGEventFlagMaskAlternate | kCGEventFlagMaskCommand)) ||
        CGEventSourceButtonState(kCGEventSourceStateCombinedSessionState, kCGMouseButtonRight);
    pthread_mutex_lock(&mutex);
    frameCount++;
    bool hadGesture = gesture.active;
    bool hadFull = gesture.full;
    bool fire = VDFeed(&gesture, timestamp, points, n, blocked || !enabled);
    if (enabled && hadGesture && n == 0 && !fire && gesture.lastReject >= 0 && gesture.lastReject < 7) {
        rejected[gesture.lastReject]++;
        if (hadFull) fullRejected[gesture.lastReject]++;
    }
    if (fire && tapCallback) {
        tapCount++;
        // Callback yalniz sinirli Python kuyruguna olay birakir; model/GUI calistirmaz.
        tapCallback();
    }
    pthread_mutex_unlock(&mutex);
}

void vd_trackpad_enable(int value) {
    pthread_mutex_lock(&mutex);
    enabled = value != 0; VDReset(&gesture);
    pthread_mutex_unlock(&mutex);
}

void vd_trackpad_counts(unsigned long *frames, unsigned long *taps) {
    pthread_mutex_lock(&mutex);
    *frames = frameCount; *taps = tapCount;
    pthread_mutex_unlock(&mutex);
}

void vd_trackpad_rejections(unsigned long *values) {
    pthread_mutex_lock(&mutex);
    memcpy(values, rejected, sizeof(rejected));
    pthread_mutex_unlock(&mutex);
}

int vd_trackpad_fingers(void) { return VD_FINGERS; }

void vd_trackpad_full_rejections(unsigned long *values) {
    pthread_mutex_lock(&mutex);
    memcpy(values, fullRejected, sizeof(fullRejected));
    pthread_mutex_unlock(&mutex);
}

int vd_trackpad_start(void (*callback)(void)) {
    if (device) return -4;
    if (!library) library = dlopen("/System/Library/PrivateFrameworks/MultitouchSupport.framework/MultitouchSupport", RTLD_LOCAL | RTLD_NOW);
    if (!library) return -1;
    createList = dlsym(library, "MTDeviceCreateList");
    builtIn = dlsym(library, "MTDeviceIsBuiltIn");
    registerFrame = dlsym(library, "MTRegisterContactFrameCallbackWithRefcon");
    unregisterFrame = dlsym(library, "MTUnregisterContactFrameCallback");
    startDevice = dlsym(library, "MTDeviceStart"); stopDevice = dlsym(library, "MTDeviceStop");
    if (!createList || !builtIn || !registerFrame || !unregisterFrame || !startDevice || !stopDevice) return -1;
    devices = createList();
    for (CFIndex i = 0; devices && i < CFArrayGetCount(devices); i++) {
        Device candidate = CFArrayGetValueAtIndex(devices, i);
        if (builtIn(candidate)) { device = candidate; break; }
    }
    if (!device) { if (devices) CFRelease(devices); devices = NULL; return -2; }
    tapCallback = callback;
    registerFrame(device, contacts, NULL);
    int result = startDevice(device, 0);
    if (result != 0) {
        unregisterFrame(device, contacts); CFRelease(devices);
        devices = NULL; device = NULL; tapCallback = NULL; return -3;
    }
    return 0;
}

void vd_trackpad_stop(void) {
    vd_trackpad_enable(0);
    if (device) { stopDevice(device); unregisterFrame(device, contacts); }
    pthread_mutex_lock(&mutex); tapCallback = NULL; pthread_mutex_unlock(&mutex);
    if (devices) CFRelease(devices);
    devices = NULL; device = NULL;
    // Ozel framework process sonuna kadar yuklu kalir; gec callback icin dlclose yok.
}
