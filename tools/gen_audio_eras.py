"""Era music loops (Iron Age -> The Data Center) and the weapon / ability SFX for eras 3-10.
Everything is synthesized from scratch (numpy additive + filtered noise, no samples, no licensing).

Run: python3 tools/gen_audio_eras.py assets/audio [name ...]
  - music is written as OGG Vorbis (needs ffmpeg with libvorbis), 22050 Hz mono, seamless loop:
    every track is rendered with a tail that is overlap-added back onto the start (so ringing notes and
    reverb wrap around), continuous layers use whole-cycle frequencies and all bus filters / reverb are
    circular FFT ops, so sample N-1 flows straight into sample 0.
  - SFX are 22050 Hz mono 16-bit WAV, normalized the same way as tools/gen_audio.py.
  - optional extra args restrict the run to those names (e.g. `music_iron laser`).
Companion of tools/gen_audio.py (Stone/Bronze music + base SFX)."""
import sys, os, re, wave, subprocess, tempfile
from functools import lru_cache
import numpy as np

SR = 22050
NYQ = SR / 2
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/audio"
ONLY = set(sys.argv[2:])
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(2077)


def want(name):
    return not ONLY or name in ONLY


# ================================================================ DSP helpers
def ns(d):
    return max(1, int(round(SR * d)))


def T(n):
    return np.arange(n) / SR


def noise(n):
    return rng.uniform(-1, 1, n)


def nrm(x):
    m = np.max(np.abs(x))
    return x / m if m > 0 else x


def unit(x):
    s = np.std(x)
    return x / s if s > 0 else x


def endfade(x, m=96):
    x = np.array(x, dtype=np.float64)
    m = min(m, len(x))
    x[-m:] *= np.linspace(1, 0, m)
    return x


def fft_filter(x, g, pad=True):
    """Zero-phase FFT filter. pad=False keeps it circular (what we want on loop buffers)."""
    p = min(len(x), SR // 8) if pad else 0
    y = np.concatenate([np.zeros(p), x, np.zeros(p)]) if p else x
    Y = np.fft.rfft(y)
    Y *= g(np.fft.rfftfreq(len(y), 1 / SR))
    y = np.fft.irfft(Y, len(y))
    return y[p:p + len(x)] if p else y


def lp(x, fc, order=4, pad=True):
    return fft_filter(x, lambda f: 1 / (1 + (f / fc) ** order), pad)


def hp(x, fc, order=4, pad=True):
    return fft_filter(x, lambda f: (f / fc) ** order / (1 + (f / fc) ** order), pad)


def bp(x, lo, hi, pad=True):
    return hp(lp(x, hi, pad=pad), lo, pad=pad)


def perc(n, a=0.002, dec=0.2):
    t = T(n)
    return np.minimum(1, t / max(a, 1e-5)) * np.exp(-np.maximum(0, t - a) / dec)


def adsr(n, gate, a=0.01, d=0.1, s=0.7, r=0.08):
    t = T(n)
    e = np.where(t < a, t / max(a, 1e-5), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-5)))
    return e * np.where(t < gate, 1.0, np.exp(-(t - gate) / max(r, 1e-5)))


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def at(x, d):
    """Delay a sound by d seconds."""
    return np.concatenate([np.zeros(ns(d)), x])


def sweep(f0, f1, d, shape="sine", geo=True):
    n = ns(d)
    f = np.geomspace(f0, f1, n) if geo else np.linspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == "square":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def thud(f=80, d=0.25, drop=0.5):
    return endfade(sweep(f, f * drop, d) * perc(ns(d), 0.002, d * 0.25), ns(0.02))


def clank(f=520, d=0.35):
    t = T(ns(d))
    s = sum(np.sin(2 * np.pi * f * r * t) * a for r, a in ((1, 1), (2.76, 0.6), (5.4, 0.4), (8.93, 0.25)) if f * r < NYQ * 0.95)
    return endfade(s * perc(len(t), 0.001, d * 0.25), ns(0.02))


def stft_filter(x, gain):
    """Time-varying filter: gain(freq[1,bins], time[frames,1]) -> (frames, bins). For whooshes / doppler."""
    nfft, hop = 512, 128
    w = np.hanning(nfft)
    p = np.concatenate([np.zeros(nfft), x, np.zeros(nfft)])
    nf = (len(p) - nfft) // hop + 1
    idx = hop * np.arange(nf)[:, None] + np.arange(nfft)[None, :]
    F = np.fft.rfft(p[idx] * w, axis=1)
    fr = np.fft.rfftfreq(nfft, 1 / SR)[None, :]
    tm = ((hop * np.arange(nf) + nfft / 2 - nfft) / SR)[:, None]
    y = np.fft.irfft(F * gain(fr, tm), nfft, axis=1) * w
    out = np.zeros(len(p))
    for i in range(nf):
        out[i * hop:i * hop + nfft] += y[i]
    return out[nfft:nfft + len(x)] / 1.5


def band(fc_of_t, width_oct=0.6):
    return lambda f, t: np.exp(-0.5 * (np.log2(np.maximum(f, 1) / fc_of_t(t)) / width_oct) ** 2)


# ================================================================ pitch helpers
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(nm):
    m = re.fullmatch(r"([A-G])([#b]?)(-?\d)", nm)
    return 12 * (int(m[3]) + 1) + PC[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]]


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def hz(nm, tr=0):
    return mhz(midi(nm) + tr)


def chord(sym, octave=3):
    """'Dm' -> midi [D3, F3, A3]; 'Bb' -> major; 'E5' -> power chord (root, fifth, octave)."""
    m = re.fullmatch(r"([A-G][#b]?)(m|5)?", sym)
    r = midi(m[1] + str(octave))
    return [r, r + {"m": 3, "5": 7, None: 4}[m[2]], r + {"m": 7, "5": 12, None: 7}[m[2]]]


# ================================================================ instruments (cached: same note -> same array)
def additive(ph, f, weights):
    out = np.zeros(len(ph))
    for k, w in enumerate(weights, 1):
        if w and k * f < NYQ * 0.9:
            out += w * np.sin(k * ph)
    return out


def phase(f, n, vib=0.0, rate=5.5, scoop=0.0):
    t = T(n)
    fr = np.full(n, float(f))
    if scoop:
        fr *= 1 - scoop * np.exp(-t / 0.04)
    if vib:
        fr *= 1 + vib * np.sin(2 * np.pi * rate * t) * np.clip((t - 0.12) / 0.25, 0, 1)
    return 2 * np.pi * np.cumsum(fr) / SR


@lru_cache(maxsize=None)
def wind(f, d, weights, vib=0.005, rate=5.5, a=0.03, r=0.06, breath=0.05, chiff=0.0, detune=0.0):
    n = ns(d + 5 * r)
    s = additive(phase(f, n, vib, rate), f, weights)
    if detune:
        s += 0.6 * additive(phase(f * (1 + detune), n, vib, rate * 1.07), f, weights)
    s = nrm(s)
    if breath:
        s += unit(bp(noise(n), f * 0.9, min(f * 5, NYQ * 0.9))) * breath
    if chiff:
        s += unit(bp(noise(n), 1500, 6000)) * np.exp(-T(n) / 0.012) * chiff
    return endfade(s * adsr(n, d, a, 0.15, 0.85, r))


def pipe(f, d):  # Celtic whistle / chanter blend
    return wind(f, d, (1, .35, .3, .12, .1, .05), vib=.004, rate=6, a=.015, r=.05, breath=.07)


def aulos(f, d):  # nasal double reed, two slightly detuned pipes
    w = tuple(k ** -0.6 * (0.35 + 1.6 * np.exp(-((k * f - 1100) / 650) ** 2)) for k in range(1, 15))
    return wind(f, d, w, vib=.005, rate=5, a=.04, r=.07, breath=.04, detune=.0035)


def recorder(f, d):
    return wind(f, d, (1, .1, .16, .03), vib=.003, rate=5, a=.02, r=.05, breath=.05, chiff=.25)


