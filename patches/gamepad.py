import sys
path = sys.argv[1]
s = open(path, encoding="utf-8").read()

def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("patch failed: %d matches for: %s" % (n, old[:80]))
    s = s.replace(old, new, 1)

rep(r'''static NSString *const k_layout_key = @"DmPadLayout";''',
r'''static NSString *const k_offsets_key = @"DmPadOffsets";   // per-control offsets (DM_PAD_EDIT=1 moves them)
static NSString *const k_layout_key = @"DmPadLayout";''')

rep(r'''    UITouch *_game[16];''',
r'''    CGPoint _off[19];                              // control offsets in u: 0..15 the B_ keys, 16 the diamond, 17 the left stick, 18 the D-pad
    BOOL _edit; UITouch *_dragT; int _dragId; CGPoint _dragStart, _dragOff0;
    CAShapeLayer *_rring, *_rknob;                 // the right stick, drawn while held
    UITouch *_game[16];''')

rep(r'''        _knob = shape(_controls);''',
r'''        _knob = shape(_controls);
        _rring = shape(_controls); _rring.fillColor = k_ringFill.CGColor; _rring.hidden = YES;
        _rknob = shape(_controls); _rknob.hidden = YES;''')

rep(r'''        [self applyLayout];
        NSNotificationCenter *nc = NSNotificationCenter.defaultCenter;''',
r'''        [self loadOffsets];
        [self applyLayout];
        NSNotificationCenter *nc = NSNotificationCenter.defaultCenter;''')

rep(r'''- (CGPoint)faceCenter { CGRect s = self.corner; CGFloat u = self.u;''',
r'''- (CGPoint)faceCenter { return [self moved:16 point:[self faceCenterBase]]; }
- (CGPoint)faceCenterBase { CGRect s = self.corner; CGFloat u = self.u;''')
rep(r'''- (CGPoint)stickHome {''',
r'''- (CGPoint)stickHome { return [self moved:17 point:[self stickHomeBase]]; }
- (CGPoint)stickHomeBase {''')
rep(r'''- (CGPoint)dpadCenter {''',
r'''- (CGPoint)dpadCenter { return [self moved:18 point:[self dpadCenterBase]]; }
- (CGPoint)dpadCenterBase {''')
rep(r'''- (CGPoint)dropCenter:(int)b { CGRect s = self.safe; CGFloat u = self.u; BOOL z = b == B_ZL || b == B_ZR;''',
r'''- (CGPoint)dropCenter:(int)b { return [self moved:b point:[self dropCenterBase:b]]; }
- (CGPoint)dropCenterBase:(int)b { CGRect s = self.safe; CGFloat u = self.u; BOOL z = b == B_ZL || b == B_ZR;''')
rep(r'''- (CGPoint)clickCenter:(int)b { CGRect s = self.safe; CGFloat u = self.u; CGFloat edge = _layout.separated ? 22 : 0;''',
r'''- (CGPoint)clickCenter:(int)b { return [self moved:b point:[self clickCenterBase:b]]; }
- (CGPoint)clickCenterBase:(int)b { CGRect s = self.safe; CGFloat u = self.u; CGFloat edge = _layout.separated ? 22 : 0;''')
rep(r'''- (CGRect)pillRect:(int)b { CGRect s = self.safe; CGFloat u = self.u, w = K_PILL_W * u, h = K_PILL_H * u;''',
r'''- (CGRect)pillRect:(int)b { CGRect r = [self pillRectBase:b]; CGPoint o = [self moved:b point:CGPointZero]; return CGRectOffset(r, o.x, o.y); }
- (CGRect)pillRectBase:(int)b { CGRect s = self.safe; CGFloat u = self.u, w = K_PILL_W * u, h = K_PILL_H * u;''')

