#!/bin/bash
# Leistung messen, während ein Spiel läuft: CPU (gesamt, je Kern, Takt), Emulator-Prozess, RAM, GPU (Takt/Last),
# Temperatur, GPU-Treiber. Aufruf vom PC (Spiel läuft schon):
#   ssh root@IP 'bash /storage/rds-leistung.sh NAME [SEKUNDEN]'     z. B. drastic-libmali 30
# Ergebnis zusätzlich in /storage/rds-leistung-NAME.txt
NAME=${1:-test}; SECS=${2:-30}
OUT=/storage/rds-leistung-$NAME.txt
exec > >(tee "$OUT") 2>&1
python3 - "$NAME" "$SECS" <<'PY'
import glob, os, sys, time
name, secs = sys.argv[1], int(sys.argv[2])

def rd(p):
    try:
        return open(p).read().strip()
    except OSError:
        return None

def cpu_times():
    out = {}
    for line in open("/proc/stat"):
        if line.startswith("cpu"):
            p = line.split()
            v = list(map(int, p[1:]))
            out[p[0]] = (sum(v), v[3] + v[4])           # gesamt, idle+iowait
    return out

EMUS = ("drastic", "drastic_v2522", "dsperate", "retroarch", "ppsspp", "PPSSPPSDL", "mupen64plus", "flycast")
def emu_pids():
    res = {}
    for d in glob.glob("/proc/[0-9]*"):
        c = rd(d + "/comm")
        if c in EMUS:
            res[int(d[6:])] = c
    return res

def proc_ticks(pid):
    s = rd("/proc/%d/stat" % pid)
    if not s:
        return None
    f = s[s.rindex(")") + 2:].split()
    return int(f[11]) + int(f[12])                       # utime + stime

def meminfo():
    m = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":")
        m[k] = int(v.split()[0]) // 1024
    return m

gpu = next(iter(glob.glob("/sys/class/devfreq/*gpu*")), None)
mods = rd("/proc/modules") or ""
driver = "panfrost" if "panfrost" in mods else "mali (libmali)" if ("mali" in mods or os.path.exists("/dev/mali0")) else "?"
print("=== Leistung: %s · %s · %s" % (name, time.strftime("%d.%m. %H:%M"), rd("/proc/device-tree/model").strip("\0")))
print("GPU-Treiber:", driver, "· GPU-devfreq:", gpu or "-", "· Governor:", rd(gpu + "/governor") if gpu else "-")
print("CPU-Governor:", rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
      "· max", int(rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq") or 0) // 1000, "MHz")
emus = emu_pids()
print("Emulator:", ", ".join("%s (%d)" % (c, p) for p, c in emus.items()) or "KEINER läuft – Ergebnis nur Grundlast")
hz = os.sysconf("SC_CLK_TCK")
ncpu = os.cpu_count()
S = {k: [] for k in ("cpu", "emu", "freq", "gpuf", "gpul", "temp", "avail", "swap")}
cores = {}
t0, e0 = cpu_times(), {p: proc_ticks(p) for p in emus}
w0 = time.time()
for i in range(secs):
    time.sleep(1)
    t1, w1 = cpu_times(), time.time()
    tot = t1["cpu"][0] - t0["cpu"][0]
    S["cpu"].append(100 * (1 - (t1["cpu"][1] - t0["cpu"][1]) / max(tot, 1)))
    for k in t1:
        if k != "cpu":
            dt = t1[k][0] - t0[k][0]
            cores.setdefault(k, []).append(100 * (1 - (t1[k][1] - t0[k][1]) / max(dt, 1)))
    e1 = {p: proc_ticks(p) for p in emus}
    S["emu"].append(sum(100 * (e1[p] - e0[p]) / hz / (w1 - w0) for p in emus if e1.get(p) is not None and e0.get(p) is not None))
    S["freq"].append(int(rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") or 0) // 1000)
    if gpu:
        S["gpuf"].append(int(rd(gpu + "/cur_freq") or 0) // 1000000)
        l = rd(gpu + "/load")
        if l and "@" in l:
            S["gpul"].append(int(l.split("@")[0]))
    temps = [int(rd(z) or 0) / 1000 for z in glob.glob("/sys/class/thermal/thermal_zone*/temp")]
    S["temp"].append(max(temps) if temps else 0)
    m = meminfo()
    S["avail"].append(m["MemAvailable"]); S["swap"].append(m["SwapTotal"] - m["SwapFree"])
    t0, e0, w0 = t1, e1, w1

def st(v, unit=""):
    return "Ø %.0f%s (min %.0f · max %.0f)" % (sum(v) / len(v), unit, min(v), max(v)) if v else "-"
print("\nMessung über %d s:" % secs)
print("  CPU gesamt:      ", st(S["cpu"], " %"))
print("  je Kern Ø:       ", "  ".join("%s %.0f%%" % (k[3:], sum(v) / len(v)) for k, v in sorted(cores.items())))
print("  Emulator-Prozess:", st(S["emu"], " %"), "(100 % = ein Kern voll, max %d %%)" % (100 * ncpu))
print("  CPU-Takt:        ", st(S["freq"], " MHz"))
print("  GPU-Takt:        ", st(S["gpuf"], " MHz"))
print("  GPU-Last:        ", st(S["gpul"], " %") if S["gpul"] else "- (Treiber meldet keine Last)")
print("  Temperatur:      ", st(S["temp"], " °C"))
print("  RAM frei:        ", st(S["avail"], " MB"))
print("  Swap belegt:     ", st(S["swap"], " MB"))
PY
echo "Gespeichert: $OUT"
