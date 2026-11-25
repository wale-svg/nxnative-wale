import sys
path = sys.argv[1]
s = open(path, encoding="utf-8").read()

def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("patch failed: %d matches for: %s" % (n, old[:80]))
    s = s.replace(old, new, 1)

rep(r'''__block int rate_n = 0;''',
r'''__block int rate_n = 0;
    int level = getenv("DM_MOTION_LEVEL") && atoi(getenv("DM_MOTION_LEVEL"));   // the pose at the first sample and at each Recenter becomes "console held upright"
    __block BOOL needLevel = YES; double *lev = calloc(9, sizeof *lev); lev[0] = lev[4] = lev[8] = 1;
    if (level) LOG("front end: motion neutral pose on (DM_MOTION_LEVEL): recenter with the phone held the way you play");''')

rep(r'''haveYaw = YES; recentred = held;''',
r'''haveYaw = YES; recentred = held; needLevel = YES;''')

rep(r'''        double dt = prev >= 0 ? fmin(d.timestamp - prev, 0.1) : 0; prev = d.timestamp;''',
r'''        if (level) {
            if (needLevel) {
                double an = sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
                if (an > 0.5) {
                                        double tl = getenv("DM_MOTION_TILT") ? atof(getenv("DM_MOTION_TILT")) * M_PI / 180 : 0, tx = 0, ty = -sin(tl), tz = -cos(tl);   // the pose it is turned into: flat (0 degrees), or tilted back by this much
                    double gx = a[0] / an, gy = a[1] / an, gz = a[2] / an, vx = gy * tz - gz * ty, vy = gz * tx - gx * tz, vz = gx * ty - gy * tx, c = gx * tx + gy * ty + gz * tz;

                    if (c > -0.99) {
                        double k2 = 1 / (1 + c), V[9] = {0, -vz, vy, vz, 0, -vx, -vy, vx, 0};
                        for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) { double v2 = 0; for (int l = 0; l < 3; l++) v2 += V[3 * i + l] * V[3 * l + j]; lev[3 * i + j] = (i == j ? 1 : 0) + V[3 * i + j] + v2 * k2; }
                        LOG("front end: motion neutral pose set, tilted %.0f degrees from upright", acos(fmin(fmax(c, -1), 1)) * 180 / M_PI);
                    }
                }
                needLevel = NO;
            }
            double ta[3] = {a[0], a[1], a[2]}, tw[3] = {w[0], w[1], w[2]};
            for (int i = 0; i < 3; i++) { a[i] = lev[3 * i] * ta[0] + lev[3 * i + 1] * ta[1] + lev[3 * i + 2] * ta[2]; w[i] = lev[3 * i] * tw[0] + lev[3 * i + 1] * tw[1] + lev[3 * i + 2] * tw[2]; }
        }
        double dt = prev >= 0 ? fmin(d.timestamp - prev, 0.1) : 0; prev = d.timestamp;''')

rep(r'''        if (pubm == 1) {''',
r'''        if (level) for (int k = 0; k < 3; k++) { double r0 = s.dir[k], r1 = s.dir[3 + k], r2 = s.dir[6 + k]; for (int i = 0; i < 3; i++) s.dir[3 * i + k] = (float)(lev[3 * i] * r0 + lev[3 * i + 1] * r1 + lev[3 * i + 2] * r2); }
        if (pubm == 1) {''')

open(path, "w", encoding="utf-8").write(s)
print("patched", path)