rep(r'''// ---- Touch ----
- (void)recompute {''',
r'''// ---- Movable controls (DM_PAD_EDIT=1) ----
- (void)loadOffsets {
    const char *rs = getenv("DM_PAD_RESET"), *ed = getenv("DM_PAD_EDIT");
    if (rs && atoi(rs)) [NSUserDefaults.standardUserDefaults removeObjectForKey:k_offsets_key];
    NSArray<NSNumber *> *a = [NSUserDefaults.standardUserDefaults arrayForKey:k_offsets_key];
    for (int i = 0; i < 19 && a.count >= (NSUInteger)(2 * i + 2); i++) _off[i] = CGPointMake(a[2 * i].doubleValue, a[2 * i + 1].doubleValue);
    _edit = ed && atoi(ed);
    if (_edit) LOG("front end: touch controls edit mode (DM_PAD_EDIT): drag a control to move it, remove the switch to play");
}
- (void)saveOffsets {
    NSMutableArray *a = [NSMutableArray array];
    for (int i = 0; i < 19; i++) { [a addObject:@(_off[i].x)]; [a addObject:@(_off[i].y)]; }
    [NSUserDefaults.standardUserDefaults setObject:a forKey:k_offsets_key];
}
- (CGPoint)moved:(int)i point:(CGPoint)p { CGFloat u = self.u; return CGPointMake(p.x + _off[i].x * u, p.y + _off[i].y * u); }
- (int)editHit:(CGPoint)p {
    int b = [self btnAt:p]; if (b >= 0) return b;
    if (dist(p, self.faceCenter) / (self.faceGap + MAX(self.faceR * 1.6, self.faceHitR)) <= 1) return 16;
    if (_full && dist(p, self.dpadCenter) / MAX(self.dpadR * K_DPAD_GRAB, 22) < 1) return 18;
    if (dist(p, self.stickHome) / MAX([self stickR:0] * K_STICK_GRAB, 22) < 1) return 17;
    return -1;
}
- (CGPoint)controlCentre:(int)i {
    if (i == 16) return self.faceCenter;
    if (i == 17) return self.stickHome;
    if (i == 18) return self.dpadCenter;
    if (i == B_PLUS || i == B_MINUS) { CGRect r = [self pillRect:i]; return CGPointMake(CGRectGetMidX(r), CGRectGetMidY(r)); }
    return isClick(i) ? [self clickCenter:i] : [self dropCenter:i];
}
- (void)dragTo:(CGPoint)p {
    CGFloat u = MAX(self.u, 0.01); CGPoint old = _off[_dragId];
    _off[_dragId] = CGPointMake(_dragOff0.x + (p.x - _dragStart.x) / u, _dragOff0.y + (p.y - _dragStart.y) / u);
    if (!CGRectContainsPoint(CGRectInset(self.bounds, 10, 10), [self controlCentre:_dragId])) _off[_dragId] = old;
    [self setNeedsLayout];
}

// ---- Touch ----
- (void)recompute {''')

rep(r'''    BOOL stick = _stick[0] != nil;''',
r'''    BOOL stick = _stick[0] != nil || _stick[1] != nil;''')

rep(r'''        if (_padOff) { game |= [self gameBegin:t]; continue; }''',
r'''        if (_edit) { CGPoint ep = [t locationInView:self]; int cid = [self editHit:ep]; if (cid >= 0 && !_dragT) { _dragT = t; _dragId = cid; _dragStart = ep; _dragOff0 = _off[cid]; } continue; }
        if (_padOff) { game |= [self gameBegin:t]; continue; }''')

rep(r'''        uint64_t v = [_owner objectForKey:t].unsignedLongLongValue; int c = (int)(v & 0xff); CGPoint p = [t locationInView:self];''',
r'''        uint64_t v = [_owner objectForKey:t].unsignedLongLongValue; int c = (int)(v & 0xff); CGPoint p = [t locationInView:self];
        if (_edit) { if (t == _dragT) [self dragTo:p]; continue; }''')

