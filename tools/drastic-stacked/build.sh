#!/bin/sh
# libdrastouch.so (ROCKNIX, GPL-2.0-or-later) für aarch64 bauen – Quelle: ROCKNIX/distribution
# projects/ROCKNIX/packages/emulators/standalone/drastic-sa/sources/libdrastouch.c (Stand 25.10.2026, mit
# DSHOOK_WINDOW_SIZE für übereinander liegende Bildschirme). RDS-Änderung: Größe ohne sscanf/strtol einlesen
# (sonst glibc-2.38-Symbole). Benötigt clang, lld, SDL2-Header (SDL=…/include) und glibc-Header.
SDL=${SDL:-/home/claude/sdl2/include}
mkdir -p compat/bits compat/gnu
printf '#define __WORDSIZE 64\n#define __WORDSIZE_TIME64_COMPAT32 0\n#define __SYSCALL_WORDSIZE 64\n' > compat/bits/wordsize.h
: > compat/gnu/stubs.h
ln -sfn "$SDL" compat/SDL2
clang --target=aarch64-linux-gnu -O2 -fPIC -shared -nostdlib -fuse-ld=lld -Wl,--allow-shlib-undefined -Wl,-z,undefs \
  -isystem compat -I"$SDL" -isystem /usr/include/x86_64-linux-gnu -isystem /usr/include -D_REENTRANT \
  -o libdrastouch.so libdrastouch.c