def fife(f, d):
    return wind(f, d, (1, .08, .22, .03, .04), vib=.006, rate=6.5, a=.01, r=.04, breath=.09, chiff=.2)


@lru_cache(maxsize=None)
def brass(f, d, a=0.04, r=0.08, K=14, bright=1.0, vib=0.004, s=0.8):
    n = ns(d + 5 * r)
    ph = phase(f, n, vib, 5, scoop=0.025)
    e = adsr(n, d, a, 0.12, s, r)
    out = np.zeros(n)
    for k in range(1, K + 1):
        if k * f > NYQ * 0.9:
            break
        out += np.sin(k * ph) / k ** 0.9 * e ** (1 + 0.45 * (k - 1) / bright)
    return endfade(nrm(out))


def tuba(f, d):
    return brass(f, d, a=0.015, r=0.05, K=9, bright=0.6, vib=0.0, s=0.55)


@lru_cache(maxsize=None)
def pluck(f, ring, pos=0.25, bright=0.5, dec=1.2, K=24, inh=0.00015):
    n = ns(ring)
    t = T(n)
    out = np.zeros(n)
    for k in range(1, K + 1):
        fk = k * f * np.sqrt(1 + inh * k * k)
        if fk > NYQ * 0.9:
            break
        amp = abs(np.sin(np.pi * k * pos)) / k ** (1.6 - bright)
        out += amp * np.sin(2 * np.pi * fk * t) * np.exp(-t / dec * (1 + 0.15 * (k - 1) ** 1.3))
    out = nrm(out) * np.minimum(1, t / 0.0015)
    m = ns(0.006)
    out[:m] += unit(hp(noise(m), 2500)) * np.linspace(0.25, 0, m) * bright
    return endfade(out)


def lute(f, ring=0.9):
    return pluck(f, ring, pos=0.18, bright=0.6, dec=0.55)


def lyre(f, ring=1.4):
    return pluck(f, ring, pos=0.45, bright=0.35, dec=0.9)


def harp(f, ring=1.2):
    return pluck(f, ring, pos=0.3, bright=0.55, dec=0.7)


@lru_cache(maxsize=None)
def synth(f, d, wave="saw", fc=2500.0, fenv=0.0, fdec=0.08, detune=0.0, a=0.005, dcy=0.15, s=0.7, r=0.06, vib=0.0, K=48):
    """Band-limited saw / square with (optionally enveloped) 4-pole-ish low-pass, done per harmonic."""
    n = ns(d + 5 * r)
    t = T(n)
    fct = fc + fenv * np.exp(-t / fdec) if fenv else None
    out = np.zeros(n)
    for dt in ((0.0,) if not detune else (-detune, detune)):
        ff = f * (1 + dt)
        ph = phase(ff, n, vib, 5.2)
        for k in range(1, K + 1, 2 if wave == "square" else 1):
            if k * ff > NYQ * 0.9:
                break
            if fct is None:
                g = 1 / (1 + (k * ff / fc) ** 4)
                if g < 0.002:
                    break
            else:
                g = 1 / (1 + (k * ff / fct) ** 4)
            out += g / k * np.sin(k * ph + (k * 1.7 if dt > 0 else 0))
    return endfade(nrm(out) * adsr(n, d, a, dcy, s, r))


# ---------------------------------------------------------------- drums
@lru_cache(maxsize=None)
def kick(f0=150.0, f1=48.0, dec=0.28, click=0.4, pdec=0.035, v=0):
    n = ns(dec * 5)
    t = T(n)
    fr = f1 + (f0 - f1) * np.exp(-t / pdec)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / dec)
    s += unit(hp(noise(n), 2000)) * np.exp(-t / 0.003) * click
    return endfade(nrm(s))


@lru_cache(maxsize=None)
def snare(tone=190.0, dec=0.12, snap=1.0, hpf=1200.0, v=0):
    n = ns(dec * 5)
    t = T(n)
    s = np.sin(2 * np.pi * tone * t) * np.exp(-t / 0.04) + unit(hp(noise(n), hpf)) * np.exp(-t / dec) * snap * 0.5
    return endfade(nrm(s))


@lru_cache(maxsize=None)
def hat(dec=0.025, hpf=6000.0, metal=0.5, v=0):
    n = ns(max(dec * 6, 0.03))
    t = T(n)
    m = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (587, 845, 1190, 1426, 1660, 2120))
    s = hp(unit(noise(n)) + metal * unit(m), hpf)
    return endfade(nrm(s * np.exp(-t / dec)))


@lru_cache(maxsize=None)
def clap(v=0):
    n = ns(0.3)
    t = T(n)
    e = sum(np.exp(-np.maximum(0, t - o) / 0.006) * (t >= o) for o in (0, 0.011, 0.022)) + 0.6 * np.exp(-np.maximum(0, t - 0.03) / 0.07) * (t >= 0.03)
    return endfade(nrm(bp(noise(n), 900, 3500) * e))


@lru_cache(maxsize=None)
def skin(f0, f1, dec, nz=0.4, nlp=1200.0, v=0):
    """Hand / frame drums: pitched membrane thump plus skin noise."""
    n = ns(dec * 5)
    t = T(n)
    fr = f1 + (f0 - f1) * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / dec)
    s += unit(lp(noise(n), nlp)) * np.exp(-t / 0.025) * nz
    return endfade(nrm(s * np.minimum(1, t / 0.0012)))


@lru_cache(maxsize=None)
def tabor(accent=True, v=0):
    n = ns(0.4)
    t = T(n)
    fr = 200 + 50 * np.exp(-t / 0.02)
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.06)
    s += unit(bp(noise(n), 1800, 6000)) * np.exp(-t / (0.09 if accent else 0.05)) * 0.5   # snare string buzz
    return endfade(nrm(s))


@lru_cache(maxsize=None)
def metal(f, d, v=0):
    return endfade(nrm(clank(f, d) + 0.2 * unit(hp(noise(ns(d)), 3000)) * perc(ns(d), 0.0005, 0.01)))


@lru_cache(maxsize=None)
def chuff(v=0):
    n = ns(0.12)
    return endfade(nrm(bp(noise(n), 700, 3500) * perc(n, 0.004, 0.035)))


@lru_cache(maxsize=None)
def crash(d=1.6, v=0):
    n = ns(d)
    t = T(n)
    m = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (431, 619, 877, 1093, 1488, 1871))
    return endfade(nrm(hp(unit(noise(n)) + 0.4 * unit(m), 3500) * np.exp(-t / (d / 4))))


def glitch(kind):
    if kind == 0:  # bit-crushed blip
        f = rng.choice([1500, 2200, 3100, 4400])
        n = ns(0.025)
        s = np.round(np.sign(np.sin(2 * np.pi * f * T(n))) * perc(n, 0.001, 0.01) * 3) / 3
    elif kind == 1:  # noise grain
        n = ns(0.014)
        s = hp(noise(n), 2500) * np.hanning(n)
    elif kind == 2:  # stutter
        g = hp(noise(ns(0.007)), 1500) * np.hanning(ns(0.007))
        s = mix(*[at(g * 0.85 ** i, i * 0.031) for i in range(4)])
    elif kind == 3:  # low digital click
        n = ns(0.035)
        s = np.round(np.sin(2 * np.pi * 95 * T(n)) * perc(n, 0.001, 0.01) * 4) / 4
    else:  # downward zip
        s = sweep(5000, 500, 0.045, "square") * perc(ns(0.045), 0.001, 0.015)
    return endfade(nrm(s), 16)


# ================================================================ song engine
def reverb_circ(x, rt=1.6, lpf=3500.0, pre=0.02):
    n = len(x)
    L = ns(rt * 1.4)
    t = T(L)
    ir = lp(noise(L), lpf) * np.exp(-t * 6.9 / rt)
    ir[:ns(pre)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(np.pad(ir, (0, n - L))), n)


