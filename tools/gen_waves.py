"""Writes the wave file for every map. Each group = (type, count, interval_s, delay_s[, path]).
Run: python3 tools/gen_waves.py data"""
import json, sys, os

OUT = sys.argv[1]
MAP1 = [
  [("walker", 10, 1.1, 0)],
  [("walker", 16, 0.8, 0)],
  [("walker", 10, 0.8, 0), ("scout", 8, 0.6, 4)],
  [("walker", 24, 0.5, 0)],
  [("scout", 18, 0.35, 0), ("walker", 10, 0.7, 3)],
  [("walker", 20, 0.5, 0), ("brute", 2, 3.0, 5)],
  [("scout", 32, 0.22, 0)],
  [("brute", 4, 2.2, 0), ("walker", 24, 0.45, 2)],
  [("carrier", 3, 3.0, 0), ("walker", 18, 0.5, 1)],
  [("brute", 7, 1.6, 0), ("walker", 30, 0.35, 2), ("scout", 12, 0.3, 8)],
  [("scout", 45, 0.16, 0)],
  [("carrier", 6, 1.8, 0), ("brute", 4, 2.0, 4)],
  [("walker", 60, 0.2, 0)],
  [("brute", 12, 1.0, 0), ("carrier", 4, 2.0, 3)],
  [("scout", 40, 0.15, 0), ("carrier", 6, 1.2, 2), ("walker", 30, 0.25, 5)],
  [("brute", 18, 0.8, 0)],
  [("carrier", 12, 0.9, 0), ("scout", 40, 0.12, 6)],
  [("brute", 16, 0.7, 0), ("walker", 60, 0.15, 1), ("carrier", 8, 1.0, 6)],
  [("brute", 26, 0.5, 0), ("carrier", 12, 0.7, 4), ("scout", 50, 0.1, 8)],
  [("prime_walker", 1, 1.0, 0), ("brute", 10, 1.2, 6), ("walker", 40, 0.3, 10)],
]

# Glacier Pass: armor shows up earlier, carriers come in bigger flocks, boss brings an armored escort.
MAP2 = [
  [("walker", 12, 1.0, 0)],
  [("walker", 18, 0.7, 0), ("scout", 6, 0.5, 6)],
  [("walker", 14, 0.6, 0), ("brute", 1, 1.0, 6)],
  [("scout", 24, 0.3, 0), ("walker", 12, 0.6, 4)],
  [("brute", 3, 2.5, 0), ("walker", 20, 0.45, 2)],
  [("carrier", 3, 2.5, 0), ("walker", 20, 0.4, 3)],
  [("scout", 40, 0.18, 0), ("brute", 2, 2.0, 5)],
  [("brute", 7, 1.6, 0), ("walker", 28, 0.35, 2)],
  [("carrier", 6, 1.6, 0), ("scout", 24, 0.25, 4)],
  [("brute", 10, 1.2, 0), ("walker", 36, 0.3, 2), ("carrier", 3, 2.0, 8)],
  [("scout", 55, 0.13, 0), ("brute", 4, 1.5, 4)],
  [("carrier", 9, 1.3, 0), ("brute", 6, 1.6, 3)],
  [("walker", 70, 0.17, 0), ("brute", 6, 1.2, 6)],
  [("brute", 16, 0.8, 0), ("carrier", 6, 1.5, 3)],
  [("scout", 50, 0.12, 0), ("carrier", 9, 1.0, 2), ("walker", 40, 0.22, 5)],
  [("brute", 24, 0.65, 0), ("scout", 30, 0.15, 6)],
  [("carrier", 16, 0.75, 0), ("brute", 8, 1.0, 5)],
  [("brute", 22, 0.55, 0), ("walker", 70, 0.13, 1), ("carrier", 10, 0.9, 6)],
  [("brute", 32, 0.45, 0), ("carrier", 16, 0.6, 4), ("scout", 60, 0.09, 8)],
  [("prime_walker", 1, 1.0, 0), ("brute", 16, 0.9, 4), ("carrier", 8, 1.2, 10), ("walker", 50, 0.25, 12)],
]

