# How to Update FPL Draft Data

Run this process after each gameweek to refresh the app with the latest scores and standings.

---

## Prerequisites

Make sure these are installed on your local Windows machine:

- Python 3.9+ — [python.org](https://www.python.org/downloads/)
- Jupyter Notebook — install via `pip install notebook`
- Required Python packages — run once:
  ```
  pip install requests pandas numpy
  ```
- Git — [git-scm.com](https://git-scm.com/)

---

## Step 1 — Get your FPL Cookie and Bearer Token

The FPL Draft API requires your browser session credentials. These **expire after ~8 hours** so you must re-copy them each time you run the notebook.

### 1a. Open the FPL Draft site in Chrome or Edge

Go to [draft.premierleague.com](https://draft.premierleague.com) and log in to your account.

### 1b. Open DevTools

Press `F12` (or right-click anywhere → **Inspect**) then click the **Network** tab.

### 1c. Trigger an API request

Click on your league or any page that loads data (e.g. your squad, the standings). You will see network requests appear in the list.

### 1d. Find a Draft API request

In the filter box at the top of the Network tab, type `draft.premierleague.com` to filter the list.

Click on any request that starts with `draft.premierleague.com/api/...`.

### 1e. Copy the Cookie

In the right-hand panel, click the **Headers** tab and scroll down to **Request Headers**.

Find the `cookie:` row. Click on the value and select all (`Ctrl+A`), then copy it (`Ctrl+C`).

This is your **FPL_COOKIE** value.

### 1f. Copy the Bearer Token

In the same **Request Headers** section, find the `x-api-authorization:` row.

The value starts with `Bearer eyJ...`. Copy the entire value including the word `Bearer`.

This is your **FPL_TOKEN** value.

---

## Step 2 — Open and configure the notebook

### 2a. Open a terminal / command prompt

Navigate to the repo folder:

```
cd path\to\FPL-Draft-App
```

### 2b. Launch Jupyter

```
jupyter notebook
```

Your browser will open. Click on **FPL_Draft_Data.ipynb**.

### 2c. Paste your credentials into Cell 1

Find these two lines near the top of Cell 1:

```python
FPL_COOKIE = ""
FPL_TOKEN  = ""
```

Paste your values inside the quotes:

```python
FPL_COOKIE = "paste your cookie string here"
FPL_TOKEN  = "Bearer eyJ... paste your full token here"
```

> **Important:** Do not save/commit the notebook while credentials are filled in.
> The token expires in ~8 hours so they will be useless to anyone who finds them,
> but it is still good practice to clear them before committing (Step 4 covers this).

---

## Step 3 — Run the notebook

At the top of the notebook click **Kernel → Restart & Run All** (or use the ▶▶ button).

The notebook will:
1. Authenticate with the FPL Draft API using your credentials
2. Fetch league, match, player, and transfer data across all 38 gameweeks
3. Export 6 JSON files and 5 CSV files to the `data/` folder

When it finishes you will see:

```
Data exported to data/ (6 JSON files + 5 CSV files)
```

The files created in `data/` are:

| File | Used by |
|------|---------|
| `gw_and_team.json` | HTML app |
| `matches.json` | HTML app |
| `player_scores.json` | HTML app |
| `transfers.json` | HTML app |
| `draft_picks.json` | HTML app |
| `bootstrap.json` | HTML app |
| `*.csv` | Reference / backup |

---

## Step 4 — Clear credentials before committing

Before touching Git, clear your credentials from Cell 1:

```python
FPL_COOKIE = ""
FPL_TOKEN  = ""
```

Then save the notebook (`Ctrl+S`).

---

## Step 5 — Commit and push to GitHub

Open a terminal in the repo root and run:

```bash
# Stage the updated data files and notebook
git add data/
git add FPL_Draft_Data.ipynb

# Commit with a descriptive message
git commit -m "GW{N} data refresh"

# Push to main
git push origin main
```

Replace `{N}` with the gameweek number, e.g. `GW31 data refresh`.

---

## Step 6 — Netlify auto-deploys

Netlify is connected to this GitHub repo and will automatically detect the push and redeploy the site within 1–2 minutes. No manual action required.

You can check the deploy status at [app.netlify.com](https://app.netlify.com).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `403 Forbidden` from API | Your credentials have expired — repeat Step 1 |
| `401 Unauthorized` | Token is wrong or missing the `Bearer ` prefix |
| Notebook hangs on player prices | The FPL.com prices API is slow (fetches ~600 players) — leave it running |
| JSON file not found on site | Check that `data/*.json` files were committed and pushed |
| Site still showing old data | Wait 2 minutes for Netlify to redeploy, then hard-refresh (`Ctrl+Shift+R`) |