class Song:
    def __init__(s, bpm, bpb, bars, tail=4.0):
        s.beat = 60 / bpm
        s.bpb = bpb
        s.barlen = bpb * s.beat
        s.bars = bars
        s.N = int(round(bars * s.barlen * SR))
        s.L = s.N / SR
        s.tail = ns(tail)
        s.buses = {}

    def bus(s, name):
        if name not in s.buses:
            s.buses[name] = np.zeros(s.N + s.tail)
        return s.buses[name]

    def t(s, bar, beat=0.0):
        return bar * s.barlen + beat * s.beat

    def add(s, bus, t, sig, vol=1.0):
        buf = s.bus(bus)
        i = int(round(t * SR)) % s.N
        m = min(len(sig), len(buf) - i)
        buf[i:i + m] += sig[:m] * vol

    def cont(s, bus, sig, vol=1.0):
        s.bus(bus)[:s.N] += sig * vol

    def cyc(s, f):
        """Snap a frequency so it completes a whole number of cycles per loop (no seam)."""
        return max(1, round(f * s.L)) / s.L

    def time(s):
        return np.arange(s.N) / SR

    def melody(s, bus, start, text, inst, vol=1.0, tr=0, unit_beats=1.0, legato=0.92, grace=None):
        t = start
        for tok in text.split():
            nm, du = tok.split(":")
            du = float(du) * unit_beats * s.beat
            if nm != "r":
                f = hz(nm, tr)
                s.add(bus, t, inst(f, round(du * legato, 4)), vol)
                if grace and du >= grace[0] * s.beat:
                    gf = f * 2 ** (grace[1] / 12)
                    s.add(bus, t - 0.045, inst(gf, 0.04), vol * 0.7)
            t += du
        return t

    def render(s, mixdef, rev=(1.6, 3500.0)):
        out = np.zeros(s.N)
        wet = np.zeros(s.N)
        for name, buf in s.buses.items():
            x = buf[:s.N].copy()
            x[:s.tail] += buf[s.N:]          # wrap the ringing tail onto the loop start
            g, send, fx = mixdef.get(name, (1.0, 0.0, None))
            if fx:
                x = fx(x)
            out += x * g
            wet += x * g * send
        return out + reverb_circ(wet, *rev)


def prog_at(prog, bar, beat, bpb):
    """prog entry may be 'Bb|C' = split bar."""
    parts = prog[bar % len(prog)].split("|")
    return parts[min(len(parts) - 1, int(beat / (bpb / len(parts))))]


def sidechain(s, depth=0.6, rel=0.11):
    tm = s.time() % s.beat
    return 1 - depth * np.minimum(1, tm / 0.004) * np.exp(-tm / rel)


# ================================================================ output
def finish(x, rms_db=-19.5, ceil=0.79, th=0.55):
    """Hit a target RMS (matched to the Stone/Bronze loops), soft-knee limit above th, hard ceiling ~-2 dBFS."""
    x = x - x.mean()
    target = 10 ** (rms_db / 20)
    g = target / np.sqrt(np.mean(x ** 2))
    for _ in range(4):
        y = x * g
        a = np.abs(y)
        o = a > th
        y[o] = np.sign(y[o]) * (th + (ceil - th) * np.tanh((a[o] - th) / (ceil - th)))
        g *= target / np.sqrt(np.mean(y ** 2))
    return np.clip(y, -ceil, ceil)


def write_wav(path, x):
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def save_music(name, x):
    y = finish(x)
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "m.wav")
        write_wav(tmp, y)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "4",
                        os.path.join(OUT, name + ".ogg")], check=True)
    print(f"{name:20s} {len(y) / SR:6.2f}s  rms {20 * np.log10(np.sqrt(np.mean(y ** 2))):.1f} dBFS  peak {20 * np.log10(np.max(np.abs(y))):.1f} dBFS")


def save_sfx(name, x, peak=0.5):
    """Same normalization as gen_audio.py save(): soft-saturate to a fixed peak."""
    x = np.asarray(x, dtype=np.float64)
    fade = min(len(x), ns(0.004))
    x[-fade:] *= np.linspace(1, 0, fade)
    m = np.max(np.abs(x)) or 1
    x = np.tanh(x / m * 1.2) / np.tanh(1.2) * min(peak, 0.85)
    write_wav(os.path.join(OUT, name + ".wav"), x)
    print(f"{name:20s} {len(x) / SR:6.2f}s")


# ================================================================ MUSIC
def music_iron():
    """Celtic jig in 6/8 (unit = eighth note), D Mixolydian: bodhran, drones, pipe lead, harp strums."""
    s = Song(bpm=300, bpb=6, bars=40)            # dotted quarter = 100 bpm, 48 s
    tt = s.time()
    drone = sum(a * additive(2 * np.pi * s.cyc(hz(nm)) * tt, hz(nm), (1, .5, .35, .25, .2, .15, .1))
                for nm, a in (("D2", 1.0), ("A2", 0.7), ("D3", 0.45)))
    drone *= 0.8 + 0.2 * np.sin(2 * np.pi * tt * 5 / s.L)
    s.cont("drone", drone / np.max(np.abs(drone)))
    prog = ["D", "D", "C", "C", "D", "G", "C", "D"]
    for b in range(s.bars):
        fancy = b % 4 == 3 or 20 <= b < 24
        for e, (kind, vol) in enumerate([("low", 1.0), ("tip", .45), ("tip", .5), ("mid", .8), ("tip", .45), ("tip", .55)]):
            snd = {"low": skin(105.0, 66.0, 0.16, 0.5, 900.0, b % 3), "mid": skin(140.0, 100.0, 0.1, 0.5, 1200.0, b % 3),
                   "tip": skin(190.0, 160.0, 0.045, 0.8, 2200.0, e % 3)}[kind]
            s.add("drums", s.t(b, e), snd, vol)
        if fancy:   # triplet-ish roll into the next bar
            s.add("drums", s.t(b, 5.5), skin(190.0, 160.0, 0.045, 0.8, 2200.0, 1), 0.4)
            s.add("drums", s.t(b, 4.5), skin(190.0, 160.0, 0.045, 0.8, 2200.0, 2), 0.35)
        if b >= 2:   # harp strums on the two dotted-quarter beats
            ch = chord(prog[b % 8], 3)
            notes = [ch[0] - 12, ch[0], ch[1], ch[2]]
            for e in (0, 3):
                for i, m in enumerate(notes if e == 0 else notes[1:]):
                    s.add("harp", s.t(b, e) + i * 0.014, harp(mhz(m), 1.2), 0.55 if e == 0 else 0.4)
    A = ("A4:2 F#4:1 A4:2 D5:1 F#5:2 E5:1 D5:2 B4:1 C5:2 B4:1 C5:2 E5:1 G5:2 E5:1 D5:1 C5:1 B4:1 "
         "A4:2 F#4:1 A4:2 D5:1 B4:2 G4:1 B4:2 D5:1 C5:1 D5:1 E5:1 G5:2 E5:1 D5:5 r:1")
    B = ("D5:2 F#5:1 A5:2 F#5:1 G5:2 F#5:1 E5:2 D5:1 C5:2 E5:1 G5:2 E5:1 C5:2 B4:1 A4:2 G4:1 "
         "F#4:2 A4:1 D5:2 F#5:1 G5:2 B5:1 A5:2 G5:1 E5:1 F#5:1 G5:1 E5:2 C5:1 D5:5 r:1")
    for start, low in ((4, False), (24, True)):
        s.melody("lead", s.t(start), A + " " + B, pipe, 1.0, grace=(2, 4))
        if low:
            s.melody("lead", s.t(start), A + " " + B, pipe, 0.35, tr=-12)
    return s.render({"drone": (0.16, 0.1, lambda x: lp(x, 900, pad=False)), "drums": (0.8, 0.12, None),
                     "harp": (0.32, 0.35, None), "lead": (0.38, 0.3, lambda x: lp(x, 4000, pad=False))}, rev=(1.4, 3000.0))