# Volcano Ridge: everything splits across two portals (counts are totals). Final wave: one Prime Walker per portal.
MAP3 = [
  [("walker", 16, 0.7, 0)],
  [("walker", 20, 0.55, 0), ("scout", 8, 0.45, 6)],
  [("walker", 18, 0.5, 0), ("brute", 2, 2.5, 6)],
  [("scout", 30, 0.25, 0), ("walker", 14, 0.55, 4)],
  [("brute", 4, 2.0, 0), ("walker", 24, 0.4, 3)],
  [("carrier", 4, 2.0, 0), ("walker", 24, 0.35, 3)],
  [("scout", 60, 0.13, 0), ("brute", 4, 1.5, 5)],
  [("brute", 12, 1.0, 0), ("walker", 40, 0.25, 2)],
  [("carrier", 10, 1.0, 0), ("scout", 36, 0.18, 4)],
  [("brute", 16, 0.8, 0), ("walker", 50, 0.2, 2), ("carrier", 6, 1.4, 8)],
  [("scout", 80, 0.09, 0), ("brute", 8, 1.0, 4)],
  [("carrier", 14, 0.9, 0), ("brute", 10, 1.0, 3)],
  [("walker", 100, 0.12, 0), ("brute", 10, 0.8, 6)],
  [("brute", 24, 0.55, 0), ("carrier", 10, 1.0, 3)],
  [("scout", 70, 0.09, 0), ("carrier", 14, 0.7, 2), ("walker", 60, 0.15, 5)],
  [("brute", 36, 0.45, 0), ("scout", 40, 0.12, 6)],
  [("carrier", 24, 0.5, 0), ("brute", 14, 0.7, 5)],
  [("brute", 34, 0.4, 0), ("walker", 100, 0.09, 1), ("carrier", 16, 0.6, 6)],
  [("brute", 48, 0.3, 0), ("carrier", 24, 0.4, 4), ("scout", 90, 0.06, 8)],
  [("prime_walker", 2, 10.0, 0), ("brute", 24, 0.6, 5), ("carrier", 12, 0.8, 10), ("walker", 70, 0.18, 12)],
]


