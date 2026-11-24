import sys
path = sys.argv[1]
s = open(path, encoding="utf-8").read()

def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("patch failed: %d matches for: %s" % (n, old[:80]))
    s = s.replace(old, new, 1)

rep(r'''    g_motion.deviceMotionUpdateInterval = 1.0 / 120;''',
r'''    int euler = getenv("DM_MOTION_EULER") && atoi(getenv("DM_MOTION_EULER"));   // the angle is the phone's own pitch / yaw / roll since the recenter, whatever its resting tilt
    int eswap = getenv("DM_MOTION_SWAP") && atoi(getenv("DM_MOTION_SWAP"));   // swap the pitch and yaw axes
    __block BOOL eNeed = YES; __block double ePitch0 = 0, eRoll0 = 0, eYawPrev = 0, eYawU = 0; double *eAng = calloc(3, sizeof *eAng);
    if (euler) LOG("front end: motion angle from pitch / yaw / roll (DM_MOTION_EULER)%s: recenter with the phone held the way you play", eswap ? ", axes swapped" : "");
    g_motion.deviceMotionUpdateInterval = 1.0 / 120;''')

rep(r'''haveYaw = YES; recentred = held;''',
r'''haveYaw = YES; recentred = held; eNeed = YES;''')

rep(r'''        dm_phone_motion_set(&s);''',
r'''        if (euler) {
            float d0[9]; dm_motion_dir(hr, 0, m, yaw0, d0);   // the controller's axes in the world, unflipped: x right, y top, z out of the screen
            double px = -d0[6], py = -d0[7], pz = -d0[8];   // the aim: into the screen
            double pitch = asin(fmax(-1.0, fmin(1.0, pz)));
            double yaw = fabs(pz) > 0.94 ? atan2(-d0[3], d0[4]) : atan2(-px, py);
            double roll = asin(fmax(-1.0, fmin(1.0, (double)d0[2])));
            if (eNeed) { ePitch0 = pitch; eRoll0 = roll; eYawPrev = yaw; eYawU = 0; eNeed = NO; for (int k = 0; k < 3; k++) eAng[k] = 0; }
            double dyw = yaw - eYawPrev; while (dyw > M_PI) dyw -= 2 * M_PI; while (dyw < -M_PI) dyw += 2 * M_PI;
            eYawPrev = yaw; eYawU += dyw;
            double ang[3] = {(pitch - ePitch0) / (2 * M_PI), eYawU / (2 * M_PI), (roll - eRoll0) / (2 * M_PI)};
            if (eswap) { double sw = ang[0]; ang[0] = ang[1]; ang[1] = sw; }
            if (flip & DM_FLIP_X) ang[0] = -ang[0];
            if (flip & DM_FLIP_Y) ang[1] = -ang[1];
            for (int k = 0; k < 3; k++) { s.angle[k] = (float)ang[k]; s.gyro[k] = dt > 0 ? (float)((ang[k] - eAng[k]) / dt) : 0.f; eAng[k] = ang[k]; }
        }
        dm_phone_motion_set(&s);''')

open(path, "w", encoding="utf-8").write(s)
print("patched", path)
