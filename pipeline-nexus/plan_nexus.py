#!/usr/bin/env python3
# plan_nexus_ep2.py — generator plan.json NEXUS ZERO Episode 2 "THE FIRST DOUBT".
# Satu baris per frame (f 0..1439). Per frame: rig tiap karakter, intensitas
# lampu, kamera (x,y,z,target,focus,lens,roll Dutch), flag.
# Murni Python (tanpa bpy). Pola: plan_nexus.py Ep 1.
# Set: ruang inti MONUMENTAL (RX=80, 60x48 m, dinding 16 m, wajah ~12 m,
# gerbang 5x6 m di y=23.55) + kota aerial S2 (x~0).
# TIDAK ADA flash putih di Ep 2 (berakhir hitam + end card).
# Flag baru: gate_open (0..1, gerbang terbuka S6-S8), nexus_glitch (S2),
# props scar_glow (S4), laser_eva (S8).
#   python3 plan_nexus_ep2.py [plan.json]
import json
import math
import os
import sys

N = 1440
RX = 80.0   # offset ruang inti NEXUS (sama dengan build_scene_nexus_ep2.py)
ALL_CHARS = ["KAI", "EVA"] + [f"SEN{i}" for i in range(1, 9)] + ["RES1", "RES2", "CIV1", "CIV2"]


def clamp(x, a, b):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def seg_t(f, a, b):
    return clamp((f - a) / max(1, b - a), 0.0, 1.0)


def shake(f, amp, freq=1.7):
    return amp * (math.sin(f * 0.9 * freq) * 0.6 + math.sin(f * 2.3 * freq + 1.3) * 0.4)


def walk_cycle(phase, amp, arm_amp=None):
    if arm_amp is None:
        arm_amp = amp * 0.8
    return {
        "legL": amp * math.sin(phase),
        "legR": -amp * math.sin(phase),
        "armL": -arm_amp * math.sin(phase),
        "armR": arm_amp * math.sin(phase),
        "bob": 0.045 * abs(math.cos(phase)),
    }


def char(x=0, y=0, z=0, rot=0, lean=0, squash=1.0, crouch=0.0, pitch=0.0,
         head_tilt=0, head_turn=0, armL=0, armR=0, legL=0, legR=0,
         eye_red=False, vis=True, mouthW=1.0, mouthH=1.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "rot": round(rot, 2),
            "lean": round(lean, 2), "squash": round(squash, 3), "crouch": round(crouch, 3),
            "pitch": round(pitch, 2), "head_tilt": round(head_tilt, 2),
            "head_turn": round(head_turn, 2), "armL": round(armL, 2), "armR": round(armR, 2),
            "legL": round(legL, 2), "legR": round(legR, 2),
            "eye_red": bool(eye_red), "vis": bool(vis),
            "mouthW": round(mouthW, 2), "mouthH": round(mouthH, 2)}


def hidden():
    return char(vis=False)


def cam(x, y, z, tx, ty, tz, focus, lens, roll=0.0):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
            "tx": round(tx, 3), "ty": round(ty, 3), "tz": round(tz, 3),
            "focus": round(focus, 2), "lens": round(lens, 1),
            "roll": round(roll, 2)}


def lights(siren=0, lamp=300, dusk=60, moon=260, flash=0, hide=0, nexus=120,
           gate=0, rim=0, eye=0, core=0, eva=0, corr=0, neon=150, fill=90):
    return {"siren": round(siren, 1), "lamp": round(lamp, 1), "dusk": round(dusk, 1),
            "moon": round(moon, 1), "flash": round(flash, 1), "hide": round(hide, 1),
            "nexus": round(nexus, 1), "gate": round(gate, 1), "rim": round(rim, 1),
            "eye": round(eye, 1), "core": round(core, 1), "eva": round(eva, 1),
            "corr": round(corr, 1), "neon": round(neon, 1), "fill": round(fill, 1)}


