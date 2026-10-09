"""Synthesizes every sound effect and the Stone Age music loop from scratch (no samples, no licensing).
Run: python3 gen_audio.py assets/audio"""
import sys, os, wave
import numpy as np

SR = 22050
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)


def t_(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, d=0.2, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) * curve / max(d, 1e-4))
    return e


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def highpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (f / cutoff) ** 4 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def sweep(f0, f1, d, shape="sine"):
    t = t_(d)
    f = np.geomspace(f0, f1, len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == "square":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def save(name, x, peak=0.85):
    x = np.asarray(x, dtype=np.float64)
    fade = min(len(x), int(0.004 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    m = np.max(np.abs(x)) or 1
    x = np.tanh(x / m * 1.2) / np.tanh(1.2) * peak
    data = (x * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())
    print(f"{name:16s} {len(x) / SR:.2f}s")


def thud(f=80, d=0.25, drop=0.5):
    s = sweep(f, f * drop, d) * env(int(SR * d), 0.002, d * 0.5)
    return s


def clank(f=520, d=0.35):
    t = t_(d)
    parts = sum(np.sin(2 * np.pi * f * r * t) * a for r, a in ((1, 1), (2.76, 0.6), (5.4, 0.4), (8.93, 0.25)))
    return parts * env(len(t), 0.001, d * 0.35)


# ---------------------------------------------------------------- SFX
n = noise(0.2)
save("throw", highpass(n, 900) * np.sin(np.linspace(0, np.pi, len(n))) ** 2 * 0.7, 0.45)
save("rock_hit", mix(thud(140, 0.14, 0.6), lowpass(noise(0.05), 2500) * env(int(SR * 0.05), 0.001, 0.02)), 0.5)
save("club", mix(thud(95, 0.22, 0.55) * 1.3, lowpass(noise(0.08), 1800) * env(int(SR * 0.08), 0.001, 0.03) * 0.8), 0.6)
save("catapult", mix(lowpass(sweep(70, 55, 0.3, "saw"), 600) * env(int(SR * 0.3), 0.02, 0.12) * 0.6,
                     highpass(noise(0.35), 700) * np.sin(np.linspace(0, np.pi, int(SR * 0.35))) ** 2 * 0.6), 0.5)
save("boulder_land", mix(thud(60, 0.45, 0.6) * 1.4, lowpass(noise(0.4), 400) * env(int(SR * 0.4), 0.003, 0.15)), 0.7)
t = t_(0.45)
blub = np.sin(2 * np.pi * (140 + 60 * np.sin(2 * np.pi * 9 * t)) * t) * env(len(t), 0.03, 0.2)
save("pulse", mix(blub, lowpass(noise(0.45), 500) * env(len(t), 0.05, 0.15) * 0.5), 0.45)
zap = lowpass(sweep(1400, 160, 0.22, "square"), 3000) * env(int(SR * 0.22), 0.001, 0.08) * 0.35
save("robot_death", mix(clank(560, 0.32) * 0.8, zap, lowpass(noise(0.12), 3000) * env(int(SR * 0.12), 0.001, 0.04) * 0.6), 0.45)
boom = lowpass(noise(1.8), 300) * env(int(SR * 1.8), 0.005, 0.7) * 1.4
save("boss_death", mix(boom, thud(45, 1.2, 0.5) * 1.2, clank(300, 0.9) * 0.6, np.pad(clank(420, 0.6) * 0.4, (int(SR * 0.25), 0))), 0.9)
save("coin", mix(np.sin(2 * np.pi * 1320 * t_(0.06)) * env(int(SR * 0.06), 0.002, 0.03),
                 np.pad(np.sin(2 * np.pi * 1760 * t_(0.1)) * env(int(SR * 0.1), 0.002, 0.05), (int(SR * 0.05), 0))), 0.18)
save("place", mix(thud(220, 0.12, 0.7), clank(900, 0.1) * 0.25, lowpass(noise(0.03), 4000) * 0.4), 0.5)
up = np.concatenate([np.sin(2 * np.pi * f * t_(0.09)) * env(int(SR * 0.09), 0.003, 0.08) for f in (523, 659, 784, 1047)])
save("upgrade", mix(up, np.pad(np.sin(2 * np.pi * 1047 * t_(0.35)) * env(int(SR * 0.35), 0.003, 0.25) * 0.6, (int(SR * 0.27), 0))), 0.4)
# wave horn: breathy low horn with vibrato (Stone Age war horn)
t = t_(1.3)
vib = 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t)
horn = sum(np.sin(2 * np.pi * 110 * k * vib * t) / k ** 1.3 for k in range(1, 9))
horn *= np.minimum(1, t / 0.18) * np.exp(-np.maximum(0, t - 0.9) * 6)
save("wave_horn", mix(lowpass(horn, 1400), lowpass(noise(1.3), 900) * 0.06 * np.minimum(1, t / 0.18)), 0.6)
save("life_lost", lowpass(sweep(220, 140, 0.35, "square"), 1200) * env(int(SR * 0.35), 0.005, 0.2), 0.4)
t = t_(1.6)
roar = lowpass(sweep(95, 48, 1.6, "saw") * (1 + 0.4 * np.sin(2 * np.pi * 23 * t)), 900) * np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - 1.0) * 4)
save("boss_roar", mix(np.tanh(roar * 3) * 0.8, lowpass(noise(1.6), 300) * 0.3 * np.minimum(1, t / 0.2)), 0.8)
t = t_(0.7)
save("summon", np.sin(2 * np.pi * (300 + 250 * np.sin(2 * np.pi * 7 * t)) * t) * env(len(t), 0.05, 0.3) * 0.6, 0.4)
save("click", mix(clank(1800, 0.04) * 0.5, lowpass(noise(0.015), 5000) * 0.3), 0.3)
save("error", lowpass(sweep(180, 170, 0.18, "square"), 900) * env(int(SR * 0.18), 0.003, 0.12), 0.3)