rep(r'''        if ((v & 0xff) == C_GAME && (v >> 8) < 16) { _game[v >> 8] = nil; game = YES; }''',
r'''        if (t == _dragT) { _dragT = nil; [self saveOffsets]; }
        if ((v & 0xff) == C_GAME && (v >> 8) < 16) { _game[v >> 8] = nil; game = YES; }''')

rep(r'''    setPath(_knob, circlePath(CGPointMake(k, k), k));''',
r'''    setPath(_knob, circlePath(CGPointMake(k, k), k));
    _rknob.bounds = CGRectMake(0, 0, 2 * k, 2 * k); setPath(_rknob, circlePath(CGPointMake(k, k), k));''')

rep(r'''    for (int b = 0; b < B_N; b++) { BOOL on = (all >> b) & 1;''',
r'''    for (int b = 0; b < B_N; b++) { BOOL on = ((all >> b) & 1) || _edit;''')

rep(r'''    _knob.position = CGPointMake(h.x + o.x, h.y + o.y); _knob.fillColor = (_stick[0] ? k_on : k_idle).CGColor;''',
r'''    _knob.position = CGPointMake(h.x + o.x, h.y + o.y); _knob.fillColor = ((_stick[0] || _edit) ? k_on : k_idle).CGColor;
    BOOL rd = _stick[1] != nil && _full && !_tap;   // the right stick, drawn while held
    _rring.hidden = _rknob.hidden = !rd;
    if (rd) { CGPoint rcn = _rCentre, rof = [self knobOffset:1]; setPath(_rring, circlePath(rcn, [self stickR:1])); _rknob.position = CGPointMake(rcn.x + rof.x, rcn.y + rof.y); _rknob.fillColor = k_on.CGColor; }''')

rep(r'''    int flip = dm_motion_flip_parse(getenv("DM_MOTION_FLIP"));''',
r'''    const char *gyf = getenv("DM_MOTION_GYRO"), *rtf = getenv("DM_MOTION_ROT");   // tuning: gyro axes to flip (letters x y z), the frame turned about the screen normal (degrees)
    double gsx = gyf && strchr(gyf, 'x') ? -1 : 1, gsy = gyf && strchr(gyf, 'y') ? -1 : 1, gsz = gyf && strchr(gyf, 'z') ? -1 : 1;
    double rot = rtf ? atof(rtf) * M_PI / 180 : 0, rcs = cos(rot), rsn = sin(rot);
    if (gyf || rtf) LOG("front end: motion tuning: gyro axes flipped: %s, frame turned %.1f degrees", gyf ? gyf : "none", rot * 180 / M_PI);
    int flip = dm_motion_flip_parse(getenv("DM_MOTION_FLIP"));''')

rep(r'''        dm_motion_vec(hr, flip, ga, a); dm_motion_vec(hr, flip, ro, w);''',
r'''        dm_motion_vec(hr, flip, ga, a); dm_motion_vec(hr, flip, ro, w);
        w[0] *= gsx; w[1] *= gsy; w[2] *= gsz;
        if (rot != 0) {
            double t0 = a[0], t1 = a[1]; a[0] = rcs * t0 + rsn * t1; a[1] = -rsn * t0 + rcs * t1;
            t0 = w[0]; t1 = w[1]; w[0] = rcs * t0 + rsn * t1; w[1] = -rsn * t0 + rcs * t1;
        }''')

rep(r'''        dm_motion_dir(hr, flip, m, yaw0, s.dir);''',
r'''        dm_motion_dir(hr, flip, m, yaw0, s.dir);
        if (rot != 0) for (int k = 0; k < 3; k++) { double r0 = s.dir[k], r1 = s.dir[3 + k]; s.dir[k] = (float)(rcs * r0 + rsn * r1); s.dir[3 + k] = (float)(-rsn * r0 + rcs * r1); }''')

open(path, "w", encoding="utf-8").write(s)
print("patched", path)