def music_classical():
    """Stately 3/4 in D Dorian: lyre arpeggios, aulos lead with drone pipe, frame drum, finger cymbals."""
    s = Song(bpm=100, bpb=3, bars=28)            # 50.4 s
    P = ["Dm", "G", "Dm", "C", "Dm", "G", "C", "Dm"]
    prog = ["Dm", "G", "Dm", "C"] + P + P + P
    for b in range(s.bars):
        ch = chord(prog[b], 3)
        tones = [ch[0], ch[2], ch[0] + 12, ch[1] + 12]
        for e, ix in enumerate([0, 1, 2, 3, 2, 1]):
            s.add("lyre", s.t(b, e * 0.5), lyre(mhz(tones[ix]), 1.4), 0.75 if e == 0 else 0.5)
        s.add("drums", s.t(b, 0), skin(90.0, 60.0, 0.2, 0.45, 1000.0, b % 3), 1.0)
        s.add("drums", s.t(b, 1), skin(160.0, 130.0, 0.06, 0.7, 2000.0, 0), 0.4)
        s.add("drums", s.t(b, 2), skin(160.0, 130.0, 0.06, 0.7, 2000.0, 1), 0.45)
        if b % 4 == 3:
            s.add("drums", s.t(b, 2.5), skin(160.0, 130.0, 0.06, 0.7, 2000.0, 2), 0.35)
        if b >= 4 and b % 2 == 1:
            s.add("bells", s.t(b, 2), metal(2600.0, 0.6, 0), 1.0)
    A = "D5:1 F5:1 A5:1 B5:2 A5:.5 G5:.5 A5:1.5 F5:.5 D5:1 E5:1 G5:1 E5:1 F5:1 E5:.5 D5:.5 F5:1 G5:1.5 A5:.5 B5:1 C6:1 B5:.5 A5:.5 G5:1 A5:3"
    B = "A5:1 G5:.5 F5:.5 E5:1 D5:1 B4:1 D5:1 F5:1.5 E5:.5 D5:1 C5:1 E5:1 G5:1 A5:1 F5:1 D5:1 B4:1 D5:1 G5:1 E5:1.5 D5:.5 C5:1 D5:3"
    s.melody("lead", s.t(4), A + " " + B, aulos, 1.0, tr=-12)
    for blk in range(4, 20, 4):     # second aulos pipe drones the tonic
        s.add("lead", s.t(blk), aulos(hz("D4"), round(4 * s.barlen - 0.1, 3)), 0.22)
    s.melody("lyre2", s.t(20), A, lambda f, d: lyre(f, 1.6), 1.0)   # lyre takes the tune
    return s.render({"lyre": (0.24, 0.35, None), "lyre2": (0.36, 0.4, None), "drums": (0.6, 0.15, None),
                     "bells": (0.15, 0.5, None), "lead": (0.6, 0.3, lambda x: lp(x, 3500, pad=False))}, rev=(1.9, 3200.0))


def music_medieval():
    """Heroic march in G: tabor, lute arpeggios + bass, recorder lead."""
    s = Song(bpm=112, bpb=4, bars=24)            # 51.4 s
    A_ = ["G", "C", "G", "D", "Em", "C", "D", "G"]
    B_ = ["Em", "C", "G", "D", "C", "G", "D", "G"]
    prog = ["G", "C", "D", "G"] + A_ + B_ + ["G", "C", "D", "D"]
    for b in range(s.bars):
        roll = b % 4 == 3
        hits = [(0, 1.0), (1, .45), (2, .85), (3, .45), (3.5, .4)] if not roll else \
               [(0, 1.0), (1, .45), (2, .85), (3, .5), (3.25, .4), (3.5, .45), (3.75, .55)]
        for k, (bt, v) in enumerate(hits):
            s.add("drums", s.t(b, bt), tabor(v > 0.7, k % 3), v)
        s.add("drums", s.t(b, 0), skin(80.0, 52.0, 0.22, 0.3, 700.0, b % 3), 0.9)
        s.add("drums", s.t(b, 2), skin(80.0, 52.0, 0.22, 0.3, 700.0, (b + 1) % 3), 0.7)
        ch = chord(prog[b], 3)
        tones = [ch[0], ch[2], ch[0] + 12, ch[1] + 12]
        for e, ix in enumerate([0, 1, 2, 3, 2, 1, 2, 1]):
            s.add("lute", s.t(b, e * 0.5), lute(mhz(tones[ix]), 0.9), 0.7 if e % 2 == 0 else 0.5)
        s.add("lute", s.t(b, 0), lute(mhz(ch[0] - 12), 1.4), 0.8)
        s.add("lute", s.t(b, 2), lute(mhz(ch[2] - 12), 1.2), 0.6)
    A = ("G4:1 B4:1 D5:1.5 B4:.5 C5:1 E5:1 G5:2 D5:1 B4:.5 C5:.5 D5:1 G5:1 F#5:1.5 E5:.5 D5:2 "
         "E5:1 G5:1 B5:1 G5:1 A5:1 G5:1 E5:2 D5:1 E5:.5 F#5:.5 A5:1 F#5:1 G5:3 r:1")
    B = ("B4:1 E5:1 G5:1.5 F#5:.5 E5:1 C5:1 G4:2 B4:1 D5:1 G5:1.5 D5:.5 A5:2 F#5:1 D5:1 "
         "E5:1.5 F#5:.5 G5:1 E5:1 D5:1 B4:1 G4:2 A4:1 B4:.5 C5:.5 D5:1 F#5:1 G5:3 r:1")
    s.melody("lead", s.t(4), A + " " + B, recorder, 1.0)
    return s.render({"drums": (0.55, 0.15, None), "lute": (0.38, 0.3, None),
                     "lead": (0.36, 0.35, lambda x: lp(x, 4500, pad=False))}, rev=(1.5, 3200.0))


def music_gunpowder():
    """Sea-shanty march in 6/8 (unit = eighth), D minor: snare + bass drum, fife lead, squeezebox stabs, plucked bass."""
    s = Song(bpm=324, bpb=6, bars=40)            # dotted quarter = 108 bpm, 44.4 s
    A_ = ["Dm", "Dm", "C", "C", "Dm", "Dm", "A", "Dm"]
    B_ = ["Dm", "C", "Bb", "A", "Dm", "C", "A", "Dm"]
    prog = ["Dm", "C", "A", "Dm"] + A_ + B_ + ["Dm", "C", "A", "A"] + A_ + B_
    for b in range(s.bars):
        roll = b % 4 == 3 or 20 <= b < 24
        for e, v in enumerate([1.0, .4, .5, .85, .4, .5]):
            if roll and e >= 3:
                continue
            s.add("snare", s.t(b, e), snare(230.0, 0.07 if v > 0.8 else 0.035, 1.0, 1800.0, e % 3), v if v > 0.8 else 0.6 * v)
            if v > 0.8:   # flam
                s.add("snare", s.t(b, e) - 0.025, snare(230.0, 0.08, 1.0, 1500.0, 2), 0.35)
        if roll:          # buzz roll crescendo
            for k in range(12):
                s.add("snare", s.t(b, 3 + k * 0.25), snare(230.0, 0.035, 1.0, 1800.0, k % 3), 0.2 + 0.035 * k)
        s.add("drums", s.t(b, 0), kick(110.0, 50.0, 0.25, 0.2, 0.03, 0), 1.0)
        s.add("drums", s.t(b, 3), kick(110.0, 50.0, 0.25, 0.2, 0.03, 1), 0.8)
        ch = chord(prog[b], 3)
        s.add("bass", s.t(b, 0), pluck(mhz(ch[0] - 12), 0.5, 0.2, 0.4, 0.3), 1.0)
        s.add("bass", s.t(b, 3), pluck(mhz(ch[2] - 12), 0.5, 0.2, 0.4, 0.3), 0.85)
        if b >= 2:
            for e in (2, 5):
                stab = sum(wind(mhz(m + 12), 0.14, (1, .6, .5, .4, .3, .2, .15), vib=0.0, a=0.008, r=0.04, breath=0.0, detune=0.004)
                           for m in ch)
                s.add("box", s.t(b, e), stab, 0.8 if e == 2 else 0.65)
    A = ("A4:2 D5:1 D5:2 E5:1 F5:2 E5:1 D5:2 A4:1 C5:2 E5:1 G5:2 E5:1 C5:2 D5:1 E5:3 "
         "F5:2 G5:1 A5:2 F5:1 D5:2 E5:1 F5:2 D5:1 E5:2 C#5:1 A4:2 E5:1 D5:5 r:1")
    B = ("A5:2 A5:1 F5:2 D5:1 G5:2 G5:1 E5:2 C5:1 F5:2 F5:1 D5:2 Bb4:1 C#5:2 E5:1 A5:3 "
         "A5:2 G5:1 F5:2 E5:1 G5:2 F5:1 E5:2 C5:1 E5:1 F5:1 E5:1 C#5:2 A4:1 D5:5 r:1")
    for start, dbl in ((4, False), (24, True)):
        s.melody("lead", s.t(start), A + " " + B, fife, 1.0, tr=12, grace=(3, 2))
        if dbl:
            s.melody("lead", s.t(start), A + " " + B, fife, 0.45)
    return s.render({"snare": (0.9, 0.15, None), "drums": (0.4, 0.1, None), "bass": (0.4, 0.1, None),
                     "box": (0.25, 0.25, lambda x: lp(x, 2500, pad=False)),
                     "lead": (0.3, 0.3, lambda x: lp(x, 5000, pad=False))}, rev=(1.3, 3500.0))


