# 🧱 The Brick Bench

A phone-first LEGO collection and build-time tracker. Add a set by typing the
number off the box, start a stopwatch when you sit down to build, snap progress
photos as you go, and watch the hours and piece counts add up.

Built with [Streamlit](https://streamlit.io). The whole app is one file:
[`brick_bench.py`](./brick_bench.py).

---

## For the person using it

**Adding a set** — tap **➕ Add a LEGO set**, type the number printed on the box
(like `10276`) or the set's name (like `Millennium Falcon`), and pick it from
the list. The name, theme, piece count, year, minifigure count and official
picture all fill themselves in. Want it but don't own it yet? Tap **⭐ Wishlist**
instead — and hit **🛒 I bought it!** when you get it.

**Timing a build** — open a set and hit **▶️ Start build session**. The clock
keeps running even if you close the app or your phone locks — come back later
and hit **⏹️ Stop & save**. Forgot to stop? A paused session saves itself after
an hour, and you can always correct the minutes afterwards.

**Finishing** — when the last brick clicks in, hit **🎉 I finished it!** on the
set's Timer tab. Balloons.

**Photos** — snap progress pictures from the **📸 Photos** tab, or right after a
session when the app offers. They appear in the set's **📖 Journal** alongside
your notes, newest first.

**Finding things** — the search box above your sets matches names, set numbers
and themes as you type.

**Statuses** — 📦 Unbuilt · 🔧 Building · ✅ Built · ⏸️ On Hold (and ⭐ Wishlist
for sets you don't own yet).

**Is my stuff safe?** — every change is backed up automatically. If a backup
ever fails, an orange warning appears at the top with a **Retry backup** button.
No warning means it's saved. The bottom of the **📊 Stats** page can also hand
you an Excel copy of everything.

---

## For the person setting it up

### Run it locally

```bash
pip install -r requirements.txt
streamlit run brick_bench.py
```

It opens at http://localhost:8501 and works with no configuration at all —
you just type set details in by hand and nothing is backed up off the machine.
The secrets below are what turn on the good parts.

### Secrets

Settings live in `.streamlit/secrets.toml` locally, or under
*Manage app → Settings → Secrets* on Streamlit Community Cloud. That file is
gitignored — never commit tokens.

```toml
# Backup + photo storage (strongly recommended)
GITHUB_TOKEN = "ghp_..."          # fine-grained PAT with Contents: read & write
GITHUB_REPO  = "username/reponame"

# Automatic set lookup (recommended — this is what makes adding sets one-tap)
REBRICKABLE_API_KEY = "..."

# Simple PIN lock (recommended — the app URL is public without it)
APP_PIN = "1234"
```

**`GITHUB_TOKEN` / `GITHUB_REPO`** — the app has no server database. It keeps
its data in a SQLite file, `lego_db.db`, and pushes that file to this repo after
every change; build photos go to `photos/` the same way. Without these two, the
app still runs, but the container it runs on is disposable — restarts lose
everything. Create the token at *GitHub → Settings → Developer settings →
Personal access tokens → Fine-grained tokens*, scoped to just this repository
with **Contents: read & write**.

**`REBRICKABLE_API_KEY`** — free, takes about two minutes:

1. Make an account at [rebrickable.com](https://rebrickable.com).
2. Go to *Account → Settings → API* and generate a key.
3. Paste it in as `REBRICKABLE_API_KEY`.

That's what powers the set search — name, theme, piece count, year, minifig
count and set picture, all from the number on the box. Without it, the add-set
form falls back to typing the details in by hand, and everything else in the app
works exactly the same.

**`APP_PIN`** — any string; whoever opens the app must type it once. After a
correct entry the PIN rides along in the page URL, so bookmarking the unlocked
page means never typing it again on that device. It's a garden gate, not a bank
vault — it keeps strangers who stumble on the URL from scribbling on the
collection, nothing more. Leave it unset for no lock.

### Deploying to Streamlit Community Cloud

1. Point a new app at this repo, main file `brick_bench.py`.
2. Add the secrets above under *Manage app → Settings → Secrets*.
3. Free apps sleep after ~12 hours without visitors, and cold starts take a
   minute or two. The [keep-awake workflow](.github/workflows/keep-awake.yml)
   visits the app every 2 hours to prevent that — set a repository variable
   named `APP_URL` to your app's URL (*Settings → Secrets and variables →
   Actions → Variables*) to switch it on. If you set `APP_PIN`, include it in
   the variable so the pinger gets past the lock:
   `https://your-app.streamlit.app/?key=YOURPIN`

### What's stored where

| | |
|---|---|
| `lego_db.db` | SQLite: sets, build sessions, photo records, the running timer |
| `photos/` | Uploaded build photos |
| `brick_bench.py` | The entire app |

Tables: `Sets` (set_num, name, theme, pieces, year, minifigs, image_url, status,
rating, notes, last_worked, price_paid), `Build_Logs`, `Photos`, `Active_Timer`,
`App_State`. Wishlist sets are rows with `status='Wishlist'`.

---

*LEGO® is a trademark of the LEGO Group, which does not sponsor, authorize or
endorse this project. Set data comes from [Rebrickable](https://rebrickable.com).*
