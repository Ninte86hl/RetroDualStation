#!/usr/bin/env python3
"""Liegengebliebene Eingaben eines eingefrorenen Prozesses verwerfen.
Ein mit SIGSTOP angehaltener Emulator liest seine /dev/input/event*-Geräte nicht; der Kernel puffert die Tasten
für ihn und er spielt sie nach dem Aufwecken nach. pidfd_getfd holt eine Kopie genau seiner Datei-Beschreibung,
deren Puffer hier leer gelesen wird. Aufruf: evdev-flush.py <pid> [<pid> …]"""
import ctypes, os, sys

SYS_pidfd_open, SYS_pidfd_getfd = 434, 438
libc = ctypes.CDLL(None, use_errno=True)
total = 0
for pid in map(int, sys.argv[1:]):
    try:
        fds = [(int(n), os.readlink(f"/proc/{pid}/fd/{n}")) for n in os.listdir(f"/proc/{pid}/fd")]
    except OSError:
        continue
    fds = [n for n, t in fds if t.startswith("/dev/input/event")]
    if not fds:
        continue
    pfd = libc.syscall(SYS_pidfd_open, pid, 0)
    if pfd < 0:
        print("pidfd_open fehlgeschlagen", pid, ctypes.get_errno()); continue
    for n in fds:
        fd = libc.syscall(SYS_pidfd_getfd, pfd, n, 0)
        if fd < 0:
            print("pidfd_getfd fehlgeschlagen", pid, n, ctypes.get_errno()); continue
        os.set_blocking(fd, False)
        try:
            while True:
                b = os.read(fd, 24 * 64)
                if not b:
                    break
                total += len(b)
        except BlockingIOError:
            pass
        os.close(fd)
    os.close(pfd)
print("verworfen: %d Eingabe-Ereignisse" % (total // 24))