def steam_whistle(d=1.1):
    n = ns(d + 0.3)
    t = T(n)
    out = np.zeros(n)
    for nm, dt in (("F5", 0.0), ("A5", 0.003), ("C6", -0.002)):
        f = hz(nm) * (1 + dt)
        ph = phase(f, n, 0.003, 7.0, scoop=0.08)
        out += np.sin(ph) + 0.15 * np.sin(2 * ph)
    out = nrm(out) + unit(bp(noise(n), 900, 4000)) * 0.35
    return endfade(out * adsr(n, d, 0.05, 0.3, 0.75, 0.08))


def music_industrial():
    """Steampunk oompah in F: tuba + brass stabs, rhythmic clanks and chuffs, brass lead, steam whistle."""
    s = Song(bpm=120, bpb=4, bars=24)            # 48 s
    A_ = ["F", "F", "Bb", "F", "C", "F", "Bb|C", "F"]
    B_ = ["Dm", "Bb", "F", "C", "Dm", "Bb", "C", "F"]
    prog = ["F", "F", "C", "C"] + A_ + B_ + ["F", "Bb", "C", "C"]
    for b in range(s.bars):
        for bt in (0, 2):
            ch = chord(prog_at(prog, b, bt, 4), 2)
            s.add("tuba", s.t(b, bt), tuba(mhz(ch[0] if bt == 0 else ch[2] - 12), 0.32), 1.0 if bt == 0 else 0.85)
            s.add("drums", s.t(b, bt), kick(90.0, 45.0, 0.22, 0.1, 0.03, bt // 2), 0.8)
        for bt in (1, 3):
            ch = chord(prog_at(prog, b, bt, 4), 3)
            for m in (ch[1], ch[2], ch[0] + 12):
                s.add("pah", s.t(b, bt), brass(mhz(m), 0.13, 0.01, 0.05, 10, 0.7, 0.0, 0.6), 0.5)
            s.add("drums", s.t(b, bt), snare(220.0, 0.07, 0.7, 2500.0, bt % 3), 0.35)
        for k, bt in enumerate((0.5, 1.5, 2.5, 3.5)):
            s.add("clank", s.t(b, bt), metal(1150.0 if k % 2 == 0 else 760.0, 0.25, k % 2), 0.8 if k % 2 == 0 else 0.6)
        if b % 2 == 1:
            s.add("clank", s.t(b, 3.75), metal(1600.0, 0.4, 2), 0.6)
        for k in range(16):   # locomotive chuff, accent on beats
            s.add("chuff", s.t(b, k * 0.25), chuff(k % 3), 1.0 if k % 4 == 0 else 0.45)
    for b in (0, 20):
        s.add("whistle", s.t(b), steam_whistle(1.1), 1.0)
    A = ("C5:1 F5:1 A5:1 F5:1 G5:.5 A5:.5 G5:1 F5:2 D5:1 F5:1 Bb5:1.5 A5:.5 A5:1 G5:1 F5:2 "
         "E5:1 G5:1 C6:1.5 Bb5:.5 A5:1 F5:1 C5:2 D5:1 F5:1 E5:1 G5:1 F5:3 r:1")
    B = ("A5:1.5 A5:.5 F5:1 D5:1 Bb5:1.5 A5:.5 G5:1 F5:1 C5:1 F5:.5 G5:.5 A5:1 C6:1 Bb5:1 A5:1 G5:2 "
         "F5:1 E5:.5 F5:.5 A5:1 D5:1 D5:1 F5:1 Bb5:2 A5:1 G5:1 E5:1 C5:1 F5:3 r:1")
    s.melody("lead", s.t(4), A + " " + B, lambda f, d: brass(f, d, 0.035, 0.08, 14, 1.0, 0.005, 0.8), 1.0, tr=-12, legato=0.88)
    return s.render({"tuba": (0.5, 0.05, lambda x: lp(x, 1500, pad=False)), "drums": (0.5, 0.1, None),
                     "pah": (0.28, 0.2, lambda x: lp(x, 2500, pad=False)), "clank": (0.25, 0.3, None),
                     "chuff": (0.1, 0.1, None), "whistle": (0.16, 0.4, None),
                     "lead": (0.36, 0.25, lambda x: lp(x, 3500, pad=False))}, rev=(1.5, 3000.0))


def music_modern():
    """Action-movie drive in E minor: 8th-note synth bass, punchy drums, distorted power-chord pads, synth-brass lead."""
    s = Song(bpm=128, bpb=4, bars=28)            # 52.5 s
    P = ["Em", "C", "G", "D", "Em", "C", "Am", "B"]
    prog = P * 4
    for b in range(s.bars):
        sec = 0 if b < 4 else 1 if b < 12 else 2 if b < 16 else 3
        ch = chord(prog[b], 2)
        for e in range(8):
            up = (b % 4 == 3 and e >= 6)
            if sec == 2 and e % 4:
                continue
            m = ch[0] + 12 * up
            s.add("bass", s.t(b, e * 0.5),
                  synth(mhz(m), 0.2 if sec != 2 else 0.9, "saw", 220.0, 1600.0, 0.06, 0.0, 0.003, 0.12, 0.6, 0.04), 1.0 if e % 2 == 0 else 0.8)
        if sec != 2:
            for bt in ((0, 1.5, 2, 2.75) if sec else (0, 2)):
                s.add("drums", s.t(b, bt), kick(170.0, 50.0, 0.22, 0.5, 0.03, 0), 1.0)
            if sec or b >= 2:
                for bt in (1, 3):
                    s.add("drums", s.t(b, bt), snare(200.0, 0.13, 1.0, 1300.0, bt % 3), 0.75)
            for e in range(8):
                s.add("hats", s.t(b, e * 0.5), hat(0.02, 6000.0, 0.5, e % 3), 0.7 if e % 2 else 0.45)
        else:
            for bt in (0, 2):
                s.add("drums", s.t(b, bt), skin(120.0, 75.0, 0.25, 0.3, 1200.0, bt // 2), 0.9)
        if b in (11, 15, 23):
            for k, f in enumerate((220.0, 180.0, 150.0, 120.0)):
                s.add("drums", s.t(b, 3 + k * 0.25), skin(f, f * 0.65, 0.16, 0.3, 1500.0, k % 3), 0.7)
        if b in (4, 12, 16, 24):
            s.add("hats", s.t(b), crash(1.8, 0), 0.8)
        if sec >= 1:
            pc = chord(re.match(r"[A-G][#b]?", prog[b])[0] + "5", 3)
            if sec == 2:
                hits = [(0, 4.0)]
            else:
                hits = [(0, 1.4), (1.5, 0.4), (2, 1.9)]
            for bt, du in hits:
                for m in pc:
                    s.add("power", s.t(b, bt), synth(mhz(m), round(du * s.beat, 3), "saw", 3000.0, 0.0, 0.08, 0.004, 0.006, 0.3, 0.75, 0.08), 0.6)
    L = ("E5:1.5 B4:.5 E5:1 G5:1 G5:1.5 F#5:.5 E5:2 D5:1.5 B4:.5 D5:1 G5:1 F#5:3 r:1 "
         "E5:1.5 B4:.5 E5:1 G5:1 C6:1.5 B5:.5 G5:2 A5:1.5 G5:.5 E5:1 C5:1 D#5:2 F#5:2")
    lead = lambda f, d: synth(f, d, "saw", 2400.0, 0.0, 0.08, 0.006, 0.03, 0.2, 0.8, 0.1, 0.005)
    s.melody("lead", s.t(16), L, lead, 1.0, tr=-12)
    s.melody("lead", s.t(24), " ".join(L.split()[:8]), lead, 1.0, tr=-12)
    return s.render({"bass": (0.45, 0.0, lambda x: lp(x, 2500, pad=False)), "drums": (0.75, 0.08, None),
                     "hats": (0.3, 0.1, None),
                     "power": (0.17, 0.2, lambda x: lp(np.tanh(x * 3.0), 2800, pad=False)),
                     "lead": (0.5, 0.3, None)}, rev=(1.3, 4000.0))


def music_digital():
    """Electro in A minor: 16th arps, side-chained pads, 909-style drums, offbeat bass, square lead."""
    s = Song(bpm=124, bpb=4, bars=28)            # 54.2 s
    prog = ["Am", "F", "C", "G"] * 7
    for b in range(s.bars):
        sec = 0 if b < 4 else 1 if b < 12 else 2 if b < 16 else 3
        ch = chord(prog[b], 4)
        notes = [ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12, ch[0] + 12, ch[2], ch[1]]
        for k in range(16):
            s.add("arp", s.t(b, k * 0.25), synth(mhz(notes[k % 8]), 0.1, "square", 700.0, 3000.0, 0.05, 0.0, 0.002, 0.08, 0.3, 0.05),
                  0.85 if k % 4 == 0 else 0.6)
        pad = chord(prog[b], 3)
        for m in pad + [pad[0] + 12]:
            s.add("pad", s.t(b), synth(mhz(m), round(s.barlen, 3), "saw", 1700.0, 0.0, 0.08, 0.005, 0.04, 0.3, 0.85, 0.25), 0.5)
        if sec in (1, 3):
            for bt in range(4):
                s.add("drums", s.t(b, bt), kick(160.0, 46.0, 0.3, 0.5, 0.025, 0), 1.0)
            for bt in (1, 3):
                s.add("drums", s.t(b, bt), clap(bt // 2), 0.6)
            for e in range(4):
                s.add("bass", s.t(b, e + 0.5), synth(mhz(chord(prog[b], 2)[0]), 0.2, "saw", 300.0, 1200.0, 0.05, 0.0, 0.003, 0.1, 0.6, 0.03), 1.0)
            s.add("hats", s.t(b, 3.5), hat(0.12, 6500.0, 0.6, 1), 0.6)
        for e in range(8 if sec != 3 else 16):
            step = 0.5 if sec != 3 else 0.25
            if sec == 3 or e % 2 == 1:
                s.add("hats", s.t(b, e * step), hat(0.018, 7000.0, 0.4, e % 3), 0.7 if (e * step) % 1 else 0.35)
        if b == 15:   # riser into the drop
            n = ns(s.barlen)
            r = stft_filter(noise(n), band(lambda t: 500 * 16 ** np.clip(t / s.barlen, 0, 1), 0.5)) * np.linspace(0, 1, n) ** 2
            s.add("fx", s.t(b), endfade(nrm(r)), 1.0)
        if b in (4, 16):
            s.add("hats", s.t(b), crash(1.6, 0), 0.6)
    L = "E5:1.5 C5:.5 r:.5 E5:.5 A5:1 A5:1.5 G5:.5 F5:1 E5:1 G5:1.5 E5:.5 r:.5 G5:.5 C6:1 B5:1.5 A5:.5 G5:1 D5:1"
    L3 = L.replace("B5:1.5 A5:.5 G5:1 D5:1", "B5:1 G5:1 E5:1 G5:1")
    lead = lambda f, d: synth(f, d, "square", 2600.0, 1500.0, 0.1, 0.004, 0.005, 0.15, 0.6, 0.07, 0.004)
    for rep, txt in enumerate((L, L, L3)):
        s.melody("lead", s.t(16 + 4 * rep), txt, lead, 1.0, legato=0.85)
    sc = sidechain(s, 0.65, 0.12)
    return s.render({"arp": (0.17, 0.35, None), "pad": (0.2, 0.3, lambda x: lp(x, 2500, pad=False) * sc),
                     "drums": (0.7, 0.05, None), "bass": (0.4, 0.0, lambda x: x * (0.4 + 0.6 * sc)),
                     "hats": (0.25, 0.1, None), "fx": (0.3, 0.4, None), "lead": (0.3, 0.35, None)}, rev=(1.7, 4500.0))


def music_datacenter():
    """Final era, C minor/phrygian: dark pulsing 16th bass whose filter opens over the loop, glitch percussion,
    tremolo strings, risers, and a climax with full drums + lead before a power-down back to the start."""
    s = Song(bpm=120, bpb=4, bars=28)            # 56 s
    prog = ["Cm", "Ab", "Db", "G"] * 7
    grng = np.random.default_rng(404)
    for b in range(s.bars):
        sec = 0 if b < 8 else 1 if b < 16 else 2 if b < 24 else 3
        ch = chord(prog[b], 2)
        root = ch[0] if ch[0] <= midi("G2") else ch[0] - 12
        base = (280.0, 500.0, 850.0, 1300.0)[sec] + 25.0 * (b % 8)
        for k in range(16):
            if b == s.bars - 1 and k >= 8:
                break
            m = root + (12 if k % 8 == 6 else 0)
            s.add("pulse", s.t(b, k * 0.25), synth(mhz(m), 0.11, "saw", round(base, 0), round(base * 2.5, 0), 0.04, 0.0, 0.002, 0.08, 0.5, 0.03),
                  1.0 if k % 4 == 0 else 0.7)
        for m in chord(prog[b], 3):
            s.add("pad", s.t(b), synth(mhz(m), round(s.barlen, 3), "saw", 900.0, 0.0, 0.08, 0.006, 0.4, 0.4, 0.9, 0.5), 0.5)
        if sec >= 1:   # tremolo strings on the chord fifth (8 Hz = 16ths)
            f5 = mhz(chord(prog[b], 5)[2] - 12)
            n = ns(s.barlen + 0.2)
            tr = additive(phase(f5, n, 0.004, 5.0), f5, (1, .4, .25, .15)) * (0.55 + 0.45 * np.sin(2 * np.pi * 8 * T(n)) ** 2)
            s.add("strings", s.t(b), endfade(nrm(tr) * adsr(n, s.barlen, 0.15, 0.2, 0.9, 0.06)), 0.8 if sec < 3 else 1.0)
        # glitch percussion, denser as the track builds
        p = (0.12, 0.2, 0.28, 0.35)[sec]
        for k in range(16):
            if grng.random() < p and not (b == s.bars - 1 and k >= 8):
                s.add("glitch", s.t(b, k * 0.25), glitch(int(grng.integers(0, 5))), float(grng.uniform(0.4, 1.0)))
        last = b == s.bars - 1
        if sec == 1:
            for bt in (0, 2):
                s.add("drums", s.t(b, bt), kick(140.0, 42.0, 0.35, 0.4, 0.03, 0), 1.0)
        elif sec >= 2:
            for bt in range(2 if last else 4):
                s.add("drums", s.t(b, bt), kick(150.0, 42.0, 0.32, 0.5, 0.03, 0), 1.0)
            for bt in ((1,) if last else (1, 3)):
                s.add("drums", s.t(b, bt), clap(bt // 2), 0.55)
                s.add("drums", s.t(b, bt), snare(180.0, 0.1, 0.8, 1500.0, 0), 0.4)
            for e in range(8 if sec == 2 else 16):
                st = 0.5 if sec == 2 else 0.25
                if last and e * st >= 2:
                    break
                if sec == 3 or e % 2:
                    s.add("hats", s.t(b, e * st), hat(0.015, 7000.0, 0.5, e % 3), 0.7 if (e * st) % 1 else 0.4)
        if b in (15, 23):   # risers
            n = ns(s.barlen)
            r = stft_filter(noise(n), band(lambda t: 400 * 20 ** np.clip(t / s.barlen, 0, 1), 0.45)) * np.linspace(0, 1, n) ** 2
            s.add("fx", s.t(b), endfade(nrm(r)), 1.0)
        if b in (16, 24):
            s.add("hats", s.t(b), crash(2.0, 0), 0.7)
    # power-down sweep on the last half bar, so the loop resets to the sparse intro on purpose
    n = ns(2 * s.beat + 0.3)
    pd = sweep(320, 30, 2 * s.beat + 0.3, "saw") * np.linspace(1, 0, n) ** 1.5
    s.add("fx", s.t(s.bars - 1, 2), endfade(lp(pd, 1500)), 0.8)
    L = "G5:1.5 Ab5:.5 G5:1 Eb5:1 C5:1.5 Eb5:.5 Ab5:2 F5:1.5 Ab5:.5 Db6:1 C6:1 B5:2 G5:1 D5:1"
    lead = lambda f, d: synth(f, d, "square", 2200.0, 0.0, 0.08, 0.005, 0.01, 0.2, 0.75, 0.1, 0.006)
    for rep in range(2):
        s.melody("lead", s.t(16 + 4 * rep), L, lead, 0.85, tr=-12)
    s.melody("lead", s.t(24), L, lead, 0.7)
    s.melody("lead", s.t(24), L, lead, 0.8, tr=-12)
    return s.render({"pulse": (0.42, 0.05, lambda x: lp(x, 3000, pad=False)), "pad": (0.17, 0.45, None),
                     "strings": (0.07, 0.4, None), "glitch": (0.3, 0.25, None), "drums": (0.7, 0.06, None),
                     "hats": (0.25, 0.1, None), "fx": (0.3, 0.5, None), "lead": (0.25, 0.35, None)}, rev=(2.2, 3500.0))


MUSIC = {"music_iron": music_iron, "music_classical": music_classical, "music_medieval": music_medieval,
         "music_gunpowder": music_gunpowder, "music_industrial": music_industrial, "music_modern": music_modern,
         "music_digital": music_digital, "music_datacenter": music_datacenter}


# ================================================================ SFX
def whoosh(d, fc_of_t, width=0.6, shape=2.0, peak_at=0.5):
    n = ns(d)
    t = T(n) / d
    amp = np.where(t < peak_at, t / peak_at, (1 - t) / (1 - peak_at)) ** shape
    return stft_filter(noise(n), band(fc_of_t, width)) * amp


def make_sfx():
    S = save_sfx
    # --- bolt: crossbow / ballista string twang + wooden thunk + short whoosh
    if want("bolt"):
        twang = pluck(98.0, 0.3, 0.08, 0.8, 0.07)
        S("bolt", mix(twang * 0.6, thud(190, 0.14, 0.5) * 0.9,
                      at(lp(noise(ns(0.05)), 2500) * perc(ns(0.05), 0.001, 0.008) * 0.5, 0.0),
                      at(whoosh(0.18, lambda t: np.maximum(400, 2500 - 6000 * t), 0.7) * 0.5, 0.03)), 0.45)
    if want("javelin"):
        S("javelin", mix(whoosh(0.42, lambda t: 2200 * 0.35 ** np.clip(t / 0.42, 0, 1), 0.5, 1.5, 0.4),
                         lp(noise(ns(0.42)), 300) * np.sin(np.linspace(0, np.pi, ns(0.42))) ** 2 * 0.2), 0.4)
    if want("musket"):
        pfft = hp(noise(ns(0.05)), 1500) * perc(ns(0.05), 0.003, 0.012) * 0.35
        crack = hp(noise(ns(0.08)), 900) * perc(ns(0.08), 0.0005, 0.012)
        smoke = lp(noise(ns(0.9)), 1100) * np.minimum(1, T(ns(0.9)) / 0.06) * np.exp(-T(ns(0.9)) / 0.22) * 0.3
        S("musket", mix(pfft, at(crack, 0.055), at(thud(95, 0.45, 0.45) * 0.8, 0.055), at(smoke, 0.08)), 0.6)
    if want("rifle"):
        n = ns(0.45)
        S("rifle", mix(hp(noise(ns(0.04)), 1500) * perc(ns(0.04), 0.0003, 0.005),
                       lp(noise(n), 2500) * perc(n, 0.001, 0.035) * 0.6,
                       lp(noise(n), 900) * perc(n, 0.01, 0.12) * 0.25, thud(170, 0.12, 0.6) * 0.5), 0.5)
    if want("cannon"):
        n = ns(1.5)
        S("cannon", mix(hp(noise(ns(0.06)), 700) * perc(ns(0.06), 0.0005, 0.01) * 0.7,
                        lp(noise(n), 320) * perc(n, 0.004, 0.35) * 1.4, thud(70, 1.2, 0.42) * 1.3,
                        lp(noise(n), 110) * perc(n, 0.05, 0.6) * 0.8), 0.8)
    if want("shell"):
        n = ns(0.9)
        debris = mix(*[at(hp(noise(ns(0.02)), 2500) * perc(ns(0.02), 0.001, 0.005) * rng.uniform(0.05, 0.15), rng.uniform(0.12, 0.55))
                       for _ in range(10)])
        S("shell", mix(thud(58, 0.7, 0.55) * 1.3, lp(noise(n), 200) * perc(n, 0.003, 0.25), debris), 0.7)
    if want("missile"):
        d = 1.1
        n = ns(d)
        t = T(n)
        ign = hp(noise(ns(0.09)), 2500) * perc(ns(0.09), 0.001, 0.03) * 0.5
        wsh = stft_filter(noise(n), band(lambda tt: 450 * 5 ** np.clip(tt / 0.5, 0, 1), 0.7)) * np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.25) / 0.3)
        roar = lp(noise(n), 700) * (0.7 + 0.3 * np.sin(2 * np.pi * 31 * t)) * np.minimum(1, t / 0.05) * np.exp(-t / 0.35) * 0.6
        S("missile", mix(ign, wsh, roar), 0.55)
    if want("laser"):
        d = 0.18
        ph = 2 * np.pi * np.cumsum(np.geomspace(1700, 320, ns(d))) / SR
        s = np.sin(ph) + 0.33 * np.sin(3 * ph) + 0.2 * np.sin(5 * ph) + 0.3 * np.sin(2 * ph + 1)
        S("laser", s * perc(ns(d), 0.002, 0.06), 0.28)
    if want("plasma"):
        d = 0.55
        n = ns(d)
        t = T(n)
        f = 270 * (1 - 0.45 * t / d) * (1 + 0.22 * np.sin(2 * np.pi * 14 * t))
        ph = 2 * np.pi * np.cumsum(f) / SR
        body = sum(np.sin(k * ph) / k for k in range(1, 7)) * perc(n, 0.01, 0.17)
        fizz = unit(bp(noise(n), 700, 2600)) * perc(n, 0.005, 0.08) * 0.3
        S("plasma", mix(body, fizz, thud(110, 0.2, 0.5) * 0.5), 0.45)
    if want("zap"):
        d = 0.36
        n = ns(d)
        t = T(n)
        gate = np.repeat(rng.random(n // 22 + 1) < 0.45, 22)[:n].astype(float)
        gate = lp(gate, 2000)
        buzz = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.3 + unit(hp(noise(n), 1800))
        spark = sweep(3200, 1400, d) * 0.2
        S("zap", (buzz * gate + spark) * perc(n, 0.002, 0.11), 0.4)
    if want("flame"):
        d = 0.7
        n = ns(d)
        t = T(n)
        flick = 0.65 + 0.35 * nrm(lp(noise(n), 14))
        roar = unit(lp(noise(n), 1500)) * flick * np.minimum(1, t / 0.07) * np.exp(-np.maximum(0, t - 0.15) / 0.2)
        crackle = mix(*[at(hp(noise(ns(0.004)), 3000) * rng.uniform(0.3, 0.8), rng.uniform(0.02, 0.5)) for _ in range(25)], np.zeros(n))
        S("flame", mix(roar, crackle, unit(lp(noise(n), 220)) * perc(n, 0.03, 0.2) * 0.6), 0.45)
    if want("steam"):
        d = 0.75
        n = ns(d)
        t = T(n)
        hiss = unit(hp(noise(n), 2600)) * np.minimum(1, t / 0.03) * np.exp(-np.maximum(0, t - 0.2) / 0.18) * (0.85 + 0.15 * np.sin(2 * np.pi * 23 * t))
        S("steam", mix(clank(640, 0.3) * 1.2, at(hiss * 0.55, 0.03), unit(lp(noise(ns(0.1)), 600)) * perc(ns(0.1), 0.002, 0.03) * 0.4), 0.45)
    if want("drum"):
        n = ns(0.95)
        S("drum", mix(thud(64, 0.9, 0.62) * 1.4, unit(lp(noise(n), 700)) * perc(n, 0.002, 0.05) * 0.5,
                      np.sin(2 * np.pi * 96 * T(n)) * perc(n, 0.003, 0.18) * 0.4,
                      unit(hp(noise(ns(0.05)), 1200)) * perc(ns(0.05), 0.0005, 0.008) * 0.3), 0.7)
    if want("emp"):
        d = 1.1
        n = ns(d)
        t = T(n)
        down = lp(sweep(1200, 35, d, "square"), 2500) * np.exp(-t / 0.4) * 0.6
        ring = np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t * (1 - 0.6 * t / d))) * perc(n, 0.005, 0.3)
        S("emp", mix(down, ring * 0.7, thud(90, 0.45, 0.5) * 0.9, unit(hp(noise(n), 3000)) * perc(n, 0.001, 0.02) * 0.4), 0.6)
    if want("freeze"):
        d = 0.9
        n = ns(d)
        t = T(n)
        sh = np.zeros(n)
        for _ in range(16):
            f = rng.uniform(2000, 7000)
            o = rng.uniform(0, 0.35)
            sh += np.sin(2 * np.pi * f * t) * (t >= o) * np.exp(-np.maximum(0, t - o) / rng.uniform(0.12, 0.35)) * rng.uniform(0.4, 1)
        swell = unit(hp(noise(n), 4000)) * np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.12) / 0.25) * 0.25
        crk = mix(*[at(hp(noise(ns(0.003)), 4000) * 0.6, rng.uniform(0.0, 0.25)) for _ in range(6)], np.zeros(n))
        S("freeze", mix(sh / 4, swell, crk), 0.35)
    if want("explosion"):
        n = ns(1.3)
        debris = mix(*[at(hp(noise(ns(0.015)), 2000) * rng.uniform(0.05, 0.2), rng.uniform(0.15, 0.8)) for _ in range(14)])
        S("explosion", mix(hp(noise(ns(0.05)), 900) * perc(ns(0.05), 0.0005, 0.01) * 0.8,
                           unit(lp(noise(n), 700)) * perc(n, 0.003, 0.2) * 0.8, unit(lp(noise(n), 200)) * perc(n, 0.01, 0.45) * 0.9,
                           thud(85, 0.9, 0.4) * 1.2, debris), 0.75)
    if want("airstrike"):
        d = 3.2
        n = ns(d)
        t = T(n)
        pas = 0.9
        amp = np.exp(-0.5 * ((t - pas) / 0.42) ** 2)
        jet = stft_filter(noise(n), band(lambda tt: 500 + 2300 / (1 + np.exp((tt - pas) / 0.18)), 0.8)) * amp
        roar = unit(lp(noise(n), 300)) * amp * 0.5
        booms = [at(mix(thud(rng.uniform(55, 80), 0.8, 0.45), unit(lp(noise(ns(0.8)), 400)) * perc(ns(0.8), 0.003, 0.18) * 0.7) * v, o)
                 for o, v in ((1.25, 1.0), (1.5, 0.8), (1.72, 0.9), (2.0, 0.7))]
        rumble = unit(lp(noise(n), 140)) * np.clip((t - 1.2) / 0.05, 0, 1) * np.exp(-np.maximum(0, t - 1.25) / 0.7) * 0.6
        S("airstrike", mix(jet * 1.3, roar, *booms, rumble)[:n], 0.8)
    if want("boss_roar_mech"):
        d = 2.4
        n = ns(d)
        t = T(n)
        e = np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - 1.5) / 0.3)
        core = lp(sweep(115, 42, d, "saw") * (1 + 0.6 * np.sin(2 * np.pi * 28 * t)), 1100)
        grind = sum(np.sin(2 * np.pi * f * (1 + 0.03 * np.sin(2 * np.pi * 9 * t)) * t) * a for f, a in ((310, 1), (857, .6), (1673, .4), (2390, .25)))
        grind *= (0.5 + 0.5 * np.tanh(3 * np.sin(2 * np.pi * 17 * t))) * 0.25
        whine = sweep(380, 950, d) * 0.12
        hiss = unit(hp(noise(n), 2500)) * np.clip((t - 1.55) / 0.08, 0, 1) * np.exp(-np.maximum(0, t - 1.63) / 0.3) * 0.3
        body = np.tanh(core * 3) * 0.8 + grind + whine
        S("boss_roar_mech", mix(body * e, hiss, thud(45, 0.8, 0.6) * 0.8, unit(lp(noise(n), 250)) * e * 0.3), 0.8)
    if want("cloak"):
        d = 0.75
        n = ns(d)
        t = T(n)
        glide = 1 - 0.35 * t / d
        sh = sum(np.sin(2 * np.pi * np.cumsum(np.full(n, f) * glide) / SR + i) for i, f in enumerate((1800, 2410, 3130)))
        sh *= 0.6 + 0.4 * np.sin(2 * np.pi * 22 * t)
        air = unit(hp(noise(n), 3000)) * 0.25
        e = np.minimum(1, t / 0.06) * np.exp(-np.maximum(0, t - 0.1) / 0.18)
        S("cloak", (sh / 3 + air) * e, 0.3)
    if want("swing"):
        d = 0.32
        S("swing", mix(whoosh(d, lambda tt: 450 + 650 * np.sin(np.pi * np.clip(tt / d, 0, 1)), 0.55, 1.6, 0.45),
                       np.sin(2 * np.pi * 110 * T(ns(d))) * np.sin(np.linspace(0, np.pi, ns(d))) ** 3 * 0.25), 0.45)


if __name__ == "__main__":
    make_sfx()
    for name, fn in MUSIC.items():
        if want(name):
            save_music(name, fn())
