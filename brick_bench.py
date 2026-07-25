import streamlit as st
import sqlite3
import pandas as pd
import requests
import base64
import io
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG & THEME
# ─────────────────────────────────────────────
APP_NAME = "The Brick Bench"
DB_FILE  = "lego_db.db"          # own database — never shared with any other tracker

st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🧱")

st.markdown("""
<style>
/* ── Theme: charcoal + LEGO yellow (all colors defined here) ── */
:root {
    --bg:           #14161b;   /* deep charcoal */
    --surface:      #1d212a;   /* cards, buttons, inputs */
    --surface2:     #262b36;   /* zero-intensity heatmap, hover */
    --border:       #333a48;   /* cool gray lines */
    --accent:       #ffd400;   /* LEGO yellow — text & lines on charcoal */
    --accent-deep:  #c9a600;   /* darker yellow — fills & borders */
    --accent-hover: #ffe45c;
    --brick-red:    #e3000b;   /* classic brick red — used sparingly */
    --building:     #3d8ee0;   /* Building */
    --built:        #4caf50;   /* Built */
    --text:         #e9eaee;
    --muted:        #8b90a0;
}

/* ── Dark base ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
[data-testid="stSidebar"] { background-color: var(--surface) !important; }
[data-testid="stHeader"]  { background-color: var(--bg) !important; }

/* ── Phone-first density ── */
.block-container { padding-top: 2.2rem !important; padding-bottom: 2rem !important; }
hr { border-color: var(--border) !important; margin: 0.6rem 0 !important; }
[data-testid="stToolbar"] { display: none !important; }  /* hide Deploy/menu chrome */

/* ── Headings ── */
h1, h2, h3, h4 {
    color: var(--accent) !important;
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    font-weight: 800;
    letter-spacing: 0.5px;
}
h2 { font-size: 1.35rem !important; }

/* ── One-line header widgets ── */
.brand-line { color: var(--accent);
              font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
              font-size: 1.15rem; font-weight: 800; letter-spacing: 0.5px; margin: 0; }
.stats-line { color: var(--muted); font-size: 0.8rem; margin: 2px 0 8px 0; }
.stats-line b { color: var(--accent); font-weight: 700; }

/* ── Keyed nowrap containers: keep their columns on ONE row on phones ──
   Streamlit stacks columns below ~640px; for containers whose key starts
   with "nowrap" we keep the row layout (nav bar, back row, log rows). */
div[class*="st-key-nowrap"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.4rem !important;
}
div[class*="st-key-nowrap"] [data-testid="stColumn"],
div[class*="st-key-nowrap"] [data-testid="column"] {
    width: auto !important;
    min-width: 0 !important;
}
div[class*="st-key-nowrap"] .stButton > button {
    padding: 0.25rem 0.4rem !important;
    font-size: 0.85rem !important;
}

/* ── Metric tiles (Stats page) ── */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
[data-testid="stMetricValue"] { color: var(--accent) !important; font-size: 1.6rem; font-weight: 700; }

/* ── Buttons ── */
.stButton > button {
    background: var(--surface) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent-deep) !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--accent-deep) !important;
    color: #14161b !important;
}
/* Primary buttons — solid LEGO yellow */
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #14161b !important;
    border: 1px solid var(--accent) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    color: #14161b !important;
}

/* ── Inputs ── */
input, textarea, [data-baseweb="select"] {
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 6px !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"], [data-testid="stTabs"] [role="tab"] p {
    color: var(--muted) !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p {
    color: var(--accent) !important;
}
[data-baseweb="tab-highlight"] { background-color: var(--accent) !important; }
[data-baseweb="tab-border"]    { background-color: var(--border) !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Set cards ── */
.set-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: border-color 0.2s, background 0.2s;
}
.set-card:hover { border-color: var(--accent); background: var(--surface2); }
.set-card-thumb {
    width: 58px; height: 58px; flex: 0 0 58px;
    object-fit: contain;
    background: #fff;
    border-radius: 8px;
    padding: 3px;
}
.set-card-body { min-width: 0; }
.set-card-title { color: var(--text); font-size: 1rem; font-weight: 600; margin-bottom: 3px; }
.set-card-meta  { color: var(--muted); font-size: 0.78rem; }

/* ── Currently building banner ── */
.building-banner {
    background: linear-gradient(135deg, #1a1d24, #2a2413);
    border: 2px solid var(--accent-deep);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.building-banner-thumb {
    width: 66px; height: 66px; flex: 0 0 66px;
    object-fit: contain; background: #fff; border-radius: 8px; padding: 3px;
}
.building-banner-title { color: var(--accent); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 6px; }
.building-banner-name  { color: #fff; font-size: 1.1rem; font-weight: 700; }

/* ── Stopwatch display ── */
.stopwatch {
    background: #10131a;
    border: 2px solid var(--accent-deep);
    border-radius: 16px;
    text-align: center;
    padding: 26px;
    margin: 12px 0;
}
.stopwatch-time {
    font-size: 2.6rem;
    font-weight: 700;
    color: var(--accent);
    font-family: 'Courier New', monospace;
    letter-spacing: 2px;
    white-space: nowrap;
}
.stopwatch-label { color: #7a7f8d; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; margin-top: 8px; }

/* ── Stats cards / chips ── */
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    margin-bottom: 12px;
}
.stat-card-value { color: var(--accent); font-size: 2rem; font-weight: 700; }
.stat-card-label { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
.stat-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }
.stat-chip {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    flex: 1 1 28%;
    text-align: center;
}
.stat-chip-value { color: var(--accent); font-size: 1.15rem; font-weight: 700; }
.stat-chip-label { color: var(--muted); font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }

/* ── Journal timeline ── */
.journal-entry {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-deep);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.journal-date { color: var(--accent); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; }
.journal-body { color: var(--text); font-size: 0.9rem; margin-top: 3px; }

/* ── Search results (LEGO database lookup) ── */
.search-hit-name { color: var(--text); font-size: 0.95rem; font-weight: 600; }
.search-hit-meta { color: var(--muted); font-size: 0.75rem; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 8px !important; }

/* ── Success/info/warning ── */
[data-testid="stAlert"] { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECRETS
# ─────────────────────────────────────────────
def secret(key, default=""):
    """Read a secret without ever raising. st.secrets.get() itself throws
    StreamlitSecretNotFoundError when there is no secrets file at all — which
    is the normal state on a fresh checkout — so every read goes through here."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

# ─────────────────────────────────────────────
# GITHUB HELPERS
# ─────────────────────────────────────────────
def gh_headers():
    token = secret("GITHUB_TOKEN")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def gh_repo():
    return secret("GITHUB_REPO")

def backup_configured():
    """True when we have somewhere to back the database up to."""
    return bool(gh_repo() and secret("GITHUB_TOKEN"))

def pull_db_from_github():
    try:
        repo = gh_repo()
        if not repo: return False
        url = f"https://api.github.com/repos/{repo}/contents/{DB_FILE}"
        r = requests.get(url, headers=gh_headers(), timeout=15)
        if r.status_code == 200:
            db_bytes = base64.b64decode(r.json()["content"])
            with open(DB_FILE, "wb") as f:
                f.write(db_bytes)
            return True
        return False
    except Exception:
        return False

def push_db_to_github():
    try:
        repo = gh_repo()
        if not repo: return False
        with open(DB_FILE, "rb") as f:
            db_bytes = f.read()
        b64 = base64.b64encode(db_bytes).decode("utf-8")
        url = f"https://api.github.com/repos/{repo}/contents/{DB_FILE}"
        r   = requests.get(url, headers=gh_headers(), timeout=10)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {"message": f"Update database {datetime.now().strftime('%Y-%m-%d %H:%M')}", "content": b64}
        if sha: payload["sha"] = sha
        r2 = requests.put(url, headers=gh_headers(), json=payload, timeout=30)
        return r2.status_code in (200, 201)
    except Exception:
        return False

def upload_to_github(image_bytes, filename):
    try:
        repo = gh_repo()
        if not repo: return None, "GITHUB_REPO not set."
        path    = f"photos/{filename}"
        api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
        check   = requests.get(api_url, headers=gh_headers(), timeout=10)
        sha     = check.json().get("sha") if check.status_code == 200 else None
        b64     = base64.b64encode(image_bytes).decode("utf-8")
        payload = {"message": f"Add photo: {filename}", "content": b64}
        if sha: payload["sha"] = sha
        response = requests.put(api_url, headers=gh_headers(), json=payload, timeout=20)
        if response.status_code in (200, 201):
            return f"https://raw.githubusercontent.com/{repo}/main/{path}", None
        return None, response.json().get("message", "Upload failed.")
    except Exception as e:
        return None, str(e)

# ─────────────────────────────────────────────
# STARTUP — pull DB from GitHub once per SERVER boot, not per browser visit.
# This server is the only writer, so once it has the DB its local copy is
# always at least as new as GitHub's — re-pulling on every open just made
# each visit slower (and could clobber local changes whose push had failed).
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner="Opening your collection...")
def _startup_pull():
    pull_db_from_github()
    return True

