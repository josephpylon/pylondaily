#!/usr/bin/env python3
"""Pylon Daily: rebuild data.json from nflverse (https://github.com/nflverse/nflverse-data).

Run by .github/workflows/update-data.yml every morning. Standard library only.
Writes data.json only if every sanity check passes, so a bad download never reaches players.

data.json holds:
  note      text shown in the footer ("2026 NFL season through Week 11 (as of Nov 18, 2026)")
  QB/RB/WR/TE  fantasy rows "name,team,games,full-PPR total,standard total" joined by ";"
               (games = games with a stat, the fantasytools.ai convention the game was built on)
  YDS       {QB,RB,WR,TE}: "name,team,games played,passing yds,rushing yds,receiving yds,flags" for the Yards
            options (Passing, Rushing, Receiving, All). flags: p = threw a pass, r = had a carry, c = had a catch.
            Every QB/RB/WR/TE (fullbacks as RB) with a pass, carry or catch. Games played = games with a snap.
  rookies   names of this season's rookie class found in the pools
"""
import csv, io, json, sys, urllib.request, datetime, collections

BASE = "https://github.com/nflverse/nflverse-data/releases/download/"
# first-year NFL players who are not part of this rookie class (e.g. older undrafted players coming from other leagues)
NOT_ROOKIE_CLASS = {"Dohnte Meyers"}
# nflverse team codes that differ from the ones the game shows
TEAM_FIX = {"LA": "LAR"}
# like fantasytools.ai's leaderboard: only players with at least 1 full-PPR point on the season
MIN_PPR_TOTAL = 1.0

def get_csv(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "pylon-daily-data"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return list(csv.DictReader(io.TextIOWrapper(r, encoding="utf-8")))

def num(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def fmt(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"

def main():
    today = datetime.date.today()
    season = int(sys.argv[1]) if len(sys.argv) > 1 else (today.year if today.month >= 9 else today.year - 1)
    reg = get_csv(f"stats_player/stats_player_reg_{season}.csv")
    snaps = get_csv(f"snap_counts/snap_counts_{season}.csv")
    players = {p["gsis_id"]: p for p in get_csv("players/players.csv")}

    # the latest regular-season week with stats (player stats are posted before snap counts)
    weekly = get_csv(f"stats_player/stats_player_week_{season}.csv")
    week = max([int(s["week"]) for s in snaps if s.get("game_type") == "REG"] +
               [int(w["week"]) for w in weekly if w.get("season_type") == "REG"] + [0])
    snap_games = collections.defaultdict(set)
    for s in snaps:
        if num(s["offense_snaps"]) + num(s["defense_snaps"]) + num(s["st_snaps"]) > 0:
            snap_games[s["pfr_player_id"]].add(s["game_id"])

    fantasy = {k: [] for k in ("QB", "RB", "WR", "TE")}
    yds_rows = {k: [] for k in ("QB", "RB", "WR", "TE")}
    rookies = set()
    for x in reg:
        pos, name = x["position"], x["player_display_name"].strip()
        team = TEAM_FIX.get(x["recent_team"], x["recent_team"])
        games = int(num(x["games"]))
        if not name or games <= 0: continue
        ppr, std = num(x["fantasy_points_ppr"]), num(x["fantasy_points"])
        p = players.get(x["player_id"], {})
        if pos in fantasy and ppr >= MIN_PPR_TOTAL:
            fantasy[pos].append((ppr, f"{name},{team},{games},{fmt(ppr)},{fmt(std)}"))
        played = max(games, len(snap_games.get(p.get("pfr_id", ""), ())))
        ypos = {"FB": "RB", "CB": "WR"}.get(pos, pos)
        py, ry, cy = (int(num(x[k])) for k in ("passing_yards", "rushing_yards", "receiving_yards"))
        flags = ("p" if num(x["attempts"]) > 0 else "") + ("r" if num(x["carries"]) > 0 else "") + ("c" if num(x["receptions"]) > 0 else "")
        if ypos in yds_rows and flags and (pos != "CB" or cy > 0):     # two-way players listed at CB (Travis Hunter)
            yds_rows[ypos].append((py + ry + cy, f"{name},{team},{played},{py},{ry},{cy},{flags}"))
        if p.get("rookie_season") == str(season) and pos in ("QB", "RB", "WR", "TE", "FB") and name not in NOT_ROOKIE_CLASS:
            rookies.add(name)

    for d in (fantasy, yds_rows):
        for k in d: d[k].sort(key=lambda t: -t[0])
    out = {k: ";".join(r for _, r in v) for k, v in fantasy.items()}
    out["YDS"] = {k: ";".join(r for _, r in v) for k, v in yds_rows.items()}
    pool_names = {r.split(",")[0] for v in fantasy.values() for _, r in v} | {r.split(",")[0] for v in yds_rows.values() for _, r in v}
    out["rookies"] = sorted(rookies & pool_names)
    stamp = today.strftime("%b %-d, %Y")
    out["note"] = f"{season} NFL season through Week {week} (as of {stamp})"
    out["season"], out["week"], out["updated"] = season, week, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # sanity checks: refuse to publish anything that looks broken
    counts = {k: len(v) for k, v in fantasy.items()} | {"YDS_" + k: len(v) for k, v in yds_rows.items()}
    print("rows:", counts, "week", week, "rookies", len(out["rookies"]))
    if week < 1: sys.exit("no regular-season weeks yet; keeping the old data.json")
    if min(counts["QB"], counts["TE"]) < 20 or min(counts["RB"], counts["WR"]) < 40 or min(counts["YDS_QB"], counts["YDS_RB"], counts["YDS_WR"], counts["YDS_TE"]) < 20:
        sys.exit("too few players; keeping the old data.json")
    for k in ("QB", "RB", "WR", "TE"):
        for row in out[k].split(";"):
            n, t, g, a, b = row.split(",")
            assert int(g) > 0 and n and t, row
    for k in yds_rows:
        for row in out["YDS"][k].split(";"):
            n, t, g, py, ry, cy, fl = row.split(",")
            assert int(g) > 0 and fl and set(fl) <= set("prc"), row
    # nothing new (e.g. no games since the last run): leave data.json alone, so there is no commit and no redeploy
    try:
        with open("data.json", encoding="utf-8") as f:
            old = json.load(f)
        if all(old.get(k) == out[k] for k in out if k not in ("note", "updated")):
            print("No new stats; data.json unchanged.")
            return
    except (OSError, ValueError):
        pass
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote data.json:", out["note"])

if __name__ == "__main__":
    main()
