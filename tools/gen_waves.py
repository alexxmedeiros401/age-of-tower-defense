"""Writes data/waves.json. Edit the table below to rebalance; each group = (type, count, interval_s, delay_s)."""
import json, sys
W = [
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
waves = [[{"type": t, "count": c, "interval": i, "delay": d} for (t, c, i, d) in w] for w in W]
json.dump({"waves": waves}, open(sys.argv[1], "w"), indent=1)
print(len(waves), "waves")
