#!/usr/bin/env python3
"""Test: virtuelle Tastatur (uinput) für DraStic-Belegungen.
Legt eine Tastatur "RDS Keys" an und drückt nach Countdown 80 s lang alle 2 s F12.
Aufruf: python3 rds-vkey-test.py [Sekunden bis zum ersten Druck]"""
import fcntl, os, struct, sys, time

EV_SYN, EV_KEY, KEY_F12 = 0, 1, 88
UI_SET_EVBIT, UI_SET_KEYBIT, UI_DEV_CREATE, UI_DEV_DESTROY = 0x40045564, 0x40045565, 0x5501, 0x5502

fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY)
fcntl.ioctl(fd, UI_SET_KEYBIT, KEY_F12)
dev = struct.pack("80sHHHHi", b"RDS Keys", 0x06, 0x1234, 0x5678, 1, 0) + b"\0" * (64 * 4 * 4)
os.write(fd, dev)
fcntl.ioctl(fd, UI_DEV_CREATE)

def ev(t, c, v):
    os.write(fd, struct.pack("llHHi", 0, 0, t, c, v))

wait = int(sys.argv[1]) if len(sys.argv) > 1 else 20
print("Tastatur 'RDS Keys' angelegt. Erster F12-Druck in %d s ..." % wait, flush=True)
time.sleep(wait)
for i in range(40):                       # 80 s lang alle 2 s – DraStic wartet nur ~10 s
    print("F12 (%d/40)" % (i + 1), flush=True)
    ev(EV_KEY, KEY_F12, 1); ev(EV_SYN, 0, 0); time.sleep(0.15)
    ev(EV_KEY, KEY_F12, 0); ev(EV_SYN, 0, 0)
    time.sleep(1.85)
fcntl.ioctl(fd, UI_DEV_DESTROY)
os.close(fd)
print("fertig", flush=True)
