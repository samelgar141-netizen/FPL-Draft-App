# How to Update FPL Draft Data

Data is now refreshed **automatically every Tuesday at 11:00 UTC** via GitHub Actions.
No laptop, no Jupyter, no manual steps required week to week.

The app is hosted at:
```
https://samelgar141-netizen.github.io/FPL-Draft-App/
```

---

## Automatic weekly refresh (normal operation)

Every Tuesday morning GitHub Actions runs the `refresh_data.py` script, commits the updated data files, and pushes them to the repo. The website updates within a minute or two.

You will receive a **GitHub email notification** if the run fails.

---

## Manual trigger (e.g. after a mid-week gameweek)

1. Go to the repo on GitHub
2. Click the **Actions** tab
3. Click **Refresh FPL Draft Data** in the left sidebar
4. Click **Run workflow → Run workflow**

The run takes about 3 minutes. The site updates automatically once it completes.

---

## When the cookie expires (a few times per season)

The FPL cookie stored in GitHub Secrets expires every few months. When it does, the automated run will fail and you will get an email from GitHub.

### Step 1 — Get a fresh cookie from your browser

1. Open Chrome or Edge and go to `https://draft.premierleague.com`
2. Log in and click into your league
3. Press **F12** to open Developer Tools
4. Click the **Network** tab
5. Press **F5** to reload the page
6. In the filter box type `draft.premierleague.com`
7. Click on any request in the list
8. Click **Headers** on the right, scroll to **Request Headers**
9. Find the `cookie:` row — click it, select all (**Ctrl+A**), copy (**Ctrl+C**)

### Step 2 — Update the GitHub Secret

1. Go to the repo on GitHub → **Settings**
2. In the left sidebar: **Secrets and variables → Actions**
3. Click the **pencil icon** next to `FPL_COOKIE`
4. Paste your new cookie value and click **Save**

### Step 3 — Re-run the workflow

Go to **Actions → Refresh FPL Draft Data → Re-run jobs** on the failed run,
or trigger a fresh run using the manual trigger steps above.

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| Automated run fails with `401` errors on Step 1 or 2 | Cookie has expired — follow the cookie update steps above |
| Run shows `401` only on GW6+ | Normal — GW6 hasn't been played yet, not an error |
| Run shows `using cached draft_picks.json` | Fine — draft picks never change after the draft |
| Run shows `using cached transfers.json` | Cookie may be stale — update it if transfers look out of date in the app |
| Site still shows old data after a successful run | Wait 2 minutes then press **Ctrl+Shift+R** to hard-refresh |

---

## If you need to run the notebook manually (emergency only)

The original `FPL_Draft_Data.ipynb` notebook still works if you need it.
See the old version of this file in git history for the full step-by-step instructions.
