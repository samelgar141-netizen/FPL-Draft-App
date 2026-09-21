"""
FPL Draft data refresh script.
Reads FPL_COOKIE and FPL_TOKEN from environment variables (set as GitHub Secrets
for automated runs, or exported locally for manual runs).

Usage (local):
    export FPL_COOKIE="..."
    export FPL_TOKEN="Bearer ..."
    python refresh_data.py

Usage (GitHub Actions): credentials injected automatically via repository secrets.
"""

import os
import json
import requests
import pandas as pd
import numpy as np

# ── Configuration ─────────────────────────────────────────────────────────────
LEAGUE_ID = 48023
DATA_DIR  = "data"
os.makedirs(DATA_DIR, exist_ok=True)

FPL_COOKIE = os.environ.get("FPL_COOKIE", "")
FPL_TOKEN  = os.environ.get("FPL_TOKEN", "")

if not FPL_COOKIE:
    raise SystemExit(
        "ERROR: FPL_COOKIE environment variable must be set.\n"
        "Set it as a GitHub repository secret, or export it locally before running."
    )

if not FPL_TOKEN:
    print("WARNING: FPL_TOKEN not set. Some endpoints may require it — will use cookie-only auth.")
    print("         The Bearer token expires every ~8 hours. Update the FPL_TOKEN secret when needed.")

# ── Auth patch: inject credentials into every requests.get call ───────────────
_orig_get = requests.get
def _authed_get(url, **kwargs):
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.setdefault("Cookie", FPL_COOKIE)
    headers.setdefault("x-api-authorization", FPL_TOKEN)
    headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/146.0.0.0 Safari/537.36",
    )
    return _orig_get(url, headers=headers, **kwargs)
requests.get = _authed_get


# ── Data fetching functions (ported from FPL_Draft_Data.ipynb) ────────────────

def get_draft_league_data(draft_league_id):
    url = f"https://draft.premierleague.com/api/league/{draft_league_id}/details"
    data = requests.get(url).json()

    teams_df = pd.DataFrame(data["league_entries"])
    teams = teams_df.drop(columns=["joined_time"])
    teams["entry_name"] = teams["entry_name"].fillna("Average")
    teams = teams.sort_values("entry_name").reset_index(drop=True)
    teams["alphabetic_order"] = teams.index + 1
    teams["entry_id"] = teams["entry_id"].astype(str).str.replace(".0", "", regex=False)

    gw = pd.DataFrame({"gw": range(1, 39)})
    teams["key"] = 1
    gw["key"] = 1
    gw_and_team = pd.merge(gw, teams, on="key").drop("key", axis=1).rename(columns={
        "id": "team",
        "entry_name": "team_name",
        "player_first_name": "team_player_first_name",
        "player_last_name": "team_player_last_name",
    })

    player_stats_data = requests.get("https://draft.premierleague.com/api/bootstrap-static").json()
    elements_base = pd.DataFrame(player_stats_data["elements"])[["id"]]
    elements_base["id"] = elements_base["id"].astype(str)
    elements_base = elements_base.rename(columns={"id": "element_id"})
    elements_base["key"] = 1
    gw_and_element = pd.merge(gw, elements_base, on="key").drop("key", axis=1)

    return gw_and_team, teams, gw_and_element


