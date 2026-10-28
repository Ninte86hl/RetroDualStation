#!/bin/bash
# DraStic-Tuning nach dem Vorbild von NNDDSS (Anbernic) – Test, nur solange DraStic läuft, nichts bleibt dauerhaft.
# NNDDSS-Startprotokoll (28.10.): GPU fest auf 800 MHz (performance), Emulator auf Kern 0, Grafik Kern 1, Ton Kern 3,
# 3D-Renderer auf 1–3 (nicht auf dem Emulator-Kern).
# Aufruf vom PC (DraStic läuft):
#   ssh root@IP 'bash /storage/rds-drastic-tuning.sh faeden'   Fäden von DraStic mit CPU-Last (5 s) – zum Zuordnen
#   ssh root@IP 'bash /storage/rds-drastic-tuning.sh an'       GPU performance + Kerne zuordnen
#   ssh root@IP 'bash /storage/rds-drastic-tuning.sh aus'      GPU zurück, Fäden wieder auf alle Kerne
#   ssh root@IP 'bash /storage/rds-drastic-tuning.sh status'
G=$(ls -d /sys/class/devfreq/*gpu* 2>/dev/null | head -1)
ST=/tmp/rds-tuning.state
PID=$(pidof drastic | cut -d' ' -f1)

faeden() {
    python3 - "$PID" <<'PY'
import os, sys, time
pid = int(sys.argv[1]); hz = os.sysconf("SC_CLK_TCK")
def snap():
    r = {}
    for t in os.listdir("/proc/%d/task" % pid):
        try:
            s = open("/proc/%d/task/%s/stat" % (pid, t)).read()
            f = s[s.rindex(")") + 2:].split()
            r[int(t)] = (int(f[11]) + int(f[12]), s[s.index("(") + 1:s.rindex(")")], int(f[36]))
        except OSError:
            pass
    return r
a = snap(); time.sleep(5); b = snap()
for t, (v, n, cpu) in sorted(b.items(), key=lambda x: -(x[1][0] - a.get(x[0], (x[1][0],))[0])):
    use = 100.0 * (v - a.get(t, (v,))[0]) / hz / 5
    aff = ",".join(map(str, sorted(os.sched_getaffinity(t)))) if os.path.exists("/proc/%d/task/%d" % (pid, t)) else "-"
    print("%6.1f %%  tid %-6d %-16s läuft auf Kern %d · erlaubt %s%s" % (use, t, n, cpu, aff, "  (Hauptfaden)" if t == pid else ""))
PY
}

case "$1" in
faeden)
    [ -n "$PID" ] || { echo "DraStic läuft nicht"; exit 1; }
    faeden
    ;;
an)
    [ -n "$PID" ] || { echo "DraStic läuft nicht"; exit 1; }
    if [ -n "$G" ] && [ ! -f "$ST" ]; then
        echo "gov=$(cat $G/governor) min=$(cat $G/min_freq)" > "$ST"
    fi
    [ -n "$G" ] && echo performance > "$G/governor" 2>/dev/null
    python3 - "$PID" <<'PY'
import os, sys, time
pid = int(sys.argv[1]); hz = os.sysconf("SC_CLK_TCK")
def snap():
    r = {}
    for t in os.listdir("/proc/%d/task" % pid):
        try:
            s = open("/proc/%d/task/%s/stat" % (pid, t)).read()
            f = s[s.rindex(")") + 2:].split()
            r[int(t)] = (int(f[11]) + int(f[12]), s[s.index("(") + 1:s.rindex(")")].lower())
        except OSError:
            pass
    return r
a = snap(); time.sleep(2); b = snap()
use = {t: (b[t][0] - a.get(t, b[t])[0]) / hz / 2 for t in b}
# Emulator = Hauptfaden (NNDDSS: emu=0) · Ton = Faden mit audio/sdl/pulse/alsa im Namen → Kern 3
# übrige aktive Fäden (Grafik, 3D-Renderer) → Kerne 1–3, damit Kern 0 dem Emulator allein gehört
for t, (v, n) in b.items():
    if t == pid:
        cores, what = {0}, "Emulator"
    elif any(k in n for k in ("audio", "pulse", "alsa", "pipewire", "sdlaudio")):
        cores, what = {3}, "Ton"
    else:
        cores, what = {1, 2, 3}, "Grafik/3D/Rest"
    try:
        os.sched_setaffinity(t, cores)
        print("tid %-6d %-16s %5.0f %%  → Kern %s (%s)" % (t, n, use.get(t, 0) * 100, ",".join(map(str, sorted(cores))), what))
    except OSError as e:
        print("tid %d: %s" % (t, e))
PY
    [ -n "$G" ] && echo "GPU: $(cat $G/governor) · $(( $(cat $G/cur_freq) / 1000000 )) MHz"
    ;;
aus)
    if [ -f "$ST" ] && [ -n "$G" ]; then
        gov=$(sed -n 's/^gov=\([^ ]*\).*/\1/p' "$ST"); min=$(sed -n 's/.*min=\([0-9]*\).*/\1/p' "$ST")
        echo "${gov:-simple_ondemand}" > "$G/governor"; [ -n "$min" ] && echo "$min" > "$G/min_freq"
        rm -f "$ST"
    fi
    [ -n "$PID" ] && python3 -c "import os,sys; p=int(sys.argv[1]); [os.sched_setaffinity(int(t), set(range(os.cpu_count()))) for t in os.listdir('/proc/%d/task'%p)]" "$PID" 2>/dev/null
    echo "zurück · GPU: $([ -n "$G" ] && cat $G/governor)"
    ;;
status|*)
    echo "DraStic: ${PID:-läuft nicht} · GPU: $([ -n "$G" ] && echo "$(cat $G/governor) $(( $(cat $G/cur_freq) / 1000000 )) MHz") · Merker: $([ -f $ST ] && cat $ST || echo -)"
    [ -n "$PID" ] && faeden
    ;;
esac