def sentinel_patrol(x, y, f, phase0=0.0, rot=90, speed=0.5):
    """Sentinel: langkah berat kaku, kepala menoleh dengan jeda mekanik."""
    ph = phase0 + f * 0.06 * speed
    step = 14 * math.sin(ph)
    turn = 18 * math.sin(math.floor(f / 20) * 1.1)
    return char(x, y, 0.02 * abs(math.cos(ph)), rot=rot, lean=3,
                head_tilt=2, head_turn=turn,
                armL=6, armR=-6, legL=step, legR=-step, eye_red=True)


def sentinel_frozen(x, y, rot=180):
    """Sentinel MEMBEKU di tengah langkah (S1 Ep 2): satu lutut setengah
    tertekuk, badan condong, sensor menyala (eye_red=True — padam diatur
    lewat lampu eye di plan, bukan di sini)."""
    return char(x, y, 0, rot=rot, lean=6, crouch=0.25, head_tilt=3,
                armL=8, armR=-4, legL=18, legR=-8, eye_red=True)


def ped_walk(x, y, f, phase0, rot, amp=22):
    ph = phase0 + f * 0.11
    c = walk_cycle(ph, amp)
    return char(x, y, c["bob"], rot=rot, lean=4, head_tilt=0, head_turn=0,
                armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])