# ---------------- Bronze Age: Shield Bots (regenerating shields) and Repair Drones (heal nearby robots).
# Bosses are Siege Crawlers: armored, shielded, and they summon Shield Bots.
MAP4 = [  # River Delta (Normal)
  [("walker", 14, 0.9, 0)],
  [("walker", 18, 0.7, 0), ("scout", 8, 0.5, 6)],
  [("shield_bot", 4, 1.8, 0), ("walker", 12, 0.6, 3)],
  [("scout", 26, 0.3, 0), ("walker", 14, 0.55, 4)],
  [("shield_bot", 6, 1.4, 0), ("brute", 2, 2.5, 5)],
  [("repair_drone", 3, 2.0, 0), ("walker", 24, 0.4, 1)],
  [("brute", 5, 1.6, 0), ("shield_bot", 6, 1.2, 3)],
  [("scout", 40, 0.18, 0), ("repair_drone", 4, 1.5, 3)],
  [("carrier", 5, 2.0, 0), ("shield_bot", 8, 1.0, 2)],
  [("brute", 10, 1.1, 0), ("repair_drone", 5, 1.3, 2), ("walker", 30, 0.3, 6)],
  [("shield_bot", 16, 0.7, 0), ("scout", 30, 0.15, 4)],
  [("carrier", 8, 1.4, 0), ("repair_drone", 6, 1.0, 2), ("brute", 6, 1.5, 4)],
  [("walker", 70, 0.15, 0), ("shield_bot", 10, 0.8, 4)],
  [("brute", 16, 0.8, 0), ("repair_drone", 8, 0.9, 2)],
  [("shield_bot", 24, 0.5, 0), ("carrier", 8, 1.0, 3), ("scout", 40, 0.12, 6)],
  [("brute", 24, 0.6, 0), ("repair_drone", 10, 0.8, 3)],
  [("carrier", 16, 0.7, 0), ("shield_bot", 20, 0.5, 4)],
  [("brute", 22, 0.5, 0), ("shield_bot", 24, 0.4, 2), ("repair_drone", 12, 0.6, 5)],
  [("shield_bot", 36, 0.35, 0), ("carrier", 16, 0.6, 4), ("brute", 20, 0.5, 8)],
  [("siege_crawler", 1, 1.0, 0), ("brute", 14, 0.9, 6), ("repair_drone", 8, 1.0, 9), ("walker", 40, 0.25, 12)],
]
MAP5 = [  # Desert Citadel (Hard): shields from wave 2, armor sooner
  [("walker", 16, 0.8, 0)],
  [("shield_bot", 4, 1.6, 0), ("walker", 14, 0.6, 3)],
  [("scout", 24, 0.3, 0), ("shield_bot", 4, 1.4, 4)],
  [("brute", 3, 2.2, 0), ("walker", 22, 0.45, 2)],
  [("repair_drone", 4, 1.6, 0), ("shield_bot", 8, 1.0, 1)],
  [("carrier", 4, 2.0, 0), ("brute", 3, 2.0, 3)],
  [("scout", 50, 0.15, 0), ("repair_drone", 4, 1.3, 4)],
  [("brute", 8, 1.2, 0), ("shield_bot", 10, 0.9, 2)],
  [("carrier", 8, 1.3, 0), ("repair_drone", 6, 1.1, 3)],
  [("shield_bot", 18, 0.6, 0), ("brute", 8, 1.0, 3), ("walker", 30, 0.25, 6)],
  [("scout", 60, 0.11, 0), ("repair_drone", 8, 0.9, 3)],
  [("brute", 14, 0.8, 0), ("carrier", 8, 1.0, 3)],
  [("shield_bot", 28, 0.45, 0), ("repair_drone", 10, 0.8, 3)],
  [("brute", 22, 0.6, 0), ("shield_bot", 14, 0.6, 3)],
  [("carrier", 14, 0.7, 0), ("scout", 50, 0.1, 3), ("repair_drone", 10, 0.7, 6)],
  [("brute", 30, 0.45, 0), ("shield_bot", 20, 0.45, 4)],
  [("shield_bot", 40, 0.3, 0), ("carrier", 14, 0.6, 4)],
  [("brute", 30, 0.4, 0), ("repair_drone", 16, 0.5, 2), ("shield_bot", 24, 0.4, 6)],
  [("brute", 40, 0.3, 0), ("carrier", 20, 0.5, 4), ("shield_bot", 30, 0.3, 8)],
  [("siege_crawler", 1, 1.0, 0), ("shield_bot", 20, 0.6, 4), ("brute", 20, 0.7, 8), ("repair_drone", 12, 0.8, 10)],
]
MAP6 = [  # Copper Canyon (Brutal): two portals (counts are totals, split across lanes); twin Siege Crawlers
  [("walker", 20, 0.6, 0)],
  [("walker", 22, 0.5, 0), ("shield_bot", 6, 1.2, 5)],
  [("scout", 30, 0.25, 0), ("shield_bot", 6, 1.2, 4)],
  [("brute", 4, 1.8, 0), ("walker", 28, 0.35, 3)],
  [("repair_drone", 6, 1.2, 0), ("shield_bot", 10, 0.9, 1)],
  [("carrier", 6, 1.5, 0), ("brute", 4, 1.6, 3)],
  [("scout", 70, 0.11, 0), ("repair_drone", 6, 1.0, 4)],
  [("brute", 12, 0.9, 0), ("shield_bot", 14, 0.7, 2)],
  [("carrier", 12, 0.9, 0), ("repair_drone", 8, 0.9, 3)],
  [("shield_bot", 26, 0.45, 0), ("brute", 12, 0.8, 3), ("walker", 40, 0.2, 6)],
  [("scout", 90, 0.08, 0), ("repair_drone", 12, 0.7, 3)],
  [("brute", 20, 0.6, 0), ("carrier", 12, 0.8, 3)],
  [("shield_bot", 40, 0.3, 0), ("repair_drone", 14, 0.6, 3)],
  [("brute", 32, 0.45, 0), ("shield_bot", 20, 0.45, 3)],
  [("carrier", 20, 0.5, 0), ("scout", 70, 0.08, 3), ("repair_drone", 14, 0.5, 6)],
  [("brute", 44, 0.32, 0), ("shield_bot", 30, 0.32, 4)],
  [("shield_bot", 56, 0.22, 0), ("carrier", 20, 0.45, 4)],
  [("brute", 44, 0.28, 0), ("repair_drone", 22, 0.4, 2), ("shield_bot", 34, 0.3, 6)],
  [("brute", 56, 0.22, 0), ("carrier", 28, 0.35, 4), ("shield_bot", 44, 0.22, 8)],
  [("siege_crawler", 2, 10.0, 0), ("shield_bot", 30, 0.45, 4), ("brute", 28, 0.5, 8), ("repair_drone", 16, 0.6, 10)],
]


def write(name, table):
    waves = []
    for w in table:
        groups = []
        for g in w:
            d = {"type": g[0], "count": g[1], "interval": g[2], "delay": g[3]}
            if len(g) > 4:
                d["path"] = g[4]
            groups.append(d)
        waves.append(groups)
    json.dump({"waves": waves}, open(os.path.join(OUT, name), "w"), indent=1)
    print(name, len(waves), "waves")


write("waves.json", MAP1)
write("waves_glacier_pass.json", MAP2)
write("waves_volcano_ridge.json", MAP3)
write("waves_river_delta.json", MAP4)
write("waves_desert_citadel.json", MAP5)
write("waves_copper_canyon.json", MAP6)
