import sys
path = sys.argv[1]
s = open(path, encoding="utf-8").read()

def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("patch failed: %d matches for: %s" % (n, old[:80]))
    s = s.replace(old, new, 1)

rep(r'''    if (o == UIInterfaceOrientationLandscapeRight) atomic_store(&g_home_right, 1);
    else if (o == UIInterfaceOrientationLandscapeLeft) atomic_store(&g_home_right, 0);''',
r'''    int was = atomic_load(&g_home_right), now = was;
    if (o == UIInterfaceOrientationLandscapeRight) now = 1;
    else if (o == UIInterfaceOrientationLandscapeLeft) now = 0;
    const char *pin = getenv("DM_MOTION_HOME");   // 0 = island on the right (landscape left), 1 = island on the left: pins the orientation
    if (pin && (pin[0] == '0' || pin[0] == '1')) now = pin[0] - '0';
    if (now != was) { atomic_store(&g_home_right, now); LOG("front end: motion orientation now landscape %s", now ? "right" : "left"); }''')

rep(r'''    g_motion.deviceMotionUpdateInterval = 1.0 / 120;''',
r'''    const char *hp = getenv("DM_MOTION_HOME"); if (hp && (hp[0] == '0' || hp[0] == '1')) { atomic_store(&g_home_right, hp[0] - '0'); LOG("front end: motion orientation pinned to landscape %s (DM_MOTION_HOME)", hp[0] == '1' ? "right" : "left"); }
    const char *pubs = getenv("DM_MOTION_PUB"); int pubm = pubs && !strcmp(pubs, "gyro") ? 1 : pubs && !strcmp(pubs, "dir") ? 2 : 0;   // what is published: all (default) | gyro (rate and acceleration only) | dir (orientation only)
    if (pubm) LOG("front end: motion publishes %s only (DM_MOTION_PUB)", pubm == 1 ? "rotation rate and acceleration" : "orientation");
    g_motion.deviceMotionUpdateInterval = 1.0 / 120;''')

rep(r'''        dm_phone_motion_set(&s);''',
r'''        if (pubm == 1) { static const float id9[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1}; memcpy(s.dir, id9, sizeof id9); for (int k = 0; k < 3; k++) s.angle[k] = 0; }
        else if (pubm == 2) for (int k = 0; k < 3; k++) { s.gyro[k] = 0; s.angle[k] = 0; }
        dm_phone_motion_set(&s);''')

open(path, "w", encoding="utf-8").write(s)
print("patched", path)