rows = []
for f in range(N):
    chars = {}
    # core SUDAH terpasang di soket sejak S6 Ep 1; backpack tergeletak di
    # lantai ruang inti sejak S6 Ep 1 — keduanya ada di SEMUA segmen Ep 2.
    props = {"core_in_hand": False, "core_table": False, "core_socket": True,
             "backpack": False, "backpack_dropped": True, "rain": False,
             "gate": False, "scar_glow": False, "laser_eva": False}
    gate_open = 0.0
    nexus_glitch = False
    flash_white = False  # TIDAK ADA flash di Ep 2

    # ================= S1 HOOK (0-71) — "THE SENTINELS DID NOT FIRE." =================
    if f < 72:
        # Kairo terus berjalan ke arah 2 Sentinel (lanjutan S8 Ep 1).
        # Sentinel MEMBEKU membelakangi Kairo (rot 180, menghadap gerbang),
        # sensor merah berkedip lalu PADAM (eye: flicker 0-47, 0 setelah 48).
        t = seg_t(f, 0, 71)
        kai_y = lerp(-1.0, 3.5, smooth(t))
        ph = f * 0.35
        c = walk_cycle(ph, 26)
        chars["KAI"] = char(RX, kai_y, c["bob"], rot=180, lean=8, head_tilt=0,
                            armL=c["armL"], armR=c["armR"], legL=c["legL"], legR=c["legR"])
        chars["SEN1"] = sentinel_frozen(RX - 3, 12)
        chars["SEN2"] = sentinel_frozen(RX + 3, 12)
        # low-angle hero, push-in lambat, Dutch 8 — ruangan monumental terbaca
        chars_cam = cam(RX + 0.6, lerp(-7.0, -5.0, smooth(t)), lerp(1.0, 1.2, smooth(t)),
                        RX, kai_y + 0.6, 1.35, lerp(7.0, 5.5, smooth(t)),
                        lerp(52, 48, t), roll=8)
        if f < 48:
            eye = 600 if (f // 4) % 2 == 0 else 60  # sensor berkedip
        else:
            eye = 0  # sensor PADAM — Sentinel membeku total
        li = lights(moon=80, nexus=1200, rim=600, fill=200, core=150,
                    gate=0, eye=eye, neon=0, lamp=0, dusk=0)
        for _p in ("EVA", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S2 NEXUS GAGAP (72-287) =================
    elif f < 288:
        if f < 144:
            # 2a: tilt-down dari wajah NEXUS ke lantai — wajah GAGAP
            t = seg_t(f, 72, 143)
            nexus_glitch = True
            chars["KAI"] = char(RX, 3.5, 0, rot=180, lean=4, head_tilt=lerp(0, -14, smooth(t)),
                                head_turn=0, armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(RX - 1.0 + shake(f, 0.04), -8.0, 2.0,
                            RX, lerp(23.0, 0.0, smooth(t)), lerp(10.0, 1.0, smooth(t)),
                            lerp(24.0, 9.0, smooth(t)), lerp(45, 50, t))
            # cahaya merah berkedip acak (gagap)
            nex = 1800 if (f // 3) % 2 == 0 else 200
            li = lights(moon=80, nexus=nex, rim=500, fill=200, core=150,
                        gate=0, eye=0, neon=0, lamp=0, dusk=0)
        elif f < 216:
            # 2b: cut aerial kota — 12 menara, 4 layar, grid meredup
            t = seg_t(f, 144, 215)
            nexus_glitch = f < 200  # gagap mereda di akhir 2b
            for i in range(1, 7):
                chars[f"SEN{i}"] = sentinel_patrol(lerp(-9 + i * 3, -6 + i * 3, t), 1.0 + (i % 2),
                                                   f, phase0=i * 2.0, rot=90)
            chars["CIV1"] = ped_walk(lerp(-4, 2, t), 2.5, f, 1.0, rot=90, amp=18)
            chars["CIV2"] = ped_walk(lerp(-2, 4, t), -1.5, f, 3.0, rot=90, amp=18)
            chars_cam = cam(0, lerp(-9, -5.5, smooth(t)), lerp(15, 9.5, smooth(t)),
                            0, 2, 0, 12, 34)  # FIX R2: lensa lebih lebar — layar NEXUS masuk frame
            # layar kota berkedip (nexus flicker) + grid meredup
            nex = 600 if (f // 5) % 2 == 0 else 150
            li = lights(siren=200, lamp=300, dusk=60, moon=260, nexus=nex, rim=0, fill=130)  # FIX R2: jalan bawah tidak gelap total
        else:
            # 2c: kembali ke ruang inti — push-in ke wajah yang meredup
            t = seg_t(f, 216, 287)
            chars["KAI"] = char(RX, 3.5, 0, rot=180, lean=4, head_tilt=lerp(-14, -8, smooth(t)),
                                head_turn=0, armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(RX - 1.0, lerp(-8.0, -6.0, smooth(t)), lerp(2.0, 3.0, smooth(t)),
                            RX, lerp(6.0, 10.0, smooth(t)), lerp(4.0, 9.0, smooth(t)),
                            lerp(10.0, 14.0, smooth(t)), lerp(50, 60, t))
            li = lights(moon=80, nexus=lerp(500, 350, smooth(t)), rim=400, fill=200,
                        core=150, gate=0, eye=0, neon=0, lamp=0, dusk=0)
        for _p in ("EVA", "SEN7", "SEN8", "RES1", "RES2"):
            chars[_p] = hidden()
        if f < 144 or f >= 216:
            for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "CIV1", "CIV2"):
                chars[_p] = hidden()
    # ================= S3 EVA MASUK (288-599) — "THE FIRST DOUBT" =================
    elif f < 600:
        if f < 360:
            # 3a: wide — EVA melangkah dari bayangan ke cahaya biru
            t = seg_t(f, 288, 359)
            eva_x = lerp(88, 85, smooth(t))
            eva_y = lerp(-10, -1, smooth(t))
            chars["EVA"] = char(eva_x, eva_y, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["KAI"] = char(RX, 3.5, 0, rot=lerp(180, 135, smooth(t)), lean=4,
                                head_tilt=0, head_turn=lerp(0, 25, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(RX + 2.0, -9.0, 2.2, RX + 2.0, -1.0, 1.5, 10.0, 46)
            li = lights(moon=80, nexus=lerp(350, 250, smooth(t)), rim=400, fill=200,
                        core=150, gate=0, eva=lerp(0, 500, smooth(t)),
                        neon=0, lamp=0, dusk=0)
        elif f < 480:
            # 3b: slow dolly-in ke EVA — mata biru menyala lebih terang
            t = seg_t(f, 360, 479)
            chars["EVA"] = char(85, -1, 0, rot=135, lean=2, head_tilt=lerp(4, 0, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["KAI"] = char(RX, 3.5, 0, rot=135, lean=4, head_tilt=0, head_turn=25,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(lerp(87.3, 86.6, smooth(t)), lerp(1.3, 0.6, smooth(t)),
                            lerp(1.7, 1.6, smooth(t)),
                            85, -1, 1.5, lerp(4.5, 2.4, smooth(t)), lerp(48, 60, t))
            # FIX R3: kamera pindah ke DEPAN EVA (sisi +x+y, arah dia menghadap,
            # rot=135) — sebelumnya di -y (belakang) sehingga wajah/mata biru
            # TIDAK PERNAH terlihat; 3b harus menunjukkan mata biru.
            li = lights(moon=80, nexus=250, rim=300, fill=200, core=150, gate=0,
                        eva=600, neon=0, lamp=0, dusk=0)
        else:
            # 3c: two-shot Kairo + EVA — biru vs merah di satu frame
            t = seg_t(f, 480, 599)
            chars["EVA"] = char(85, -1, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["KAI"] = char(RX, 3.5, 0, rot=135, lean=4, head_tilt=0, head_turn=25,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(lerp(84.5, 84.0, smooth(t)), lerp(4.5, 4.0, smooth(t)),
                            1.7, 82.5, 1.0, 1.4, 6.5, 50)
            # FIX R3: kamera two-shot pindah ke DEPAN (+x+y) — sebelumnya di
            # belakang-kiri (-y) sehingga yang terlihat punggung Kairo + EVA,
            # bukan "biru vs merah di satu frame".
            li = lights(moon=80, nexus=300, rim=400, fill=200, core=150, gate=0,
                        eva=500, neon=0, lamp=0, dusk=0)
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S4 BEKAS LUKA (600-863) =================
    elif f < 864:
        if f < 672:
            # 4a: ECU bekas luka — berkilau biru SANGAT lemah (scar_glow)
            t = seg_t(f, 600, 671)
            props["scar_glow"] = True
            chars["KAI"] = char(RX, 2.0, 0, rot=0, lean=lerp(4, 6, smooth(t)),
                                head_tilt=lerp(0, -4, smooth(t)), head_turn=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(lerp(RX + 0.3, RX + 0.15, smooth(t)), lerp(-0.6, -0.35, smooth(t)),
                            lerp(1.65, 1.62, smooth(t)),
                            RX, 2.0, 1.6, lerp(2.6, 2.3, smooth(t)), lerp(75, 85, t))
            li = lights(moon=80, nexus=200, rim=500, fill=200, core=150, gate=0,
                        eva=300, neon=0, lamp=0, dusk=0)
            for _p in ("EVA", "SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES1", "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
        elif f < 768:
            # 4b: two-shot dekat — jari EVA mendekat tapi TIDAK menyentuh
            t = seg_t(f, 672, 767)
            props["scar_glow"] = True
            chars["KAI"] = char(RX, 2.0, 0, rot=0, lean=6, head_tilt=-4, head_turn=0,
                                armL=5, armR=lerp(5, 30, smooth(t)), legL=0, legR=0)
            chars["EVA"] = char(RX + 1.5, 0.5, 0, rot=200, lean=3, head_tilt=4,
                                armL=5, armR=lerp(5, 55, smooth(t)), legL=0, legR=0)
            chars_cam = cam(lerp(RX + 0.5, RX + 0.3, smooth(t)), lerp(-2.6, -2.2, smooth(t)),
                            1.6, RX + 0.7, 1.2, 1.5, lerp(3.4, 2.8, smooth(t)), 62)
            li = lights(moon=80, nexus=200, rim=500, fill=200, core=150, gate=0,
                        eva=500, neon=0, lamp=0, dusk=0)
            for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES1", "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
        else:
            # 4c: pull-back pelan ke wide — kilau biru memudar, NEXUS mengawasi
            t = seg_t(f, 768, 863)
            chars["KAI"] = char(RX, 2.0, 0, rot=0, lean=6, head_tilt=-4, head_turn=0,
                                armL=5, armR=30, legL=0, legR=0)
            chars["EVA"] = char(RX + 1.5, 0.5, 0, rot=200, lean=3, head_tilt=4,
                                armL=5, armR=55, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(RX + 0.5, lerp(-2.2, -6.0, smooth(t)), lerp(1.6, 2.0, smooth(t)),
                            RX + 0.7, 1.2, 1.5, lerp(2.8, 6.0, smooth(t)), lerp(62, 50, t))
            li = lights(moon=80, nexus=lerp(200, 400, smooth(t)), rim=500, fill=200,
                        core=150, gate=0, eva=400, neon=0, lamp=0, dusk=0)
            for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                       "RES1", "RES2", "CIV1", "CIV2"):
                chars[_p] = hidden()
    # ================= S5 NEXUS PULIH (864-1055) =================
    elif f < 1056:
        if f < 936:
            # 5a: fast push-in ke wajah NEXUS — terbentuk kembali TAJAM
            t = seg_t(f, 864, 935)
            chars["KAI"] = char(RX, 3.0, 0, rot=180, lean=4, head_tilt=lerp(0, -12, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = sentinel_frozen(RX - 3, 12)
            chars["SEN2"] = sentinel_frozen(RX + 3, 12)
            chars_cam = cam(RX - 1.0, lerp(-8.0, -5.0, smooth(t)), lerp(2.0, 3.5, smooth(t)),
                            RX, lerp(2.0, 10.0, smooth(t)), lerp(1.5, 9.0, smooth(t)),
                            lerp(9.0, 15.0, smooth(t)), lerp(50, 62, t), roll=9)
            alarm = 900 if (f // 6) % 2 == 0 else 100
            li = lights(moon=80, nexus=lerp(800, 2000, smooth(t)), rim=700, fill=200,
                        core=150, gate=0, eva=400, siren=alarm,
                        neon=0, lamp=0, dusk=0)
        elif f < 1008:
            # 5b: Sentinel BERBALIK menghadap EVA (rot 180 -> 0)
            t = seg_t(f, 936, 1007)
            rot = lerp(180, 0, smooth(seg_t(f, 936, 970)))
            chars["SEN1"] = char(RX - 3, 12, 0, rot=rot, lean=3, head_tilt=0,
                                 armL=6, armR=-6, legL=0, legR=0, eye_red=True)
            chars["SEN2"] = char(RX + 3, 12, 0, rot=rot, lean=3, head_tilt=0,
                                 armL=6, armR=-6, legL=0, legR=0, eye_red=True)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["KAI"] = char(RX, 3.0, 0, rot=180, lean=4, head_tilt=-8,
                                head_turn=lerp(0, 30, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX, lerp(-4.0, -2.0, smooth(t)), 2.0,
                            RX, 8.0, 1.5, 10.0, 52)
            li = lights(moon=80, nexus=1800, rim=700, fill=200, core=150,
                        gate=0, eva=400, eye=600, neon=0, lamp=0, dusk=0)
        else:
            # 5c: wide — Sentinel mengangkat senjata ke arah EVA
            t = seg_t(f, 1008, 1055)
            chars["SEN1"] = char(RX - 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=lerp(-6, 55, smooth(t)), legL=0, legR=0,
                                 eye_red=True)
            chars["SEN2"] = char(RX + 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=lerp(-6, 55, smooth(t)), legL=0, legR=0,
                                 eye_red=True)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["KAI"] = char(RX, 3.0, 0, rot=180, lean=4, head_tilt=-8, head_turn=30,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(RX + 1.0, -7.0, 2.2, 82.0, 5.0, 1.5, 11.0, 48)
            li = lights(moon=80, nexus=1800, rim=700, fill=200, core=150,
                        gate=0, eva=400, eye=700, neon=0, lamp=0, dusk=0)
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S6 GERBANG PUTIH (1056-1199) =================
    elif f < 1200:
        # Gerbang TERBUKA: gate_open 0 -> 1 selama S6 (celah vertikal melebar).
        gate_open = smooth(seg_t(f, 1056, 1199))
        if f < 1120:
            # 6a: tracking + low-angle ke gerbang
            t = seg_t(f, 1056, 1119)
            chars["KAI"] = char(RX, 3.0, 0, rot=lerp(180, 135, smooth(t)), lean=4,
                                head_tilt=lerp(-8, 0, smooth(t)), head_turn=lerp(30, -20, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = char(RX - 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars["SEN2"] = char(RX + 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars_cam = cam(lerp(RX + 1.0, RX, smooth(t)), lerp(-5.0, -3.0, smooth(t)),
                            lerp(1.2, 1.0, smooth(t)),
                            RX, lerp(6.0, 18.0, smooth(t)), lerp(1.5, 3.0, smooth(t)),
                            lerp(7.0, 18.0, smooth(t)), lerp(50, 55, t))
            li = lights(moon=80, nexus=800, rim=600, fill=200, core=150,
                        gate=lerp(0, 250, smooth(t)), eva=400, eye=500,
                        neon=0, lamp=0, dusk=0)
        else:
            # 6b: Kairo menoleh ke gerbang — wajah setengah putih setengah merah
            t = seg_t(f, 1120, 1199)
            chars["KAI"] = char(RX, 3.0, 0, rot=135, lean=4, head_tilt=0,
                                head_turn=lerp(-20, -45, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = char(RX - 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars["SEN2"] = char(RX + 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX + 0.8, lerp(-4.5, -3.5, smooth(t)), lerp(1.5, 1.4, smooth(t)),
                            RX, 3.0, 1.5, lerp(4.0, 3.0, smooth(t)), lerp(55, 65, t))
            li = lights(moon=80, nexus=700, rim=500, fill=200, core=150,
                        gate=lerp(250, 400, smooth(t)), eva=400, eye=500,
                        neon=0, lamp=0, dusk=0)
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S7 PENGAKUAN EVA (1200-1319) =================
    elif f < 1320:
        gate_open = 1.0
        if f < 1260:
            # 7a: dolly-in ke mata EVA -> ECU
            t = seg_t(f, 1200, 1259)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=lerp(4, -2, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["KAI"] = char(RX, 3.0, 0, rot=135, lean=4, head_tilt=0, head_turn=-30,
                                armL=5, armR=5, legL=0, legR=0)
            chars_cam = cam(lerp(85.8, 85.3, smooth(t)), lerp(2.4, 1.6, smooth(t)),
                            lerp(1.7, 1.6, smooth(t)),
                            84, 0, 1.5, lerp(3.5, 1.8, smooth(t)), lerp(50, 68, t))
            # FIX R3: kamera ECU pindah ke DEPAN EVA (+x+y, arah rot=135) —
            # sebelumnya di -y (belakang) sehingga yang terlihat punggung
            # kepala, bukan "dolly-in ke mata EVA".
            li = lights(moon=80, nexus=400, rim=400, fill=200, core=150,
                        gate=500, eva=700, neon=0, lamp=0, dusk=0)
        else:
            # 7b: montase kilat 3 cut — 213 Kairo sebelumnya, bekas luka yang sama
            cut = (f - 1260) // 20  # 0, 1, 2
            if cut == 0:
                chars["KAI"] = char(RX - 4, 8, 0, rot=30, lean=10, crouch=0.7,
                                    head_tilt=16, armL=15, armR=15)
                chars_cam = cam(RX - 4, 4.0, 1.0, RX - 4, 8, 1.0, 4.2, 55)
            elif cut == 1:
                chars["KAI"] = char(RX + 4, 9, 0, rot=-25, lean=14, crouch=0.85,
                                    head_tilt=20, armL=20, armR=10)
                chars_cam = cam(RX + 4, 5.0, 1.1, RX + 4, 9, 1.1, 4.2, 55)
            else:
                chars["KAI"] = char(RX, 12, 0, rot=0, lean=0, pitch=-80,
                                    head_tilt=0, armL=30, armR=30)
                chars_cam = cam(RX + 1, 8.0, 1.2, RX, 12, 0.5, 4.5, 50)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            li = lights(moon=80, nexus=500, rim=600, fill=200, core=150,
                        gate=500, eva=500, neon=0, lamp=0, dusk=0)
        for _p in ("SEN1", "SEN2", "SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()
    # ================= S8 TWIST (1320-1439) =================
    else:
        gate_open = 1.0
        props["laser_eva"] = True  # titik laser merah bertemu di tubuh EVA
        if f < 1380:
            # 8a: wide hero — Kairo di antara gerbang (kanan/+y) dan EVA
            t = seg_t(f, 1320, 1379)
            chars["KAI"] = char(RX, lerp(3.0, 5.0, smooth(t)), 0, rot=180, lean=6,
                                head_tilt=0, head_turn=lerp(0, -15, smooth(t)),
                                armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = char(RX - 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars["SEN2"] = char(RX + 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX + 0.6, lerp(-5.5, -4.5, smooth(t)), lerp(1.2, 1.3, smooth(t)),
                            RX, 5.0, 1.4, 8.0, lerp(54, 52, t))
            li = lights(moon=80, nexus=1500, rim=600, fill=200, core=150,
                        gate=400, eva=500, eye=700, neon=0, lamp=0, dusk=0)
        else:
            # 8b: pull-back lambat -> hitam + end card (f1380-1439, ASS)
            t = seg_t(f, 1380, 1439)
            chars["KAI"] = char(RX, 5.0, 0, rot=180, lean=6, head_tilt=0,
                                head_turn=-15, armL=5, armR=5, legL=0, legR=0)
            chars["EVA"] = char(84, 0, 0, rot=135, lean=2, head_tilt=0,
                                armL=5, armR=5, legL=0, legR=0)
            chars["SEN1"] = char(RX - 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars["SEN2"] = char(RX + 3, 12, 0, rot=0, lean=5, head_tilt=0,
                                 armL=6, armR=55, legL=0, legR=0, eye_red=True)
            chars_cam = cam(RX + 0.6, lerp(-4.5, -7.5, smooth(t)), lerp(1.3, 2.0, smooth(t)),
                            RX, 5.0, 1.4, lerp(8.0, 11.0, smooth(t)), lerp(48, 42, t))
            # ruangan meredup menuju hitam (nexus + gate turun pelan)
            dim = 1.0 - 0.55 * smooth(seg_t(f, 1400, 1439))
            li = lights(moon=80, nexus=1500 * dim, rim=600 * dim, fill=200 * dim,
                        core=150, gate=400 * dim, eva=500 * dim, eye=700,
                        neon=0, lamp=0, dusk=0)
        for _p in ("SEN3", "SEN4", "SEN5", "SEN6", "SEN7", "SEN8",
                   "RES1", "RES2", "CIV1", "CIV2"):
            chars[_p] = hidden()

    # pastikan SEMUA karakter ada di tiap baris (0 frame kosong)
    for _p in ALL_CHARS:
        if _p not in chars:
            chars[_p] = hidden()

    rows.append({"f": f, "t": round(f / 24.0, 4), "chars": chars, "lights": li,
                 "cam": chars_cam, "props": props, "flash_white": flash_white,
                 "gate_open": round(gate_open, 3), "nexus_glitch": bool(nexus_glitch)})


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plan.json")
    with open(out, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    print(f"WROTE {out}: {len(rows)} rows")
    # self-checks
    assert len(rows) == N
    assert rows[0]["f"] == 0 and rows[-1]["f"] == N - 1
    flashes = [r["f"] for r in rows if r["flash_white"]]
    assert flashes == [], f"flash frames (harus kosong di Ep 2): {flashes}"
    empty_rows = [r["f"] for r in rows if not r["chars"]]
    assert not empty_rows, f"frame kosong: {empty_rows}"
    missing = [(r["f"], [p for p in ALL_CHARS if p not in r["chars"]])
               for r in rows if any(p not in r["chars"] for p in ALL_CHARS)]
    assert not missing, f"karakter hilang: {missing[:5]}"
    glitch = [r["f"] for r in rows if r["nexus_glitch"]]
    gate = [r["f"] for r in rows if r["gate_open"] > 0]
    scar = [r["f"] for r in rows if r["props"]["scar_glow"]]
    laser = [r["f"] for r in rows if r["props"]["laser_eva"]]
    print(f"CHECK OK: 0 flash, semua {len(rows)} baris punya "
          f"{len(ALL_CHARS)} karakter, 0 frame kosong")
    print(f"  glitch frames: {glitch[0]}-{glitch[-1]} ({len(glitch)} frame)")
    print(f"  gate_open>0: {gate[0]}-{gate[-1]} ({len(gate)} frame)")
    print(f"  scar_glow: {scar[0]}-{scar[-1]} ({len(scar)} frame)")
    print(f"  laser_eva: {laser[0]}-{laser[-1]} ({len(laser)} frame)")


if __name__ == "__main__":
    main()