# ---------------------------------------------------------------- jingles
def note(f, d, kind="flute", vol=1.0):
    t = t_(d)
    if kind == "flute":
        v = 1 + 0.006 * np.sin(2 * np.pi * 5 * t)
        s = np.sin(2 * np.pi * f * v * t) + 0.25 * np.sin(4 * np.pi * f * v * t) + 0.08 * np.sin(6 * np.pi * f * v * t)
        s += lowpass(rng.uniform(-1, 1, len(t)), f * 2) * 0.08
        e = np.minimum(1, t / 0.04) * np.exp(-np.maximum(0, t - d * 0.7) * 10)
    else:  # horn
        s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.4 for k in range(1, 7))
        e = np.minimum(1, t / 0.08) * np.exp(-np.maximum(0, t - d * 0.75) * 8)
    return s * e * vol


def drum(f=70, d=0.35, vol=1.0):
    return thud(f, d, 0.55) * vol


def seq(events, total):
    out = np.zeros(int(SR * total) + SR)
    for at, sig in events:
        i = int(at * SR)
        out[i:i + len(sig)] += sig[:len(out) - i]
    return out[:int(SR * total)]


A3, C4, D4, E4, G4, A4, C5, D5, E5 = 220, 261.6, 293.7, 329.6, 392, 440, 523.3, 587.3, 659.3
v = seq([(0, drum(80)), (0.25, drum(80)), (0.5, drum(60, 0.6)), (0.0, note(A4, 0.24, "horn")), (0.25, note(C5, 0.24, "horn")),
         (0.5, note(E5, 1.4, "horn")), (0.5, note(A4, 1.4, "horn", 0.6))], 2.2)
save("victory", v, 0.7)
dft = seq([(0, drum(70, 0.5)), (0.0, note(E4, 0.5, "horn")), (0.5, note(D4, 0.5, "horn")), (1.0, drum(55, 0.9)), (1.0, note(A3, 1.4, "horn"))], 2.6)
save("defeat", dft, 0.7)

