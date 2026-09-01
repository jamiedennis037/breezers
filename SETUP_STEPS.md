# Upcoming Breezers — GitHub setup (one time, ~15 minutes)

Everything runs in the browser. No command line needed.

When you're done, colleagues open ONE link and see today + tomorrow's breezers,
always current. It refreshes itself at 08:05 and 13:00 UK time — your laptop can
be off.

---

## What's in this folder (upload all of it)

- `index.html` .................. the dashboard (the page people open)
- `scrape.py` ................... the scraper that runs in the cloud
- `breezers_db.json` ........... the breeze-up database (all 5 sales)
- `breezer_matches.json` ....... starter data so the page isn't blank on day 1
- `.github/workflows/refresh.yml` the schedule (runs the scrape twice a day)
- `.gitignore` ................. keeps local files (.env, csv) out of GitHub

DO NOT upload your `.env` file or the sale CSVs. The .gitignore blocks them,
but just don't drag them in.

---

## STEP 1 — Create a GitHub account (skip if you have one)
1. Go to https://github.com
2. Click **Sign up**, follow the prompts. Free account is fine.

## STEP 2 — Create the repository
1. Click the **+** (top right) → **New repository**.
2. Repository name: `breezers` (or anything).
3. Leave it **Public** (there's no private data here).
4. Click **Create repository**.

## STEP 3 — Upload the files
1. On the new repo page, click **uploading an existing file**
   (or the **Add file → Upload files** button).
2. Open this `github_deploy` folder on your PC.
3. Select ALL the contents and drag them into the browser.
   - Make sure the `.github` folder comes too (it holds the schedule).
   - If drag-and-drop misses the `.github` folder, see STEP 3b below.
4. Click **Commit changes**.

### STEP 3b — If the `.github/workflows` folder didn't upload
GitHub sometimes hides dotfolders in drag-and-drop. Easiest fix:
1. In the repo, click **Add file → Create new file**.
2. In the name box type exactly: `.github/workflows/refresh.yml`
   (typing the slashes creates the folders automatically).
3. Open `refresh.yml` from this folder in Notepad, copy everything,
   paste it into the GitHub editor, click **Commit changes**.

## STEP 4 — Add the two API keys as secrets
1. In the repo: **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
   - Name: `RP_API_KEY`  →  Value: (paste the RP_API_KEY from your .env)
   - Click **Add secret**.
3. Click **New repository secret** again.
   - Name: `RP_JWT_KEY`  →  Value: (paste the RP_JWT_KEY from your .env)
   - Click **Add secret**.
(These stay hidden. They are never shown on the page or in the code.)

## STEP 5 — Turn on the website (GitHub Pages)
1. In the repo: **Settings** → **Pages**.
2. Under **Source**, choose **Deploy from a branch**.
3. Branch: `main`, folder: `/ (root)`. Click **Save**.
4. Wait ~1 minute. The page URL appears at the top of the Pages screen,
   like: `https://YOURNAME.github.io/breezers/`
5. That URL is what you share with colleagues.

## STEP 6 — Run it once now (so it's fresh immediately)
1. In the repo: **Actions** tab.
2. Click **Refresh Breezers** on the left.
3. Click **Run workflow** → **Run workflow**.
4. Wait ~1 minute; a green tick means it worked. The page now shows today+tomorrow.

---

## Done. From now on:
- It refreshes automatically at 08:05 and 13:00 UK time.
- Colleagues just open the Pages URL — no VPN, no shared drive, your laptop off.
- To force a refresh any time: Actions → Refresh Breezers → Run workflow.

## When a new breeze-up season starts (once a year):
- Edit `scrape.py`, change `EXPECTED_FOALING_YEAR` to the new crop's foaling year.
- Replace `breezers_db.json` with the new season's database.
(Ask for help and this can be handed to you ready-made.)
