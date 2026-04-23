# How to Update FPL Draft Data — Step by Step

This guide assumes you are on **Windows** and have Python and Jupyter already installed.

---

## Part 1 — Get your FPL Cookie and Bearer Token from your browser

You need two pieces of information from your browser each time you run the notebook.
They expire after a few hours so you must repeat this every session.

### Step 1 — Log in to FPL Draft

Open **Google Chrome** or **Microsoft Edge** and go to:

```
https://draft.premierleague.com
```

Log in with your FPL account. Once logged in, click on your league so the page loads some data.

---

### Step 2 — Open Developer Tools

Press the **F12** key on your keyboard.

A panel will open on the right side (or bottom) of your browser. This is called Developer Tools.

---

### Step 3 — Go to the Network tab

At the top of the Developer Tools panel, you will see a row of tabs:
**Elements, Console, Sources, Network, ...**

Click on **Network**.

---

### Step 4 — Reload the page to capture requests

With the Network tab open, press **F5** (or Ctrl+R) to reload the page.

You will see a list of requests appear in the panel. These are all the calls the page makes to load data.

---

### Step 5 — Find a Draft API request

In the **filter box** near the top of the Network panel (it may say "Filter" with a magnifying glass icon), type:

```
draft.premierleague.com
```

The list will shrink to only show FPL Draft API calls. If the list is empty, click around the page (e.g. click on your squad or standings) to trigger more requests.

Click on **any one** of the requests in the list to select it.

---

### Step 6 — Copy your Cookie

On the right side of the Network panel, click the **Headers** tab (if not already selected).

Scroll down until you see a section called **Request Headers**.

Find the row that starts with **cookie:**

The value is a long string of text. Click anywhere on that long value to select it, then press **Ctrl+A** to select all of it, then **Ctrl+C** to copy it.

> This is your **FPL_COOKIE**. Keep it copied — you will paste it shortly.

---

### Step 7 — Copy your Bearer Token

In the same **Request Headers** section, scroll until you find a row that starts with:

```
x-api-authorization:
```

The value starts with `Bearer eyJ...` and is a very long string.

Click on it, select all (**Ctrl+A**), and copy it (**Ctrl+C**).

> This is your **FPL_TOKEN**. You will paste this separately in a moment.

---

## Part 2 — Find your repo folder on your computer

Before opening a terminal, you need to know where the FPL-Draft-App folder is saved on your computer.

### Step 8 — Find the folder

Open **File Explorer** (the yellow folder icon in your taskbar, or press **Windows key + E**).

Look in these common locations:
- `C:\Users\YourName\Documents\FPL-Draft-App`
- `C:\Users\YourName\FPL-Draft-App`
- `C:\Users\YourName\Desktop\FPL-Draft-App`

If you cannot find it, press **Ctrl+F** in File Explorer and search for `FPL-Draft-App`.

Once you find the folder, **click on the address bar at the top of File Explorer** (the bar that shows the path like `C:\Users\...`). The full path will be highlighted in blue — note it down, e.g.:

```
C:\Users\Sam\Documents\FPL-Draft-App
```

---

## Part 3 — Open a terminal and launch Jupyter

### Step 9 — Open a Command Prompt

Press the **Windows key** on your keyboard, type:

```
cmd
```

Click on **Command Prompt** when it appears.

A black window will open with a flashing cursor.

---

### Step 10 — Navigate to your repo folder

In the Command Prompt, type `cd` followed by a space, then paste the full path you found in Step 8. For example:

```
cd C:\Users\Sam\Documents\FPL-Draft-App
```

Press **Enter**.

The prompt should change to show your folder path. For example:

```
C:\Users\Sam\Documents\FPL-Draft-App>
```

> **Tip:** You can drag the FPL-Draft-App folder from File Explorer directly into the Command Prompt window after typing `cd ` — it will paste the path for you automatically.

---

### Step 11 — Start Jupyter Notebook