# ---------------------------------------------------------------- music loop (tribal drums + drone + bone flute)
BPM = 96
beat = 60 / BPM
bars = 16
total = bars * 4 * beat
ev = []
for b in range(bars):
    t0 = b * 4 * beat
    ev += [(t0, drum(72, 0.5, 0.9)), (t0 + 2 * beat, drum(72, 0.5, 0.8)), (t0 + 1.5 * beat, drum(110, 0.25, 0.45)),
           (t0 + 3.5 * beat, drum(110, 0.25, 0.45)), (t0 + 3.75 * beat, drum(120, 0.2, 0.35))]
    for k in range(8):
        sh = highpass(rng.uniform(-1, 1, int(SR * 0.06)), 5000) * env(int(SR * 0.06), 0.002, 0.025) * (0.16 if k % 2 else 0.24)
        ev.append((t0 + k * beat / 2, sh))
# drone: root + fifth, slow swell
tt = np.arange(int(SR * total)) / SR
drone = lowpass((np.sin(2 * np.pi * 55 * tt) + 0.6 * np.sin(2 * np.pi * 82.4 * tt) + 0.3 * np.sin(2 * np.pi * 110 * tt)), 300)
drone *= 0.22 * (0.75 + 0.25 * np.sin(2 * np.pi * tt / (4 * 4 * beat)))
# flute melody: A minor pentatonic, enters after 4 bars, rests in bars 12-13 for breathing room
phrase = [(A4, 1), (C5, 0.5), (D5, 0.5), (E5, 1.5), (D5, 0.5), (C5, 1), (A4, 1), (G4, 2),
          (A4, 1), (C5, 0.5), (A4, 0.5), (G4, 1), (E4, 1), (G4, 1.5), (A4, 2.5)]
t_cursor = 4 * 4 * beat
for rep in range(2):
    for f, dur in phrase:
        if t_cursor + dur * beat > total - 0.1:
            break
        ev.append((t_cursor, note(f, dur * beat * 0.95, "flute", 0.32)))
        t_cursor += dur * beat
    t_cursor += 2 * 4 * beat
music = seq(ev, total) + drone
save("music_stone_age", music, 0.55)


# ================================================================ v0.4: Bronze Age + heroes
def pluck(f, d, vol=1.0, bright=0.6):
    """Karplus-Strong plucked string (lyre / harp)."""
    n = int(SR * d)
    period = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, period)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % period]
        buf[i % period] = 0.5 * (buf[i % period] + buf[(i + 1) % period]) * (0.994 + 0.004 * bright)
    return out * vol


save("arrow", mix(highpass(noise(0.12), 1500) * env(int(SR * 0.12), 0.002, 0.05) * 0.5,
                  sweep(320, 220, 0.12) * env(int(SR * 0.12), 0.001, 0.05) * 0.6), 0.35)
save("spear", mix(highpass(noise(0.1), 1200) * env(int(SR * 0.1), 0.002, 0.04), clank(1300, 0.12) * 0.4), 0.4)
save("shield_up", mix(sweep(300, 900, 0.3) * env(int(SR * 0.3), 0.02, 0.15) * 0.5,
                      np.sin(2 * np.pi * 1200 * t_(0.3)) * env(int(SR * 0.3), 0.05, 0.1) * 0.2), 0.3)
save("shield_break", mix(highpass(noise(0.25), 2500) * env(int(SR * 0.25), 0.001, 0.08), sweep(1400, 300, 0.25) * env(int(SR * 0.25), 0.001, 0.1) * 0.4), 0.4)
t = t_(0.5)
save("heal", sum(np.sin(2 * np.pi * f * t) * env(len(t), 0.03 + k * 0.05, 0.3) for k, f in enumerate((660, 880, 1100))) * 0.4, 0.25)
lv = np.concatenate([np.sin(2 * np.pi * f * t_(0.1)) * env(int(SR * 0.1), 0.003, 0.09) for f in (392, 523, 659, 784, 1047)])
save("level_up", mix(lv, np.pad(note(1047, 0.6, "flute", 0.7), (int(SR * 0.45), 0))), 0.45)
save("hero_place", mix(thud(120, 0.3, 0.6), np.pad(lv[: int(SR * 0.3)], (int(SR * 0.05), 0)) * 0.6), 0.5)
rumble = lowpass(noise(1.6), 180) * np.minimum(1, t_(1.6) / 0.1) * np.exp(-t_(1.6) * 1.8)
save("ab_stone_rain", mix(rumble * 1.5, *[np.pad(thud(rng.uniform(60, 110), 0.3), (int(SR * k * 0.12), 0)) for k in range(9)]), 0.85)
save("ab_earthquake", mix(lowpass(noise(2.0), 120) * np.minimum(1, t_(2.0) / 0.2) * np.exp(-t_(2.0) * 1.2) * 2, thud(40, 1.6, 0.6)), 0.9)
t = t_(1.2)
flare = np.sin(2 * np.pi * np.cumsum(np.geomspace(200, 1600, len(t))) / SR) * np.minimum(1, t / 0.4) * np.exp(-np.maximum(0, t - 0.5) * 5)
save("ab_solar_flare", mix(flare * 0.6, highpass(noise(1.2), 2000) * np.minimum(1, t / 0.4) * np.exp(-np.maximum(0, t - 0.5) * 5) * 0.5,
                           np.pad(thud(90, 0.6), (int(SR * 0.45), 0))), 0.75)
