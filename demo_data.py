"""Synthetic horse-racing data so the pipeline and dashboard work end to end.

Everything produced here is SIMULATED (is_synthetic = True). Swap in real data
with the CSV or API options in 01_load_data once you have a source.
"""
import numpy as np
import pandas as pd

TRACKS = [
    ("Churchill Downs", "dirt"), ("Saratoga", "dirt"), ("Santa Anita", "dirt"),
    ("Keeneland", "turf"), ("Belmont Park", "turf"), ("Del Mar", "dirt"),
    ("Gulfstream Park", "dirt"), ("Aqueduct", "dirt"),
]
GOINGS = {"dirt": ["fast", "good", "muddy", "sloppy"], "turf": ["firm", "good", "yielding", "soft"]}
DISTANCES_M = [1000, 1200, 1400, 1600, 1800, 2000, 2400]


def make_demo(n_races: int = 3000, seed: int = 7):
    rng = np.random.default_rng(seed)
    horses = [f"Horse {i:03d}" for i in range(400)]
    jockeys = [f"Jockey {i:02d}" for i in range(40)]
    trainers = [f"Trainer {i:02d}" for i in range(30)]
    h_skill = rng.normal(0, 0.8, len(horses))
    j_skill = rng.normal(0, 0.25, len(jockeys))
    t_skill = rng.normal(0, 0.2, len(trainers))
    horse_trainer = rng.integers(0, len(trainers), len(horses))

    start = pd.Timestamp("2025-01-01")
    races, runners = [], []
    for r in range(n_races):
        track, surface = TRACKS[rng.integers(len(TRACKS))]
        date = start + pd.Timedelta(days=int(rng.integers(0, 600)))
        field = int(rng.integers(6, 15))
        going = str(rng.choice(GOINGS[surface]))
        race_id = f"R{r:05d}"
        races.append(dict(
            race_id=race_id, race_date=date.date(), track=track,
            race_no=int(rng.integers(1, 11)), distance_m=int(rng.choice(DISTANCES_M)),
            surface=surface, going=going, purse=int(rng.choice([20000, 35000, 50000, 100000])),
            is_synthetic=True,
        ))
        idx = rng.choice(len(horses), field, replace=False)
        jidx = rng.integers(0, len(jockeys), field)
        draws = rng.permutation(field) + 1
        true_skill = np.array([h_skill[h] + j_skill[j] + t_skill[horse_trainer[h]]
                               for h, j in zip(idx, jidx)])
        draw_bias = -0.03 * (draws - field / 2)          # small inside-draw edge
        score = true_skill + draw_bias + rng.gumbel(0, 1, field)   # race-day noise
        finish = score.argsort()[::-1].argsort() + 1               # 1 = best
        p = np.exp(true_skill + draw_bias); p /= p.sum()
        p_market = p * np.exp(rng.normal(0, 0.15, field)); p_market /= p_market.sum()
        sp = 1 / (p_market * 1.15)                                  # 15% overround
        for k in range(field):
            runners.append(dict(
                race_id=race_id, horse=horses[idx[k]], jockey=jockeys[jidx[k]],
                trainer=trainers[horse_trainer[idx[k]]], draw=int(draws[k]),
                sp_decimal=round(float(max(sp[k], 1.05)), 2), finish_pos=int(finish[k]),
            ))
    return pd.DataFrame(races), pd.DataFrame(runners)