In the Command Prompt, type:

```
jupyter notebook
```

Press **Enter**.

After a few seconds, your web browser will open automatically showing the Jupyter file browser. You will see a list of files including `FPL_Draft_Data.ipynb`.

> If the browser does not open automatically, look in the Command Prompt for a line that says something like `http://localhost:8888/...` and paste that URL into your browser.

---

## Part 4 — Paste your credentials into the notebook

### Step 12 — Open the notebook

In the Jupyter file browser, click on **FPL_Draft_Data.ipynb**.

The notebook will open in a new browser tab.

---

### Step 13 — Find Cell 1

The first code cell (Cell 1) contains lines that look like this near the top:

```python
FPL_COOKIE = ""

FPL_TOKEN  = ""
```

Click on the cell to select it, then click again between the two `"` quote marks on the `FPL_COOKIE` line so your cursor is inside them.

---

### Step 14 — Paste your Cookie

Place your cursor between the quotes on the `FPL_COOKIE` line:

```python
FPL_COOKIE = "|"   ← cursor goes here
```

Press **Ctrl+V** to paste the cookie string you copied in Step 6.

It will look something like:

```python
FPL_COOKIE = "_ga=GA1.1.xxx; datadome=abc123..."
```

---

### Step 15 — Paste your Bearer Token

Now click between the quotes on the `FPL_TOKEN` line and paste the token you copied in Step 7:

```python
FPL_TOKEN  = "Bearer eyJhbGciOiJSUzI1NiIs..."
```

Make sure the value still starts with `Bearer ` (with a space after it).

---

## Part 5 — Run the notebook

### Step 16 — Run all cells

At the top of the notebook, click the **Kernel** menu, then click **Restart & Run All**.

A dialog box will ask "Are you sure?" — click **Restart and Run All Cells**.

The notebook will now run through all the cells from top to bottom. You will see output appearing below each cell as it runs.

> **This takes 10–20 minutes** because it fetches data for every player and every gameweek. The Command Prompt window must stay open the whole time.

When it finishes, you will see this message at the bottom:

```
Data exported to data/ (6 JSON files + 5 CSV files)
```

---

## Part 6 — Clear credentials and push to GitHub

### Step 17 — Clear your credentials

**Before saving or committing**, go back to Cell 1 and delete the values you pasted, leaving empty strings:

```python
FPL_COOKIE = ""

FPL_TOKEN  = ""
```

Save the notebook with **Ctrl+S**.

---

### Step 18 — Open Git Bash or GitHub Desktop

If you have **GitHub Desktop** installed:
1. Open GitHub Desktop
2. It will show the changed files (`data/` folder and the notebook)
3. Write a summary like `GW32 data refresh`
4. Click **Commit to main**
5. Click **Push origin**

If you prefer the **command line**, go back to your Command Prompt and run:

```
git add data\
git add FPL_Draft_Data.ipynb
git commit -m "GW32 data refresh"
git push origin main
```

---

### Step 19 — Wait for Netlify to redeploy

Once pushed, Netlify will automatically detect the update and redeploy the website within 1–2 minutes.

Open your Netlify site URL and do a hard refresh (**Ctrl+Shift+R**) to see the updated data.

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| `403 Forbidden` errors in the notebook | Your credentials have expired — go back to Step 1 and get fresh ones |
| `jupyter` is not recognised in Command Prompt | Run `pip install notebook` first, then try again |
| Browser doesn't open after `jupyter notebook` | Look in the Command Prompt for a `localhost:8888` URL and open it manually |
| Can't find the `x-api-authorization` header | Make sure you are on the Network tab and have clicked on a `draft.premierleague.com` request (not a Google or CDN request) |
| Notebook finishes but no data folder appears | Check the Command Prompt — there may be an error message in red |
| Site still shows old data after pushing | Wait 2 minutes then press Ctrl+Shift+R to hard-refresh the page |