save("ab_forge_fury", mix(*[np.pad(clank(rng.uniform(600, 900), 0.5) * 0.7, (int(SR * k * 0.16), 0)) for k in range(4)],
                          lowpass(noise(1.0), 900) * env(int(SR * 1.0), 0.1, 0.5) * 0.4), 0.7)
save("boss_roar_bronze", mix(lowpass(sweep(70, 40, 1.8, "square") * (1 + 0.5 * np.sin(2 * np.pi * 12 * t_(1.8))), 700) * np.minimum(1, t_(1.8) / 0.2) * np.exp(-np.maximum(0, t_(1.8) - 1.2) * 4),
                             *[np.pad(clank(250, 0.4) * 0.5, (int(SR * k * 0.35), 0)) for k in range(4)]), 0.8)

# Bronze Age music: frame drum + sistrum + lyre melody in a Hijaz-style scale, with a reed drone
BPM2 = 104
beat2 = 60 / BPM2
bars2 = 16
total2 = bars2 * 4 * beat2
ev2 = []
for b in range(bars2):
    t0 = b * 4 * beat2
    ev2 += [(t0, drum(85, 0.4, 0.8)), (t0 + 1.5 * beat2, drum(140, 0.18, 0.5)), (t0 + 2 * beat2, drum(85, 0.4, 0.7)),
            (t0 + 3 * beat2, drum(140, 0.18, 0.45)), (t0 + 3.5 * beat2, drum(150, 0.15, 0.4))]
    for k in range(8):
        sist = highpass(rng.uniform(-1, 1, int(SR * 0.09)), 6000) * env(int(SR * 0.09), 0.003, 0.04) * (0.14 if k % 2 else 0.22)
        ev2.append((t0 + k * beat2 / 2, sist))
D4b, Eb4, Fs4, G4b, A4b, Bb4, C5b, D5b = 293.7, 311.1, 370.0, 392.0, 440.0, 466.2, 523.3, 587.3
line = [(D4b, 1), (Eb4, 0.5), (Fs4, 0.5), (G4b, 1), (A4b, 1), (Bb4, 0.5), (A4b, 0.5), (G4b, 1), (Fs4, 1), (Eb4, 0.5), (D4b, 1.5),
        (A4b, 1), (Bb4, 0.5), (C5b, 0.5), (D5b, 1.5), (C5b, 0.5), (Bb4, 1), (A4b, 1), (G4b, 0.5), (Fs4, 0.5), (D4b, 2)]
cur = 2 * 4 * beat2
for rep in range(3):
    for f, dur in line:
        if cur + dur * beat2 > total2 - 0.1:
            break
        ev2.append((cur, pluck(f, min(dur * beat2 * 1.6, 1.4), 0.38)))
        ev2.append((cur, pluck(f * 2, min(dur * beat2, 0.8), 0.08, 0.9)))
        cur += dur * beat2
    cur += 4 * beat2
tt2 = np.arange(int(SR * total2)) / SR
drone2 = lowpass(sum(np.sign(np.sin(2 * np.pi * f * tt2)) * a for f, a in ((73.4, 1.0), (110.0, 0.5))), 500) * 0.12
drone2 *= 0.75 + 0.25 * np.sin(2 * np.pi * tt2 / (8 * beat2))
save("music_bronze_age", seq(ev2, total2) + drone2, 0.55)