def process_match_results(draft_league_id, teams):
    url = f"https://draft.premierleague.com/api/league/{draft_league_id}/details"
    data = requests.get(url).json()

    matches = pd.DataFrame(data["matches"]).drop(columns=["winning_league_entry", "winning_method"])

    def outcomes(a, b):
        return np.select(
            [matches[a] > matches[b], matches[a] < matches[b], matches[a] == matches[b]],
            ["Win", "Lose", "Draw"], default="Unknown"
        )

    matches["league_entry_1_result"] = outcomes("league_entry_1_points", "league_entry_2_points")
    matches["league_entry_2_result"] = outcomes("league_entry_2_points", "league_entry_1_points")

    df1 = pd.DataFrame({
        "gw": matches["event"], "finished": matches["finished"],
        "team": matches["league_entry_1"], "opponent": matches["league_entry_2"],
        "team_points": matches["league_entry_1_points"], "opponent_points": matches["league_entry_2_points"],
        "team_result": matches["league_entry_1_result"],
    })
    df2 = pd.DataFrame({
        "gw": matches["event"], "finished": matches["finished"],
        "team": matches["league_entry_2"], "opponent": matches["league_entry_1"],
        "team_points": matches["league_entry_2_points"], "opponent_points": matches["league_entry_1_points"],
        "team_result": matches["league_entry_2_result"],
    })

    final_df = pd.concat([df1, df2], ignore_index=True)
    final_df["points_difference"] = final_df["team_points"] - final_df["opponent_points"]
    final_df["result_points"] = final_df["team_result"].map({"Win": 3, "Lose": 0, "Draw": 1})

    merged = pd.merge(final_df, teams, left_on="team", right_on="id")
    merged = pd.merge(merged, teams, left_on="opponent", right_on="id")
    match_results = merged.rename(columns={
        "entry_name_x": "team_name", "player_first_name_x": "team_player_first_name",
        "player_last_name_x": "team_player_last_name", "entry_name_y": "opponent_name",
        "player_first_name_y": "opponent_player_first_name", "player_last_name_y": "opponent_player_last_name",
        "entry_id_x": "team_entry_id", "entry_id_y": "opponent_entry_id",
    })[[
        "gw", "finished", "team", "team_entry_id", "team_name", "team_player_first_name",
        "team_player_last_name", "opponent", "opponent_entry_id", "opponent_name",
        "opponent_player_first_name", "opponent_player_last_name",
        "team_points", "opponent_points", "points_difference", "team_result", "result_points",
    ]]

    match_results = match_results.sort_values("gw")
    match_results["cumulative_team_points"]     = match_results.groupby("team")["team_points"].cumsum()
    match_results["cumulative_opponent_points"] = match_results.groupby("team")["opponent_points"].cumsum()
    match_results["cumulative_result_points"]   = match_results.groupby("team")["result_points"].cumsum()

    match_results = match_results.sort_values(
        ["gw", "cumulative_result_points", "cumulative_team_points", "team_name"],
        ascending=[True, False, False, True],
    )
    match_results["league_position"]          = match_results.groupby("gw").cumcount() + 1
    match_results["gw_team_points_rank"]      = match_results.groupby("gw")["team_points"].rank(ascending=False)
    match_results["gw_opponent_points_rank"]  = match_results.groupby("gw")["opponent_points"].rank(ascending=False)
    return match_results


def fetch_player_stats(gw_and_element):
    player_stats_data = requests.get("https://draft.premierleague.com/api/bootstrap-static").json()
    elements_df = pd.DataFrame(player_stats_data["elements"])
    elements_df_tidy = elements_df[
        ["id", "code", "first_name", "second_name", "web_name", "element_type", "team"]
    ].copy()
    elements_df_tidy["id"] = elements_df_tidy["id"].astype(str)

    all_gw_data = []
    for gw in range(1, 39):
        r = requests.get(f"https://draft.premierleague.com/api/event/{gw}/live")
        if r.status_code != 200:
            print(f"GW {gw}: no data ({r.status_code}), stopping.")
            break
        all_gw_data.append({"gw": gw, "data": r.json()})
        print(f"GW {gw}: fetched OK")

    extracted = []
    for item in all_gw_data:
        for element_id, element_info in item["data"].get("elements", {}).items():
            for explain in element_info.get("explain", []):
                for entry in explain[0]:
                    extracted.append({
                        "gw": item["gw"], "number": element_id,
                        "name": entry["name"], "points": entry["points"],
                        "value": entry["value"], "stat": entry["stat"],
                    })

    if not extracted:
        raise ValueError("No player stat data extracted from API.")

    ps = pd.DataFrame(extracted)
    ps["number"] = ps["number"].astype(str)
    ps = pd.merge(ps, elements_df_tidy, left_on="number", right_on="id")
    ps["played"] = ps.apply(lambda r: 1 if r["stat"] == "minutes" and r["value"] > 0 else 0, axis=1)

    grouped = (
        ps.groupby(["gw", "number"])
        .agg(total_points=("points", "sum"), minutes_played=("played", "max"))
        .reset_index()
    )
    grouped["minutes_played"] = grouped["minutes_played"].apply(lambda x: "yes" if x > 0 else "no")
    grouped = pd.merge(
        gw_and_element, grouped, how="left",
        left_on=["gw", "element_id"], right_on=["gw", "number"],
    ).drop(columns=["number"]).rename(columns={"element_id": "number"})

    teams_static = pd.DataFrame(player_stats_data.get("teams", []))
    if not teams_static.empty and "id" in teams_static.columns:
        teams_static = teams_static[["id", "short_name"]]
    else:
        teams_static = pd.DataFrame(columns=["id", "short_name"])

    return grouped, elements_df_tidy, elements_df, teams_static