_startup_pull()

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c    = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS Sets
             (set_num     TEXT PRIMARY KEY,
              name        TEXT,
              theme       TEXT,
              pieces      INTEGER,
              year        INTEGER,
              minifigs    INTEGER,
              image_url   TEXT,
              status      TEXT DEFAULT 'Unbuilt',
              rating      INTEGER DEFAULT 0,
              notes       TEXT,
              last_worked TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS Build_Logs
             (log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
              set_num     TEXT,
              start_time  TEXT,
              duration    REAL,
              notes       TEXT,
              is_estimate INTEGER DEFAULT 0)''')

c.execute('''CREATE TABLE IF NOT EXISTS Photos
             (photo_id    INTEGER PRIMARY KEY AUTOINCREMENT,
              set_num     TEXT,
              url         TEXT,
              caption     TEXT,
              uploaded_at TEXT)''')

# Active timer table — persists across browser sessions
c.execute('''CREATE TABLE IF NOT EXISTS Active_Timer
             (id          INTEGER PRIMARY KEY,
              set_num     TEXT,
              start_time  TEXT,
              paused_at   TEXT,
              paused_secs REAL DEFAULT 0)''')

# Small key-value store for app state (e.g. last opened set)
c.execute('''CREATE TABLE IF NOT EXISTS App_State
             (key   TEXT PRIMARY KEY,
              value TEXT)''')

conn.commit()

def get_app_state(key):
    row = c.execute("SELECT value FROM App_State WHERE key=?", (key,)).fetchone()
    return row[0] if row else None

def set_app_state(key, value):
    # Local commit only — not worth a GitHub commit per navigation. The value
    # becomes durable whenever the next real save pushes the DB.
    if get_app_state(key) != value:
        c.execute("INSERT OR REPLACE INTO App_State (key, value) VALUES (?,?)", (key, value))
        conn.commit()

# ─────────────────────────────────────────────
# SAVE HELPER
# ─────────────────────────────────────────────
def save():
    """Commit locally, then push to GitHub. Returns True only if the remote
    push succeeded — local commits alone are NOT safe, because the container
    is ephemeral and the only durable copy of the DB lives on GitHub.

    When no backup is configured at all there is nothing to push to, so a local
    commit is the whole story and counts as success — otherwise every single
    action would raise a sync alarm the user can do nothing about. The missing
    backup is surfaced once, under the header, instead."""
    conn.commit()
    if not backup_configured():
        return True
    return push_db_to_github()

# ─────────────────────────────────────────────
# SMALL HELPERS (used by the lookup code below, so defined first)
# ─────────────────────────────────────────────
def safe_int(val):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)): return None
        return int(val)
    except (ValueError, TypeError):
        return None

def safe_float(val):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)): return None
        return float(val)
    except (ValueError, TypeError):
        return None

def fmt_seconds(secs):
    secs = int(secs)
    h, rem = divmod(secs, 3600)
    m, s   = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"

def fmt_pieces(pieces):
    n = safe_int(pieces)
    return f"{n:,} pieces" if n else "— pieces"

# ─────────────────────────────────────────────
# LEGO SET DATABASE (Rebrickable API — optional, needs a free key)
# ─────────────────────────────────────────────
# With REBRICKABLE_API_KEY set, typing a set number or a name fills in the
# name, theme, piece count, year, minifig count and official set picture
# automatically. Without a key everything still works — you just type the
# details in by hand.
RB_BASE = "https://rebrickable.com/api/v3/lego"

def rb_key():
    return secret("REBRICKABLE_API_KEY")

def rb_enabled():
    return bool(rb_key())

def _rb_get(path, params=None):
    """GET a Rebrickable endpoint. Returns (json, error_message).
    'not_found' is returned as the error for a clean 404 so callers can
    tell "no such set" apart from "the lookup broke"."""
    key = rb_key()
    if not key:
        return None, "No Rebrickable API key configured."
    try:
        r = requests.get(
            f"{RB_BASE}{path}",
            headers={"Authorization": f"key {key}", "Accept": "application/json"},
            params=params or {}, timeout=15)
        if r.status_code == 200:
            return r.json(), None
        if r.status_code == 404:
            return None, "not_found"
        if r.status_code in (401, 403):
            return None, "The LEGO database rejected our key — check REBRICKABLE_API_KEY in the app secrets."
        if r.status_code == 429:
            return None, "The LEGO database is rate-limiting us. Wait a few seconds and try again."
        return None, f"The LEGO database returned HTTP {r.status_code}."
    except Exception as e:
        return None, f"Couldn't reach the LEGO database ({e})."

def normalize_set_num(raw):
    """Set numbers in the catalog carry a variant suffix: 10276 → 10276-1.
    People type the number off the box, so add the suffix when it's missing."""
    s = (raw or "").strip().upper().replace(" ", "")
    if not s:
        return ""
    return s if "-" in s else f"{s}-1"

@st.cache_data(ttl=86400, show_spinner=False)
def rb_theme_name(theme_id):
    """Theme name for an id, as 'Parent > Child' when it's a sub-theme
    (e.g. 'Star Wars > Ultimate Collector Series'). Cached for a day."""
    if not theme_id:
        return None
    data, err = _rb_get(f"/themes/{theme_id}/")
    if err or not data:
        return None
    name = data.get("name")
    parent_id = data.get("parent_id")
    if parent_id:
        parent, perr = _rb_get(f"/themes/{parent_id}/")
        if not perr and parent and parent.get("name"):
            return f"{parent['name']} > {name}"
    return name

@st.cache_data(ttl=86400, show_spinner=False)
def rb_minifig_count(set_num):
    """Total minifigures in a set (sum of quantities). None if unknown."""
    data, err = _rb_get(f"/sets/{set_num}/minifigs/", {"page_size": 200})
    if err or not data:
        return None
    try:
        return int(sum(m.get("quantity") or 0 for m in data.get("results", [])))
    except Exception:
        return None

def _rb_row_to_set(row, with_extras=True):
    """Map a Rebrickable set record onto our columns. with_extras=False skips
    the theme and minifig lookups, which are one extra API call each."""
    return {
        "set_num":   row.get("set_num"),
        "name":      row.get("name"),
        "theme":     rb_theme_name(row.get("theme_id")) if with_extras else None,
        "pieces":    safe_int(row.get("num_parts")),
        "year":      safe_int(row.get("year")),
        "minifigs":  rb_minifig_count(row.get("set_num")) if with_extras else None,
        "image_url": row.get("set_img_url"),
    }

@st.cache_data(ttl=3600, show_spinner=False)
def rb_lookup_set(set_num):
    """Look up one set by number. Returns (set_dict, error_message)."""
    num = normalize_set_num(set_num)
    if not num:
        return None, "Enter a set number first."
    data, err = _rb_get(f"/sets/{num}/")
    if err == "not_found":
        return None, (f"No set numbered **{num}** in the LEGO database. "
                      "Double-check the number on the box, or add it by hand below.")
    if err:
        return None, err
    return _rb_row_to_set(data), None

@st.cache_data(ttl=3600, show_spinner=False)
def rb_search_sets(query, limit=12):
    """Search the LEGO database by name. Returns (list_of_sets, error_message).
    Kept light: no theme/minifig lookups per hit — those are filled in when a
    set is actually added."""
    q = (query or "").strip()
    if not q:
        return [], None
    data, err = _rb_get("/sets/", {"search": q, "page_size": limit, "ordering": "-year"})
    if err == "not_found":
        return [], None
    if err:
        return [], err
    return [_rb_row_to_set(r, with_extras=False) for r in data.get("results", [])], None

def add_set_to_collection(info):
    """Insert a set. Returns (ok, message). Never overwrites an existing row."""
    set_num = (info.get("set_num") or "").strip()
    if not set_num:
        return False, "That set has no set number."
    if c.execute("SELECT 1 FROM Sets WHERE set_num=?", (set_num,)).fetchone():
        return False, f"{set_num} is already in the collection."
    c.execute(
        """INSERT INTO Sets
           (set_num, name, theme, pieces, year, minifigs, image_url,
            status, rating, notes, last_worked)
           VALUES (?,?,?,?,?,?,?,?,0,'',?)""",
        (set_num, info.get("name") or set_num, info.get("theme"),
         safe_int(info.get("pieces")), safe_int(info.get("year")),
         safe_int(info.get("minifigs")), info.get("image_url"),
         'Unbuilt', str(datetime.now().date())))
    return True, f"Added {info.get('name') or set_num}!"

def refresh_set_from_rebrickable(set_num):
    """Re-pull catalog details for a set already in the collection. Only
    catalog fields are touched — status, rating, notes and build history
    belong to the owner and are left alone."""
    # A button labelled "Refresh" that hands back an hour-old cached answer
    # isn't a refresh, so drop the cached lookups first.
    rb_lookup_set.clear()
    rb_minifig_count.clear()
    info, err = rb_lookup_set(set_num)
    if err or not info:
        return False, err or "Lookup failed."
    c.execute(
        "UPDATE Sets SET name=?, theme=?, pieces=?, year=?, minifigs=?, image_url=? WHERE set_num=?",
        (info.get("name"), info.get("theme"), safe_int(info.get("pieces")),
         safe_int(info.get("year")), safe_int(info.get("minifigs")),
         info.get("image_url"), set_num))
    return True, "Set details refreshed."

# ─────────────────────────────────────────────
# GOOGLE SHEETS SYNC (optional, via Apps Script webhook)
# ─────────────────────────────────────────────
def gsheet_webhook():
    return secret("GSHEET_WEBHOOK_URL")

def _tab_payload(df):
    """Serialize a DataFrame to {columns, rows} with JSON-native types
    (to_json handles NaN -> null and numpy -> native, which raw .tolist() does not)."""
    obj = json.loads(df.to_json(orient="split"))
    return {"columns": obj["columns"], "rows": obj["data"]}

def sync_to_sheet():
    """Push a full snapshot of the collection to the user's Google Sheet via
    their Apps Script web app. Best-effort — returns (ok, message)."""
    url = gsheet_webhook()
    if not url:
        return False, "No GSHEET_WEBHOOK_URL configured."
    try:
        sets_df = pd.read_sql_query("SELECT * FROM Sets ORDER BY set_num", conn)
        logs    = pd.read_sql_query("SELECT * FROM Build_Logs ORDER BY set_num, start_time", conn)
        photos  = pd.read_sql_query("SELECT * FROM Photos ORDER BY set_num, uploaded_at", conn)
        payload = {
            "secret": secret("GSHEET_SECRET"),
            "tabs": {
                "Sets":       _tab_payload(sets_df),
                "Build Logs": _tab_payload(logs),
                "Photos":     _tab_payload(photos),
            },
        }
        # Apps Script 302-redirects to googleusercontent; requests follows it.
        r = requests.post(url, json=payload, timeout=15)
        try:
            ok_flag = (r.json().get("status") == "ok")
        except Exception:
            ok_flag = r.ok
        return (True, "Synced.") if ok_flag else (False, f"HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        return False, str(e)

# Paste-able Apps Script for the user's Google Sheet (shown on the Export page).
APPS_SCRIPT_CODE = '''const SECRET = "";  // optional: set a password, then put the same value in GSHEET_SECRET

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (SECRET && body.secret !== SECRET) {
      return ContentService
        .createTextOutput(JSON.stringify({status: "error", message: "bad secret"}))
        .setMimeType(ContentService.MimeType.JSON);
    }
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const tabs = body.tabs || {};
    Object.keys(tabs).forEach(function (name) {
      let sheet = ss.getSheetByName(name);
      if (!sheet) sheet = ss.insertSheet(name);
      sheet.clearContents();
      const cols = tabs[name].columns || [];
      const rows = tabs[name].rows || [];
      const data = [cols].concat(rows);
      if (cols.length) {
        sheet.getRange(1, 1, data.length, cols.length).setValues(data);
      }
    });
    return ContentService
      .createTextOutput(JSON.stringify({status: "ok"}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({status: "error", message: String(err)}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}'''

def save_and_report(success_msg="Saved!"):
    """Save and surface the real outcome to the user. On failure we never
    claim success — the change is local-only and at risk until it syncs."""
    with st.spinner("Saving..."):
        ok = save()
    if ok:
        st.session_state['unsynced'] = False
        if success_msg:
            st.success(success_msg)
        # Best-effort live mirror to the user's Google Sheet, only if a webhook
        # is configured. Never blocks or fails the save — just a toast either way.
        if gsheet_webhook():
            sok, smsg = sync_to_sheet()
            st.toast("📊 Google Sheet updated" if sok else f"⚠️ Sheet sync failed: {smsg}")
    else:
        st.session_state['unsynced'] = True
        st.error(
            "⚠️ Saved on this device, but the **backup didn't go through** — this "
            "change could be lost if the app restarts. Check your connection, "
            "then use **Retry backup** at the top of the screen.")
    return ok

# ─────────────────────────────────────────────
# QUERY HELPERS
# ─────────────────────────────────────────────
STATUS_OPTIONS = ['Unbuilt', 'Building', 'Built', 'On Hold']
STATUS_EMOJI   = {'Unbuilt': '📦', 'Building': '🔧', 'Built': '✅', 'On Hold': '⏸️'}
STATUS_COLOR   = {'Unbuilt': '#777f8f', 'Building': 'var(--building)',
                  'Built': 'var(--built)', 'On Hold': '#8b90a0'}

def get_all_sets():
    return pd.read_sql_query("SELECT * FROM Sets ORDER BY last_worked DESC NULLS LAST", conn)

def get_set(set_num):
    df = pd.read_sql_query("SELECT * FROM Sets WHERE set_num=?", conn, params=(set_num,))
    return df.iloc[0] if not df.empty else None

def get_logs(set_num):
    return pd.read_sql_query(
        "SELECT * FROM Build_Logs WHERE set_num=? ORDER BY start_time DESC", conn, params=(set_num,))

def get_photos(set_num):
    return pd.read_sql_query(
        "SELECT * FROM Photos WHERE set_num=? ORDER BY uploaded_at DESC", conn, params=(set_num,))

def total_time_seconds(set_num):
    logs = get_logs(set_num)
    return logs['duration'].sum() if not logs.empty else 0

def get_active_timer():
    row = c.execute(
        "SELECT set_num, start_time, paused_at, paused_secs FROM Active_Timer WHERE id=1").fetchone()
    return row if row else None

def timer_elapsed_seconds(t):
    """Active (non-paused) seconds for an Active_Timer row
    (set_num, start_time, paused_at, paused_secs). While paused, the clock
    is frozen at the moment the pause began."""
    end = datetime.fromisoformat(t[2]) if t[2] else datetime.now()
    return max(0.0, (end - datetime.fromisoformat(t[1])).total_seconds() - (t[3] or 0))

def timer_is_paused(t):
    return bool(t and t[2])

def set_active_timer(set_num, start_time_str):
    c.execute("DELETE FROM Active_Timer")
    c.execute("INSERT INTO Active_Timer (id, set_num, start_time) VALUES (1,?,?)",
              (set_num, start_time_str))
    ok = save()
    if not ok:
        st.session_state['unsynced'] = True
    return ok

def pause_active_timer():
    c.execute("UPDATE Active_Timer SET paused_at=? WHERE id=1 AND paused_at IS NULL",
              (datetime.now().isoformat(),))
    ok = save()
    if not ok:
        st.session_state['unsynced'] = True
    return ok

def resume_active_timer():
    t = get_active_timer()
    if t and t[2]:
        pause_len = (datetime.now() - datetime.fromisoformat(t[2])).total_seconds()
        c.execute("UPDATE Active_Timer SET paused_at=NULL, paused_secs=? WHERE id=1",
                  ((t[3] or 0) + pause_len,))
        ok = save()
        if not ok:
            st.session_state['unsynced'] = True
        return ok
    return True

def clear_active_timer():
    c.execute("DELETE FROM Active_Timer")
    ok = save()
    if not ok:
        st.session_state['unsynced'] = True
    return ok

def set_meta_line(row):
    """The one-line description under a set's name: number · theme · pieces …"""
    bits = [str(row['set_num'])]
    if row['theme']:                bits.append(str(row['theme']))
    if safe_int(row['pieces']):     bits.append(fmt_pieces(row['pieces']))
    if safe_int(row['year']):       bits.append(str(safe_int(row['year'])))
    mf = safe_int(row['minifigs'])
    if mf:                          bits.append(f"{mf} minifig{'s' if mf != 1 else ''}")
    return " &nbsp;·&nbsp; ".join(bits)

def thumb_html(url, css_class="set-card-thumb"):
    return f"<img src='{url}' class='{css_class}'>" if url else ""

# ── Auto-stop sessions paused too long ──
# Runs on every script execution (including the keep-awake pinger's visits
# every 2 hours), so a forgotten pause gets finalized even if the app is
# never opened. The session's active time is preserved; the pause isn't.
PAUSE_AUTO_STOP_MINS = 60
_t = get_active_timer()
if timer_is_paused(_t):
    _paused_for = (datetime.now() - datetime.fromisoformat(_t[2])).total_seconds()
    if _paused_for > PAUSE_AUTO_STOP_MINS * 60:
        _dur = timer_elapsed_seconds(_t)
        c.execute(
            "INSERT INTO Build_Logs (set_num, start_time, duration, notes) VALUES (?,?,?,?)",
            (_t[0], _t[1], _dur, "(auto-saved — paused over an hour)"))
        c.execute("UPDATE Sets SET last_worked=? WHERE set_num=?",
                  (str(datetime.now().date()), _t[0]))
        c.execute("DELETE FROM Active_Timer")
        save()
        st.toast(f"⏸️ Your paused session was auto-saved ({fmt_seconds(_dur)} of build time).")
del _t

# ─────────────────────────────────────────────
# NAVIGATION STATE
# ─────────────────────────────────────────────
def _set_exists(sid):
    return sid and c.execute("SELECT 1 FROM Sets WHERE set_num=?", (sid,)).fetchone()

if 'page' not in st.session_state:
    # Timer first: on app open, land on the stopwatch of the set you're
    # building. Priority: running timer → last opened → single Building set.
    timer_row = get_active_timer()
    land_on = None
    if timer_row and _set_exists(timer_row[0]):
        land_on = timer_row[0]
    if not land_on:
        last_opened = get_app_state('last_opened_set')
        if _set_exists(last_opened):
            land_on = last_opened
    if not land_on:
        building = pd.read_sql_query(
            "SELECT set_num FROM Sets WHERE status='Building' LIMIT 2", conn)
        if len(building) == 1:
            land_on = building.iloc[0]['set_num']
    if land_on:
        st.session_state.page = 'workbench'
        st.session_state.selected_set = land_on
    else:
        st.session_state.page = 'collection'
        st.session_state.selected_set = None

# ─────────────────────────────────────────────
# HEADER & GLOBAL STATS
# ─────────────────────────────────────────────
all_sets      = get_all_sets()
total_secs_db = pd.read_sql_query("SELECT SUM(duration) as s FROM Build_Logs", conn)['s'].iloc[0] or 0

# Add active timer seconds if running
active_timer = get_active_timer()
if active_timer:
    total_secs_db += timer_elapsed_seconds(active_timer)

total_hours = round(total_secs_db / 3600, 1)
built_count = len(all_sets[all_sets['status'] == 'Built']) if not all_sets.empty else 0

# Compact one-line header: brand + hours/built. Everything else lives on Stats.
st.markdown(f"""
<div class='brand-line'>🧱 {APP_NAME}</div>
<div class='stats-line'>⏱ <b>{total_hours}h</b> building &nbsp;·&nbsp; ✅ <b>{built_count}</b> built</div>
""", unsafe_allow_html=True)

# Top nav — nowrap keyed container keeps these on one row on phones.
# "⏱ Build" jumps back to the set you're building, from anywhere.
build_target = None
_timer_row = get_active_timer()
if _timer_row and _set_exists(_timer_row[0]):
    build_target = _timer_row[0]
elif _set_exists(get_app_state('last_opened_set')):
    build_target = get_app_state('last_opened_set')

with st.container(key="nowrap_topnav"):
    if build_target:
        nb, n1, n2, n3 = st.columns(4)
        with nb:
            if st.button("⏱ Build", use_container_width=True, type="primary"):
                st.session_state.page = 'workbench'
                st.session_state.selected_set = build_target
                st.rerun()
    else:
        n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("🧱 Sets", use_container_width=True):
            st.session_state.page = 'collection'
            st.session_state.selected_set = None
            st.rerun()
    with n2:
        if st.button("📊 Stats", use_container_width=True):
            st.session_state.page = 'stats'
            st.session_state.selected_set = None
            st.rerun()
    with n3:
        if st.button("📤 Export", use_container_width=True):
            st.session_state.page = 'export'
            st.session_state.selected_set = None
            st.rerun()

# If a previous save couldn't reach GitHub, the DB is committed locally but
# not backed up. Give the user a one-click recovery instead of silent loss.
if st.session_state.get('unsynced'):
    uc1, uc2 = st.columns([4, 1])
    uc1.warning("⚠️ Some changes aren't backed up yet — they'd be lost if the app restarts.")
    with uc2:
        if st.button("🔁 Retry backup", use_container_width=True, type="primary"):
            if push_db_to_github():
                st.session_state['unsynced'] = False
                st.rerun()
            else:
                st.error("Still can't reach the backup. Check your connection and try again in a minute.")

# No backup target at all is a different problem from a failed push, and a
# quiet one — say so plainly rather than letting it look like everything's fine.
if not backup_configured():
    st.caption("⚠️ Backups aren't set up — your collection is only stored on this "
               "machine. Add GITHUB_TOKEN and GITHUB_REPO to the app's secrets "
               "(see the README) to keep it safe.")

st.divider()

# ─────────────────────────────────────────────
# COLLECTION PAGE
# ─────────────────────────────────────────────
if st.session_state.page == 'collection':

    # ── On the Bench banner (full-width, phone-friendly) ──
    building_sets = all_sets[all_sets['status'] == 'Building'] if not all_sets.empty else pd.DataFrame()
    # Two GROUP BY queries replace the per-card get_photos/get_logs lookups
    # (previously 2+ queries per set on every rerun).
    time_by_set = dict(c.execute(
        "SELECT set_num, SUM(duration) FROM Build_Logs GROUP BY set_num").fetchall())
    photos_by_set = dict(c.execute(
        "SELECT set_num, COUNT(*) FROM Photos GROUP BY set_num").fetchall())

    if not building_sets.empty:
        st.markdown("<div style='color:var(--accent);font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px'>🔧 On the Bench</div>", unsafe_allow_html=True)
        for _, brow in building_sets.head(3).iterrows():
            secs = time_by_set.get(brow['set_num']) or 0
            # Add live timer if this set is active
            if active_timer and active_timer[0] == brow['set_num']:
                secs += timer_elapsed_seconds(active_timer)
            time_str = fmt_seconds(secs) if secs > 0 else "Not started"
            # Built as one unbroken string on purpose: a set with no picture
            # makes thumb_html() empty, and a blank line inside raw HTML ends
            # the HTML block in markdown — which would dump tags on screen.
            st.markdown(
                "<div class='building-banner'>"
                f"{thumb_html(brow['image_url'], 'building-banner-thumb')}"
                "<div>"
                "<div class='building-banner-title'>Building</div>"
                f"<div class='building-banner-name'>{brow['name']}</div>"
                f"<div style='color:#8b90a0;font-size:0.8rem;margin-top:4px'>⏱ {time_str} logged</div>"
                "</div></div>",
                unsafe_allow_html=True)
            if st.button(f"▶ Open {brow['name']}", key=f"banner_{brow['set_num']}", use_container_width=True):
                st.session_state.selected_set = brow['set_num']
                st.session_state.page = 'workbench'
                st.rerun()
        st.divider()

    st.markdown("<h2>🧱 My Collection</h2>", unsafe_allow_html=True)

    # ── Add a set ───────────────────────────────────────────────
    with st.expander("➕ Add a LEGO set", expanded=all_sets.empty):

        if rb_enabled():
            st.caption("Type the number printed on the box (like **10276**) or a name "
                       "(like **Millennium Falcon**) and we'll fill in the rest.")
            with st.form("set_search"):
                query = st.text_input("Set number or name", placeholder="10276  ·  Millennium Falcon")
                if st.form_submit_button("🔍 Search LEGO database", type="primary"):
                    q = (query or "").strip()
                    if not q:
                        st.session_state.pop('search_results', None)
                        st.warning("Type a set number or a name first.")
                    else:
                        with st.spinner("Looking it up..."):
                            # A bare number is almost always an exact set number,
                            # so try that first and fall back to a name search.
                            hits, err = [], None
                            if q.replace("-", "").isdigit():
                                one, lookup_err = rb_lookup_set(q)
                                if one:
                                    hits = [one]
                                else:
                                    err = lookup_err
                            if not hits:
                                found, serr = rb_search_sets(q)
                                if found:
                                    hits, err = found, None
                                elif serr:
                                    err = serr
                        st.session_state['search_results'] = hits
                        st.session_state['search_error']   = err

            hits = st.session_state.get('search_results')
            err  = st.session_state.get('search_error')
            if err and not hits:
                st.warning(err)
            if hits:
                st.markdown(f"**{len(hits)} match{'es' if len(hits) != 1 else ''} — pick one to add:**")
                for hit in hits:
                    hc1, hc2, hc3 = st.columns([1, 5, 2])
                    with hc1:
                        if hit.get("image_url"):
                            st.image(hit["image_url"], use_container_width=True)
                    with hc2:
                        pcs  = safe_int(hit.get("pieces"))
                        yr   = safe_int(hit.get("year"))
                        meta = " · ".join(x for x in [
                            hit.get("set_num"),
                            f"{pcs:,} pcs" if pcs else None,
                            str(yr) if yr else None,
                        ] if x)
                        st.markdown(
                            f"<div class='search-hit-name'>{hit.get('name')}</div>"
                            f"<div class='search-hit-meta'>{meta}</div>",
                            unsafe_allow_html=True)
                    with hc3:
                        already = c.execute("SELECT 1 FROM Sets WHERE set_num=?",
                                            (hit.get("set_num"),)).fetchone()
                        if already:
                            st.caption("✓ In collection")
                        elif st.button("➕ Add", key=f"add_{hit.get('set_num')}",
                                       use_container_width=True):
                            # Search hits skip the extra theme/minifig calls;
                            # fetch the full record now that it's actually wanted.
                            full, _ferr = rb_lookup_set(hit["set_num"])
                            ok, msg = add_set_to_collection(full or hit)
                            if ok:
                                if save_and_report(msg):
                                    st.session_state.pop('search_results', None)
                                    st.session_state.pop('search_error', None)
                                    st.rerun()
                            else:
                                st.warning(msg)
            st.divider()
            manual_label = "✏️ Or type the details in by hand"
        else:
            st.info(
                "💡 **For whoever set this up:** add a free Rebrickable API key as "
                "`REBRICKABLE_API_KEY` in the app's secrets and this page will look "
                "sets up automatically — name, theme, piece count and picture, all "
                "from the number on the box. Setup takes 2 minutes; see the README.")
            manual_label = "✏️ Add a set by hand"

        with st.expander(manual_label, expanded=not rb_enabled()):
            with st.form("add_set_manual", clear_on_submit=True):
                m_num   = st.text_input("Set number (from the box, e.g. 10276)").strip()
                m_name  = st.text_input("Name")
                m_theme = st.text_input("Theme (e.g. Star Wars, Technic, Icons)")
                mc1, mc2, mc3 = st.columns(3)
                m_pieces = mc1.number_input("Pieces",   min_value=0, step=1, value=0)
                m_year   = mc2.number_input("Year",     min_value=0, max_value=2100, step=1, value=0)
                m_figs   = mc3.number_input("Minifigs", min_value=0, step=1, value=0)
                if st.form_submit_button("Add to collection"):
                    if not m_num:
                        st.error("Please enter a set number.")
                    elif not m_name:
                        st.error("Please enter a name.")
                    else:
                        ok, msg = add_set_to_collection({
                            "set_num":   m_num.upper(),
                            "name":      m_name,
                            "theme":     m_theme or None,
                            "pieces":    m_pieces or None,
                            "year":      m_year or None,
                            "minifigs":  m_figs or None,
                            "image_url": None,
                        })
                        if ok:
                            if save_and_report(msg):
                                st.rerun()
                        else:
                            st.warning(msg)

    # Filters — collapsed by default to keep the phone view short
    all_sets = get_all_sets()
    with st.expander("🔍 Filter & sort"):
        status_filter = st.selectbox("Filter by status", ['All'] + STATUS_OPTIONS)
        themes = ['All'] + sorted(all_sets['theme'].dropna().unique().tolist()) if not all_sets.empty else ['All']
        theme_filter = st.selectbox("Filter by theme", themes)
        sort_by = st.selectbox("Sort by", ['Last Worked', 'Name', 'Pieces', 'Theme', 'Year', 'Status'])

    display_df = all_sets.copy()
    if status_filter != 'All':
        display_df = display_df[display_df['status'] == status_filter]
    if theme_filter != 'All':
        display_df = display_df[display_df['theme'] == theme_filter]

    sort_map = {'Last Worked': 'last_worked', 'Name': 'name', 'Pieces': 'pieces',
                'Theme': 'theme', 'Year': 'year', 'Status': 'status'}
    # Biggest-first for pieces and newest-first for year; the rest read best A→Z.
    ascending = sort_by not in ('Pieces', 'Year')
    display_df = display_df.sort_values(sort_map[sort_by], ascending=ascending)

    if all_sets.empty:
        st.info("👋 **Welcome!** Your collection is empty. Open **➕ Add a LEGO set** "
                "above, type the number off the box, and you're away.")
    elif display_df.empty:
        st.info("No sets match those filters.")
    else:
        # Set cards — single-column compact list (phone-first)
        for _, row in display_df.iterrows():
            emoji      = STATUS_EMOJI.get(row['status'], '📦')
            photo_icon = " 📸" if photos_by_set.get(row['set_num']) else ""
            secs       = time_by_set.get(row['set_num']) or 0
            time_str   = fmt_seconds(secs) if secs > 0 else "—"

            # Is this the active timer set?
            timer_icon = ""
            if active_timer and active_timer[0] == row['set_num']:
                timer_icon = " ⏸️" if timer_is_paused(active_timer) else " ⏱️"

            status_color = STATUS_COLOR.get(row['status'], '#777f8f')

            # One unbroken string — see the note on the banner above.
            st.markdown(
                "<div class='set-card'>"
                f"{thumb_html(row['image_url'])}"
                "<div class='set-card-body'>"
                f"<div class='set-card-title'>{emoji} {row['name']}{photo_icon}{timer_icon}</div>"
                "<div class='set-card-meta'>"
                f"<span style='color:{status_color};font-weight:600'>{row['status']}</span>"
                f" &nbsp;·&nbsp; ⏱ {time_str} &nbsp;·&nbsp; {set_meta_line(row)}"
                "</div></div></div>",
                unsafe_allow_html=True)
            if st.button("Open →", key=f"btn_{row['set_num']}", use_container_width=True):
                st.session_state.selected_set = row['set_num']
                st.session_state.page = 'workbench'
                st.rerun()

    # ── Plain-language help, tucked at the bottom ──
    with st.expander("❓ How this works"):
        st.markdown("""
**Adding a set** — tap **➕ Add a LEGO set**, type the number printed on the box
(or the set's name), and pick it from the list. Everything else fills itself in.

**Timing a build** — open a set and hit **▶️ Start build session**. The clock
keeps running even if you close the app or your phone locks, so come back later
and hit **⏹️ Stop & save**. Forgot to stop? A paused session saves itself after
an hour, and you can always correct the minutes afterwards.

**Photos** — snap progress pictures from the **📸 Photos** tab, or right after a
session when it offers. They show up in the set's **📖 Journal** next to your notes.

**Is my stuff safe?** — every change is backed up automatically. If a backup ever
fails you'll see an orange warning at the top with a **Retry backup** button. No
warning means you're saved.
""")

# ─────────────────────────────────────────────
# STATS PAGE
# ─────────────────────────────────────────────
elif st.session_state.page == 'stats':
    st.markdown("<h2>📊 Collection Stats</h2>", unsafe_allow_html=True)

    all_sets = get_all_sets()
    all_logs = pd.read_sql_query("SELECT * FROM Build_Logs", conn)

    if all_sets.empty:
        st.info("Add some sets to see your stats!")
    else:
        # ── Top row stats ──
        # Split logs: estimates count toward total hours only; real sessions
        # drive the session count, average, and heatmap.
        if not all_logs.empty and 'is_estimate' in all_logs.columns:
            real_logs = all_logs[all_logs['is_estimate'].fillna(0) == 0]
        else:
            real_logs = all_logs

        total_pieces     = int(all_sets['pieces'].fillna(0).sum())
        built_sets       = all_sets[all_sets['status'] == 'Built']
        pieces_built     = int(built_sets['pieces'].fillna(0).sum())
        total_minifigs   = int(all_sets['minifigs'].fillna(0).sum())
        total_build_secs = all_logs['duration'].sum() if not all_logs.empty else 0
        avg_session_mins = round((real_logs['duration'].mean() or 0) / 60, 1) if not real_logs.empty else 0
        total_sessions   = len(real_logs)
        est_count        = len(all_logs) - len(real_logs)
        total_photos     = pd.read_sql_query("SELECT COUNT(*) as n FROM Photos", conn)['n'].iloc[0] or 0
        n_building       = len(all_sets[all_sets['status'] == 'Building'])

        # Pieces per hour, over finished sets only — the number is meaningless
        # while a build is still half-done.
        built_secs = (all_logs[all_logs['set_num'].isin(built_sets['set_num'])]['duration'].sum()
                      if not all_logs.empty else 0)
        pph = int(pieces_built / (built_secs / 3600)) if built_secs > 0 and pieces_built else 0

        # Compact wrapping stat chips (3-up on phones) instead of stacked tiles
        chips = [
            (f"{round(total_build_secs/3600, 1)}h", "Hours Building"),
            (total_sessions,                        "Sessions"),
            (f"{avg_session_mins}m",                "Avg Session"),
            (len(all_sets),                         "Sets Owned"),
            (n_building,                            "On the Bench"),
            (len(built_sets),                       "Built"),
            (f"{total_pieces:,}",                   "Pieces Owned"),
            (f"{pieces_built:,}",                   "Pieces Built"),
            (f"{total_minifigs:,}",                 "Minifigs"),
        ]
        if pph:
            chips.append((f"{pph:,}", "Pieces / Hour"))
        chips.append((total_photos, "Photos"))

        chips_html = "".join(
            f"<div class='stat-chip'><div class='stat-chip-value'>{v}</div>"
            f"<div class='stat-chip-label'>{l}</div></div>"
            for v, l in chips)
        st.markdown(f"<div class='stat-chips'>{chips_html}</div>", unsafe_allow_html=True)
        if est_count:
            st.caption(f"⚠️ {est_count} estimated/backfilled log{'s' if est_count != 1 else ''} "
                       f"included in total hours but excluded from session count, average, and the heatmap.")

        st.divider()

        # ── Collection breakdown ──
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 🎨 By Theme")
            themed = all_sets.dropna(subset=['theme'])
            if themed.empty:
                st.caption("No themes recorded yet.")
            else:
                theme_counts = themed.groupby('theme').size().reset_index(name='count')
                theme_counts = theme_counts.sort_values('count', ascending=False).head(10)
                for _, r in theme_counts.iterrows():
                    pct = int(r['count'] / len(all_sets) * 100)
                    st.markdown(f"""
                    <div style='margin-bottom:8px'>
                        <div style='display:flex;justify-content:space-between;margin-bottom:3px'>
                            <span style='color:#e9eaee;font-size:0.85rem'>{r['theme']}</span>
                            <span style='color:var(--accent);font-size:0.85rem'>{r['count']}</span>
                        </div>
                        <div style='background:var(--border);border-radius:4px;height:6px'>
                            <div style='background:var(--accent);width:{pct}%;height:6px;border-radius:4px'></div>
                        </div>
                    </div>""", unsafe_allow_html=True)

        with col_right:
            st.markdown("#### 📈 By Status")
            status_counts = all_sets.groupby('status').size().reset_index(name='count')
            for _, r in status_counts.iterrows():
                pct   = int(r['count'] / len(all_sets) * 100)
                color = STATUS_COLOR.get(r['status'], 'var(--accent)')
                st.markdown(f"""
                <div style='margin-bottom:8px'>
                    <div style='display:flex;justify-content:space-between;margin-bottom:3px'>
                        <span style='color:#e9eaee;font-size:0.85rem'>{r['status']}</span>
                        <span style='font-size:0.85rem;color:{color}'>{r['count']} ({pct}%)</span>
                    </div>
                    <div style='background:var(--border);border-radius:4px;height:6px'>
                        <div style='background:{color};width:{pct}%;height:6px;border-radius:4px'></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Build heatmap (last 12 weeks) ──
        if not real_logs.empty:
            st.markdown("#### 🗓️ Build Activity")
            heatmap_logs = real_logs.copy()
            # start_time is stored in mixed formats (ISO from the timer,
            # "%Y-%m-%d %H:%M" from manual logs) — parse flexibly and drop
            # any rows that still won't parse instead of crashing.
            parsed = pd.to_datetime(heatmap_logs['start_time'], format='mixed', errors='coerce')
            heatmap_logs = heatmap_logs.assign(date=parsed.dt.date)
            heatmap_logs = heatmap_logs.dropna(subset=['date'])
            if heatmap_logs.empty:
                st.info("No dated sessions to chart yet.")
            else:
                daily = heatmap_logs.groupby('date')['duration'].sum().reset_index()
                daily.columns = ['date', 'seconds']

                import datetime as dt
                today      = dt.date.today()
                start_date = today - dt.timedelta(weeks=12)
                date_range = pd.date_range(start=start_date, end=today)
                date_df    = pd.DataFrame({'date': date_range.date})
                merged     = date_df.merge(daily, on='date', how='left').fillna(0)
                max_secs   = merged['seconds'].max() or 1

                # Render as a grid of colored squares
                weeks = [merged.iloc[i:i+7] for i in range(0, len(merged), 7)]
                week_html = "<div style='display:flex;gap:3px;flex-wrap:nowrap;overflow-x:auto'>"
                for week in weeks:
                    week_html += "<div style='display:flex;flex-direction:column;gap:3px'>"
                    for _, day_row in week.iterrows():
                        intensity = day_row['seconds'] / max_secs
                        if intensity == 0:
                            color = "var(--surface)"
                        elif intensity < 0.3:
                            color = "#4a4113"
                        elif intensity < 0.6:
                            color = "#a48800"
                        else:
                            color = "var(--accent)"
                        mins  = int(day_row['seconds'] // 60)
                        title = f"{day_row['date']}: {mins}min"
                        week_html += f"<div title='{title}' style='width:14px;height:14px;background:{color};border-radius:3px;border:1px solid var(--border)'></div>"
                    week_html += "</div>"
                week_html += "</div>"
                week_html += "<div style='color:#6b7080;font-size:0.7rem;margin-top:6px'>Last 12 weeks — hover for details</div>"
                st.markdown(week_html, unsafe_allow_html=True)

        st.divider()

        # ── Top builds by time ──
        if not all_logs.empty:
            st.markdown("#### 🏆 Most Time Spent")
            set_time = all_logs.groupby('set_num')['duration'].sum().reset_index()
            set_time = set_time.merge(
                all_sets[['set_num', 'name', 'status']], on='set_num', how='left')
            set_time = set_time.sort_values('duration', ascending=False).head(5)
            for _, r in set_time.iterrows():
                emoji = STATUS_EMOJI.get(r['status'], '📦')
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;padding:8px 12px;
                            background:var(--surface);border-radius:6px;margin-bottom:6px;
                            border:1px solid var(--border)'>
                    <span style='color:#e9eaee'>{emoji} {r['name']}</span>
                    <span style='color:var(--accent);font-weight:700'>{fmt_seconds(r['duration'])}</span>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# EXPORT PAGE — get a copy of your data that's yours
# ─────────────────────────────────────────────
elif st.session_state.page == 'export':
    st.markdown("<h2>📤 Export Your Data</h2>", unsafe_allow_html=True)
    st.markdown("Your collection, always in sync with your Google Sheet.")

    sets_df   = get_all_sets()
    logs_df   = pd.read_sql_query("SELECT * FROM Build_Logs ORDER BY set_num, start_time", conn)
    photos_df = pd.read_sql_query("SELECT * FROM Photos ORDER BY set_num, uploaded_at", conn)

    # ── Google Sheet sync — primary ─────────────────────────────
    st.markdown("<h3>🔄 Google Sheet sync</h3>", unsafe_allow_html=True)
    if gsheet_webhook():
        st.success("✅ Connected — your sheet auto-updates on every save.")
        st.caption(f"{len(sets_df)} sets · {len(logs_df)} sessions · {len(photos_df)} photos")
        if st.button("🔄 Sync now", type="primary"):
            with st.spinner("Pushing to your Google Sheet..."):
                ok, msg = sync_to_sheet()
            if ok:
                st.success("Google Sheet updated!")
            else:
                st.error(f"Sync failed: {msg}")
    else:
        st.info("Not connected yet. Set it up once below, then it stays in sync automatically.")
        with st.expander("⚙️ One-time setup (about 5 minutes)"):
            st.markdown("""
**1.** Create (or open) a Google Sheet you want your data mirrored into.

**2.** In that sheet: **Extensions → Apps Script**. Delete whatever's there and paste the script below. *(Optional: set `SECRET` to any password to lock down your webhook.)*

**3.** Click **Deploy → New deployment** → gear icon → **Web app**. Set **Execute as: Me** and **Who has access: Anyone**, then **Deploy**. Approve the access prompt (click *Advanced → Go to … (unsafe)* — it's your own script).

**4.** Copy the **Web app URL** it gives you.

**5.** Add it to your app secrets (`.streamlit/secrets.toml`, or *Manage app → Secrets* on Streamlit Cloud):
```toml
GSHEET_WEBHOOK_URL = "https://script.google.com/macros/s/XXXX/exec"
# GSHEET_SECRET = "the-same-password-as-SECRET"   # only if you set one
```

**6.** Reload this app and hit **Sync now**. Every save after that updates the sheet automatically.
""")
            st.caption("Paste this into Apps Script:")
            st.code(APPS_SCRIPT_CODE, language="javascript")

    # ── Download backup (collapsed) ─────────────────────────────
    st.divider()
    with st.expander("⬇️ Download a backup copy"):
        if sets_df.empty and logs_df.empty:
            st.info("Nothing to export yet.")
        else:
            stamp = datetime.now().strftime("%Y-%m-%d")
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as xl:
                sets_df.to_excel(xl,   sheet_name="Sets",       index=False)
                logs_df.to_excel(xl,   sheet_name="Build Logs", index=False)
                photos_df.to_excel(xl, sheet_name="Photos",     index=False)
            st.download_button(
                "⬇️ Excel workbook (.xlsx) — Sets, Build Logs, Photos",
                data=buf.getvalue(),
                file_name=f"brick_bench_export_{stamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                st.download_button("Sets.csv", sets_df.to_csv(index=False),
                    f"sets_{stamp}.csv", "text/csv", use_container_width=True)
            with d2:
                st.download_button("Build Logs.csv", logs_df.to_csv(index=False),
                    f"build_logs_{stamp}.csv", "text/csv", use_container_width=True)
            with d3:
                st.download_button("Photos.csv", photos_df.to_csv(index=False),
                    f"photos_{stamp}.csv", "text/csv", use_container_width=True)

# ─────────────────────────────────────────────
# WORKBENCH PAGE
# ─────────────────────────────────────────────
elif st.session_state.page == 'workbench':
    set_num  = st.session_state.selected_set
    lego_set = get_set(set_num)

    if lego_set is None:
        st.error("Set not found.")
        st.session_state.page = 'collection'
        st.rerun()

    # Remember where we are so the app reopens right here next time
    set_app_state('last_opened_set', set_num)

    # Compact one-row header: back button + name, then a single info line
    with st.container(key="nowrap_backrow"):
        bc1, bc2 = st.columns([1, 6])
        with bc1:
            if st.button("⬅️", help="Back to collection"):
                st.session_state.page = 'collection'
                st.session_state.selected_set = None
                st.rerun()
        with bc2:
            st.markdown(f"<h2 style='margin:0'>🔧 {lego_set['name']}</h2>", unsafe_allow_html=True)

    st.markdown(f"<div class='stats-line'>{set_meta_line(lego_set)}</div>", unsafe_allow_html=True)

    tab_timer, tab_journal, tab_details, tab_photos = st.tabs(
        ["⏱️ Timer", "📖 Journal", "📋 Details", "📸 Photos"])

    # ── TAB: TIMER (first tab — center stage) ──────────────────
    with tab_timer:
        secs_logged = total_time_seconds(set_num)

        # Check for active timer
        active = get_active_timer()
        is_active = active and active[0] == set_num

        # Post-session recap: the session is already saved (nothing can be
        # lost) — this just offers a note + photo while it's fresh.
        recap = st.session_state.get('recap')
        if recap and recap.get('set_num') == set_num and not is_active:
            st.success(f"✅ Logged {fmt_seconds(recap['duration'])} — add a note & photo while it's fresh?")
            recap_note = st.text_input("What did you build?", key="recap_note",
                                       placeholder="e.g. Finished the cockpit")
            recap_cam  = st.camera_input("📷 Snap a progress photo (optional)", key="recap_cam")
            recap_up   = None
            if recap_cam is None:
                recap_up = st.file_uploader("…or choose a photo", type=["jpg", "jpeg", "png", "webp"],
                                            key="recap_upload")
            with st.container(key="nowrap_recap"):
                rb1, rb2 = st.columns(2)
                do_save = rb1.button("💾 Save recap", type="primary", use_container_width=True)
                do_skip = rb2.button("Skip", use_container_width=True)
            if do_save:
                if recap_note:
                    c.execute("UPDATE Build_Logs SET notes=? WHERE log_id=?",
                              (recap_note, recap['log_id']))
                photo = recap_cam or recap_up
                photo_err = None
                if photo is not None:
                    with st.spinner("Uploading photo..."):
                        ext = "jpg"
                        if getattr(photo, "name", None) and "." in photo.name:
                            ext = photo.name.rsplit(".", 1)[-1].lower()
                        filename = f"{set_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                        url, photo_err = upload_to_github(photo.getvalue(), filename)
                    if url:
                        c.execute(
                            "INSERT INTO Photos (set_num, url, caption, uploaded_at) VALUES (?,?,?,?)",
                            (set_num, url, recap_note, datetime.now().strftime("%Y-%m-%d %H:%M")))
                if photo_err:
                    st.error(f"Photo upload failed: {photo_err} — note not saved yet, try again.")
                elif save_and_report("Session saved!"):
                    del st.session_state['recap']
                    st.rerun()
            if do_skip:
                del st.session_state['recap']
                st.rerun()
            st.divider()

        if is_active:
            paused = timer_is_paused(active)

            def _stopwatch_html(elapsed, label):
                total_display = secs_logged + elapsed
                h, rem = divmod(int(elapsed), 3600)
                m, s   = divmod(rem, 60)
                return f"""
                <div class='stopwatch'>
                    <div class='stopwatch-label'>{label}</div>
                    <div class='stopwatch-time'>{h:02d}:{m:02d}:{s:02d}</div>
                    <div class='stopwatch-label' style='margin-top:12px'>Total on this set: {fmt_seconds(total_display)}</div>
                </div>"""

            if paused:
                # Frozen clock — no ticking fragment while paused
                st.markdown(_stopwatch_html(timer_elapsed_seconds(active), "⏸ PAUSED"),
                            unsafe_allow_html=True)
                st.caption(f"Paused sessions auto-save after {PAUSE_AUTO_STOP_MINS} minutes.")
            else:
                # Live stopwatch. A fragment with run_every re-renders just this
                # block once a second — a real ticking clock, no full reload.
                # The *recorded* duration still comes from timer_elapsed_seconds
                # at Stop, so the logged value is exact regardless of rendering.
                @st.fragment(run_every=1)
                def _live_stopwatch():
                    st.markdown(_stopwatch_html(timer_elapsed_seconds(active), "Session Time"),
                                unsafe_allow_html=True)
                _live_stopwatch()

            with st.container(key="nowrap_timerbtns"):
                tb1, tb2 = st.columns(2)
                with tb1:
                    if paused:
                        if st.button("▶️ Resume", use_container_width=True):
                            resume_active_timer()
                            st.rerun()
                    else:
                        if st.button("⏸ Pause", use_container_width=True):
                            pause_active_timer()
                            st.rerun()
                with tb2:
                    stop_clicked = st.button("⏹️ Stop & save", type="primary", use_container_width=True)

            if stop_clicked:
                duration = timer_elapsed_seconds(active)
                # Save the session immediately — the note/photo recap that
                # follows is optional, so nothing is lost if it's abandoned.
                c.execute(
                    "INSERT INTO Build_Logs (set_num, start_time, duration, notes) VALUES (?,?,?,?)",
                    (set_num, active[1], duration, ""))
                log_id = c.lastrowid
                c.execute(
                    "UPDATE Sets SET last_worked=?, status=? WHERE set_num=?",
                    (str(datetime.now().date()),
                     'Building' if lego_set['status'] == 'Unbuilt' else lego_set['status'],
                     set_num))
                c.execute("DELETE FROM Active_Timer")
                st.session_state['recap'] = {
                    'set_num': set_num, 'log_id': log_id, 'duration': duration}
                # Single commit+push for the whole session so a failed sync
                # is reported instead of silently dropping the logged time.
                if save_and_report(None):
                    st.rerun()

        else:
            # Show total time and start button
            st.markdown(f"""
            <div class='stopwatch'>
                <div class='stopwatch-label'>Total Time on This Set</div>
                <div class='stopwatch-time'>{fmt_seconds(secs_logged)}</div>
                <div class='stopwatch-label' style='margin-top:12px'>Ready to build</div>
            </div>""", unsafe_allow_html=True)

            # Check if another set has the timer
            if active and active[0] != set_num:
                other = get_set(active[0])
                other_name = other['name'] if other is not None else active[0]
                st.warning(f"⚠️ The timer is currently running on **{other_name}**. Stop that session first, or switch it over below.")
                if st.button(f"🔄 Switch timer to {lego_set['name']}", type="secondary"):
                    # Stop old session without saving
                    clear_active_timer()
                    set_active_timer(set_num, datetime.now().isoformat())
                    st.rerun()
            else:
                if st.button("▶️ Start build session", type="primary", use_container_width=True):
                    set_active_timer(set_num, datetime.now().isoformat())
                    st.rerun()

        st.divider()
        st.markdown("**Or log time by hand:**")
        with st.form("manual_log"):
            manual_mins = st.number_input("Minutes", min_value=1, value=30)
            manual_note = st.text_input("Note")
            manual_est  = st.checkbox(
                "This is an estimate / bulk backfill",
                help="Counts toward total hours, but excluded from session count, average, and the heatmap.")
            if st.form_submit_button("Log session"):
                c.execute(
                    "INSERT INTO Build_Logs (set_num, start_time, duration, notes, is_estimate) VALUES (?,?,?,?,?)",
                    (set_num, datetime.now().strftime("%Y-%m-%d %H:%M"), manual_mins * 60,
                     manual_note, 1 if manual_est else 0))
                c.execute("UPDATE Sets SET last_worked=? WHERE set_num=?",
                          (str(datetime.now().date()), set_num))
                if save_and_report("Logged!"):
                    st.rerun()

        st.divider()
        st.markdown("#### 📅 Build History")
        logs = get_logs(set_num)
        if logs.empty:
            st.info("No sessions logged yet.")
        else:
            for _, log in logs.iterrows():
                lid = int(log['log_id'])
                editing = st.session_state.get(f"editing_log_{lid}", False)

                if editing:
                    st.markdown(
                        "<div style='background:var(--surface);border:1px solid var(--accent);"
                        "border-radius:8px;padding:12px;margin-bottom:8px'>",
                        unsafe_allow_html=True)
                    ec1, ec2 = st.columns([1, 2])
                    with ec1:
                        new_mins = st.number_input(
                            "Minutes", min_value=0.0, step=1.0,
                            value=round(log['duration'] / 60, 1),
                            key=f"edit_mins_{lid}")
                    with ec2:
                        new_note = st.text_input(
                            "Note", value=log['notes'] or "", key=f"edit_note_{lid}")
                    new_est = st.checkbox(
                        "Estimate / bulk backfill (excluded from average, session count, heatmap)",
                        value=bool(log['is_estimate']) if 'is_estimate' in log and pd.notna(log['is_estimate']) else False,
                        key=f"edit_est_{lid}")
                    sc1, sc2, _ = st.columns([1, 1, 3])
                    with sc1:
                        if st.button("💾 Save", key=f"save_log_{lid}", type="primary"):
                            c.execute(
                                "UPDATE Build_Logs SET duration=?, notes=?, is_estimate=? WHERE log_id=?",
                                (new_mins * 60, new_note, 1 if new_est else 0, lid))
                            if save_and_report("Saved!"):
                                st.session_state[f"editing_log_{lid}"] = False
                                st.rerun()
                    with sc2:
                        if st.button("Cancel", key=f"cancel_log_{lid}"):
                            st.session_state[f"editing_log_{lid}"] = False
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    is_est = bool(log['is_estimate']) if 'is_estimate' in log and pd.notna(log['is_estimate']) else False
                    est_badge = " <span style='background:#3a3413;color:var(--accent);font-size:0.6rem;padding:1px 5px;border-radius:4px;letter-spacing:1px'>EST</span>" if is_est else ""
                    # One row per session on phones: text block + two icon buttons
                    log_note_html = f"<br><span style='color:#e9eaee'>{log['notes']}</span>" if log['notes'] else ""
                    with st.container(key=f"nowrap_logrow_{lid}"):
                        rc1, rc2, rc3 = st.columns([8, 1, 1])
                        rc1.markdown(
                            f"<div style='font-size:0.85rem;line-height:1.5'>"
                            f"<span style='color:var(--accent);font-weight:600'>{fmt_seconds(log['duration'])}</span>{est_badge}"
                            f" <span style='color:#8b90a0'>· {log['start_time']}</span>"
                            f"{log_note_html}"
                            f"</div>",
                            unsafe_allow_html=True)
                        with rc2:
                            if st.button("✏️", key=f"edit_btn_{lid}", help="Edit this session"):
                                st.session_state[f"editing_log_{lid}"] = True
                                st.rerun()
                        with rc3:
                            if st.button("🗑️", key=f"del_log_{lid}", help="Delete this session"):
                                c.execute("DELETE FROM Build_Logs WHERE log_id=?", (lid,))
                                if save_and_report(None):
                                    st.rerun()

    # ── TAB: JOURNAL — the build's story, newest first ──────────
    with tab_journal:
        j_logs   = get_logs(set_num)
        j_photos = get_photos(set_num)

        entries = []
        for _, log in j_logs.iterrows():
            ts = pd.to_datetime(log['start_time'], format='mixed', errors='coerce')
            entries.append({'ts': ts, 'kind': 'session',
                            'duration': log['duration'], 'note': log['notes'],
                            'is_est': bool(log['is_estimate']) if pd.notna(log.get('is_estimate')) else False})
        for _, photo in j_photos.iterrows():
            ts = pd.to_datetime(photo['uploaded_at'], format='mixed', errors='coerce')
            entries.append({'ts': ts, 'kind': 'photo',
                            'url': photo['url'], 'caption': photo['caption']})

        if not entries:
            st.info("Nothing here yet — log a session or add a photo and the story builds itself.")
        else:
            # Newest first; undated entries sink to the bottom
            entries.sort(key=lambda e: pd.Timestamp.min if pd.isna(e['ts']) else e['ts'], reverse=True)
            total_secs = total_time_seconds(set_num)
            total_str  = fmt_seconds(total_secs) if total_secs else "0m"
            st.markdown(
                f"<div class='stats-line'>{len(j_logs)} session{'s' if len(j_logs) != 1 else ''} · "
                f"{len(j_photos)} photo{'s' if len(j_photos) != 1 else ''} · ⏱ {total_str} total</div>",
                unsafe_allow_html=True)
            for e in entries:
                date_str = e['ts'].strftime('%b %d, %Y · %H:%M') if not pd.isna(e['ts']) else 'Undated'
                if e['kind'] == 'session':
                    est_tag = " (estimate)" if e['is_est'] else ""
                    note_html = f"<div class='journal-body'>{e['note']}</div>" if e['note'] else ""
                    st.markdown(f"""
                    <div class='journal-entry'>
                        <div class='journal-date'>⏱ {date_str} — {fmt_seconds(e['duration'])}{est_tag}</div>
                        {note_html}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='journal-entry'><div class='journal-date'>📸 {date_str}</div></div>",
                                unsafe_allow_html=True)
                    st.image(e['url'], use_container_width=True)
                    if e['caption']:
                        st.caption(e['caption'])

    # ── TAB: DETAILS ───────────────────────────────
    with tab_details:
        if lego_set['image_url']:
            st.image(lego_set['image_url'], width=220)

        with st.form("edit_set"):
            new_status = st.selectbox("Status", STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(lego_set['status']) if lego_set['status'] in STATUS_OPTIONS else 0)
            new_rating = st.slider("My rating (1–10)", 1, 10,
                int(lego_set['rating']) if lego_set['rating'] else 1)
            new_notes  = st.text_area("Notes / tips",
                value=str(lego_set['notes']) if lego_set['notes'] else "")
            if st.form_submit_button("💾 Save changes"):
                c.execute("UPDATE Sets SET status=?, rating=?, notes=? WHERE set_num=?",
                          (new_status, new_rating, new_notes, set_num))
                if save_and_report("Saved!"):
                    st.rerun()

        # Catalog details — editable by hand, or re-pulled from the LEGO database
        with st.expander("✏️ Edit set details (name, theme, pieces…)"):
            with st.form("edit_set_catalog"):
                e_name  = st.text_input("Name", value=lego_set['name'] or "")
                e_theme = st.text_input("Theme", value=lego_set['theme'] or "")
                dc1, dc2, dc3 = st.columns(3)
                e_pieces = dc1.number_input("Pieces", min_value=0, step=1,
                                            value=safe_int(lego_set['pieces']) or 0)
                e_year   = dc2.number_input("Year", min_value=0, max_value=2100, step=1,
                                            value=safe_int(lego_set['year']) or 0)
                e_figs   = dc3.number_input("Minifigs", min_value=0, step=1,
                                            value=safe_int(lego_set['minifigs']) or 0)
                if st.form_submit_button("💾 Save details"):
                    c.execute(
                        "UPDATE Sets SET name=?, theme=?, pieces=?, year=?, minifigs=? WHERE set_num=?",
                        (e_name, e_theme or None, e_pieces or None, e_year or None,
                         e_figs or None, set_num))
                    if save_and_report("Details saved!"):
                        st.rerun()

            if rb_enabled():
                st.caption("Pulls the name, theme, pieces, year, minifigs and picture "
                           "from the LEGO database. Your status, rating, notes and "
                           "build history are left alone.")
                if st.button("🔄 Refresh from the LEGO database"):
                    ok, msg = refresh_set_from_rebrickable(set_num)
                    if ok:
                        if save_and_report(msg):
                            st.rerun()
                    else:
                        st.warning(msg)

        if st.button("🗑️ Remove from collection", type="secondary"):
            c.execute("DELETE FROM Sets WHERE set_num=?",       (set_num,))
            c.execute("DELETE FROM Build_Logs WHERE set_num=?", (set_num,))
            c.execute("DELETE FROM Photos WHERE set_num=?",     (set_num,))
            if save_and_report(None):
                st.session_state.page = 'collection'
                st.session_state.selected_set = None
                st.rerun()

    # ── TAB: PHOTOS ────────────────────────────────
    with tab_photos:
        photos = get_photos(set_num)

        with st.expander("📤 Upload a progress photo"):
            uploaded_file = st.file_uploader(
                "Choose an image", type=["jpg", "jpeg", "png", "webp"],
                key=f"uploader_{set_num}")
            caption_input = st.text_input("Caption (optional, e.g. 'Cockpit done!')")
            if uploaded_file is not None:
                st.image(uploaded_file, caption="Preview", width=300)
                if st.button("📤 Add to gallery", type="primary"):
                    with st.spinner("Uploading..."):
                        image_bytes = uploaded_file.read()
                        ext         = uploaded_file.name.rsplit(".", 1)[-1].lower()
                        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename    = f"{set_num}_{timestamp}.{ext}"
                        url, err    = upload_to_github(image_bytes, filename)
                    if url:
                        c.execute(
                            "INSERT INTO Photos (set_num, url, caption, uploaded_at) VALUES (?,?,?,?)",
                            (set_num, url, caption_input, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        if save_and_report("Photo uploaded!"):
                            st.rerun()
                    else:
                        st.error(f"Upload failed: {err}")

        if photos.empty:
            st.info("No photos yet. Document your build progress!")
        else:
            st.write(f"**{len(photos)} photo{'s' if len(photos) > 1 else ''}**")
            cols = st.columns(3)
            for i, (_, photo) in enumerate(photos.iterrows()):
                with cols[i % 3]:
                    st.image(photo['url'], use_container_width=True)
                    if photo['caption']:
                        st.caption(photo['caption'])
                    st.caption(f"🕐 {photo['uploaded_at']}")
                    if st.button("🗑️", key=f"del_photo_{photo['photo_id']}", help="Delete photo"):
                        c.execute("DELETE FROM Photos WHERE photo_id=?", (photo['photo_id'],))
                        if save_and_report(None):
                            st.rerun()