def fetch_team_and_player_scores(teams, grouped_player_stats_by_gw, elements_df_tidy):
    teams = pd.DataFrame(teams)
    filtered_teams_list = teams[teams["entry_id"].notna()]["entry_id"].astype(str).tolist()

    team_data = []
    for team_id in filtered_teams_list:
        for gw in range(1, 39):
            r = requests.get(f"https://draft.premierleague.com/api/entry/{team_id}/event/{gw}")
            if r.status_code == 200:
                team_data.append({"team_id": team_id, "gw": gw, "picks": r.json().get("picks", [])})
                print(f"  Team {team_id} GW {gw}: OK")
            else:
                print(f"  Team {team_id} GW {gw}: {r.status_code} — skipping remaining GWs for this team")
                break

    team_data_df = pd.DataFrame(team_data)
    exploded = team_data_df.explode("picks").reset_index(drop=True)
    picks_df = pd.json_normalize(exploded["picks"])
    team_line_up = pd.concat([exploded[["team_id", "gw"]], picks_df], axis=1)[
        ["team_id", "gw", "element", "position"]
    ]
    team_line_up["element"] = team_line_up["element"].astype(str)

    merged = pd.merge(
        grouped_player_stats_by_gw, team_line_up,
        left_on=["gw", "number"], right_on=["gw", "element"], how="left",
    )[["team_id", "gw", "number", "position", "total_points", "minutes_played"]]

    detailed = pd.merge(merged, elements_df_tidy, left_on="number", right_on="id")[[
        "team_id", "gw", "number", "position", "total_points", "minutes_played",
        "first_name", "second_name", "web_name", "element_type", "team",
    ]]
    detailed["status"] = np.where(detailed["position"] <= 11, "played", "benched")

    scores = pd.merge(detailed, teams, left_on="team_id", right_on="entry_id", how="left")[[
        "team_id", "entry_name", "player_first_name", "player_last_name", "gw",
        "number", "position", "total_points", "minutes_played",
        "first_name", "second_name", "web_name", "element_type", "team", "status",
    ]]

    print("Fetching FPL prices...")
    players = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()["elements"]
    gw_prices = []
    for player in players:
        pid = player["id"]
        pname = f"{player['first_name']} {player['second_name']}"
        history = requests.get(f"https://fantasy.premierleague.com/api/element-summary/{pid}/").json().get("history", [])
        for record in history:
            gw_prices.append({"Player ID": str(pid), "Player Name": pname, "GW": record["round"], "Price": record["value"] / 10})

    gw_prices_df = pd.DataFrame(gw_prices)
    result = pd.merge(scores, gw_prices_df, left_on=["number", "gw"], right_on=["Player ID", "GW"], how="left").drop(columns=["Player ID", "GW"])
    result["Price"] = result.groupby("number")["Price"].ffill()
    result["Player Name"] = result.groupby("number")["Player Name"].ffill()
    result = result.dropna(subset=["team_id"])
    result["minutes_played"] = result["minutes_played"].fillna("no")
    result["total_points"] = result["total_points"].fillna(0)
    return result


def process_draft_picks(draft_league_id, elements_df):
    url = f"https://draft.premierleague.com/api/draft/{draft_league_id}/choices"
    r = requests.get(url)
    choices_data = r.json() if r.status_code == 200 else {}

    if "choices" not in choices_data:
        # Bearer token likely expired — draft picks never change after the draft,
        # so fall back to the cached file if it exists.
        cached_path = f"{DATA_DIR}/draft_picks.json"
        if os.path.exists(cached_path):
            print(f"  Choices API unavailable (HTTP {r.status_code}) — using cached draft_picks.json (safe: draft picks never change).")
            return pd.read_json(cached_path)
        raise RuntimeError(
            f"Choices API returned HTTP {r.status_code} and no cached draft_picks.json exists.\n"
            "Update the FPL_TOKEN secret with a fresh Bearer token and re-run."
        )

    choices_df = pd.DataFrame(choices_data["choices"])
    choices_df["element"] = choices_df["element"].astype(str)
    elements_df = elements_df.copy()
    elements_df["id"] = elements_df["id"].astype(str)

    draft_picks_df = pd.merge(choices_df, elements_df, how="right", left_on="element", right_on="id")

    drafted = draft_picks_df[draft_picks_df["entry_name"].notna()]
    draft_picks_df["position_points_rank"] = drafted.groupby("element_type")["total_points"].rank(method="first", ascending=False)
    draft_picks_df["pick_order"] = (draft_picks_df["round"] - 1) * 9 + draft_picks_df["pick"]
    draft_picks_df["position_pick_order"] = draft_picks_df.groupby("element_type")["pick_order"].rank(ascending=True)
    draft_picks_df["points_vs_position_pick"] = draft_picks_df["position_pick_order"] - draft_picks_df["position_points_rank"]
    draft_picks_df["points_vs_position_pick_rank"] = draft_picks_df.groupby("element_type")["points_vs_position_pick"].rank(method="first", ascending=False)
    draft_picks_df["all_players_position_points_rank"] = draft_picks_df.groupby("element_type")["total_points"].rank(method="first", ascending=False)
    draft_picks_df["all_players_points_vs_position_pick"] = draft_picks_df["position_pick_order"] - draft_picks_df["all_players_position_points_rank"]
    draft_picks_df["all_players_points_vs_position_pick_rank"] = draft_picks_df.groupby("element_type")["all_players_points_vs_position_pick"].rank(method="first", ascending=False)
    return draft_picks_df


def get_transfers(draft_league_id, elements_df_tidy, team_player_scores_with_cost):
    url = f"https://draft.premierleague.com/api/draft/league/{draft_league_id}/transactions"
    transfers_data = requests.get(url).json()
    transfers_df = pd.DataFrame(transfers_data["transactions"])
    transfers_df["element_in"]  = transfers_df["element_in"].astype(str)
    transfers_df["element_out"] = transfers_df["element_out"].astype(str)

    df = pd.merge(transfers_df, elements_df_tidy, left_on="element_in",  right_on="id")
    df = pd.merge(df,          elements_df_tidy, left_on="element_out", right_on="id")
    transfers = df[["element_in", "element_out", "entry", "event", "kind", "result", "web_name_x", "web_name_y"]].copy()
    transfers["id"] = range(1, len(transfers) + 1)

    scores = team_player_scores_with_cost[["gw", "number", "total_points", "minutes_played"]]
    t = pd.merge(transfers, scores, how="left", left_on="element_in", right_on="number")
    t = t[t["gw"] >= t["event"]]
    t = t.groupby(["id", "element_in", "element_out", "entry", "event", "kind", "result", "web_name_x", "web_name_y"], as_index=False).agg(total_points_in=("total_points", "sum"))
    t = pd.merge(t, scores, how="left", left_on="element_out", right_on="number")
    t = t[t["gw"] >= t["event"]]
    t = t.groupby(["id", "element_in", "element_out", "entry", "event", "kind", "result", "web_name_x", "web_name_y", "total_points_in"], as_index=False).agg(total_points_out=("total_points", "sum"))
    return t


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Step 1/6: Fetching league and team data...")
    gw_and_team, teams, gw_and_element = get_draft_league_data(LEAGUE_ID)

    print("\nStep 2/6: Fetching match results...")
    match_results_ordered = process_match_results(LEAGUE_ID, teams)

    print("\nStep 3/6: Fetching player stats by GW...")
    grouped_player_stats_by_gw, elements_df_tidy, elements_df, teams_static = fetch_player_stats(gw_and_element)

    print("\nStep 4/6: Fetching team lineups and player scores (this is the slow step)...")
    team_player_scores_with_cost = fetch_team_and_player_scores(teams, grouped_player_stats_by_gw, elements_df_tidy)

    print("\nStep 5/6: Fetching draft picks...")
    draft_picks_df = process_draft_picks(LEAGUE_ID, elements_df)

    print("\nStep 6/6: Fetching transfers...")
    transfers = get_transfers(LEAGUE_ID, elements_df_tidy, team_player_scores_with_cost)

    print("\nExporting CSVs...")
    gw_and_team.to_csv(f"{DATA_DIR}/gw_and_team.csv", index=False)
    match_results_ordered.to_csv(f"{DATA_DIR}/matches.csv", index=False)
    team_player_scores_with_cost.to_csv(f"{DATA_DIR}/player_scores.csv", index=False)
    transfers.to_csv(f"{DATA_DIR}/transfers.csv", index=False)
    draft_picks_df.to_csv(f"{DATA_DIR}/original_draft_picks.csv", index=False)

    print("Exporting JSONs...")
    gw_and_team.to_json(f"{DATA_DIR}/gw_and_team.json", orient="records")
    match_results_ordered.to_json(f"{DATA_DIR}/matches.json", orient="records")
    team_player_scores_with_cost.to_json(f"{DATA_DIR}/player_scores.json", orient="records")
    transfers.to_json(f"{DATA_DIR}/transfers.json", orient="records")
    draft_picks_df.to_json(f"{DATA_DIR}/draft_picks.json", orient="records")

    bs_cols = ["id", "first_name", "second_name", "web_name", "element_type", "team",
               "total_points", "form", "points_per_game", "goals_scored", "assists",
               "clean_sheets", "minutes", "draft_rank", "ict_index", "ep_next", "bonus", "starts"]
    bs_cols_available = [c for c in bs_cols if c in elements_df.columns]
    with open(f"{DATA_DIR}/bootstrap.json", "w") as f:
        json.dump({"elements": elements_df[bs_cols_available].to_dict("records"), "teams": teams_static.to_dict("records")}, f)

    print(f"\nDone — data exported to {DATA_DIR}/ (6 JSON files + 5 CSV files)")
