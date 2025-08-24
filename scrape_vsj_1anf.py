# -*- coding: utf-8 -*-
"""
VSJ 1a Nacional Femení — Classificació RFEVB per OBS (amb Playwright)

Genera a:
  classificacio.csv
  classificacio_top3.txt
  classificacio_vsj.txt
  classificacio.html   (taula completa, VSJ destacat)
"""

import os, sys, io, re, time
import pandas as pd

# ===== Paràmetres =====
OUT_DIR   = r"C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF"
CSV_OUT   = os.path.join(OUT_DIR, "classificacio.csv")
TOP3_TXT  = os.path.join(OUT_DIR, "classificacio_top3.txt")
VSJ_TXT   = os.path.join(OUT_DIR, "classificacio_vsj.txt")
HTML_OUT  = os.path.join(OUT_DIR, "classificacio.html")

URL = "https://www.rfevb.com/primera-division-femenina-grupo-b-clasificacion"
TEAM_NAME = "CV Sant Just"

# Colors corporatius VSJ
TEAM_PRIMARY = "#305D87"  # blau
TEAM_ACCENT  = "#F6F685"  # groc

# ===== Utilitats =====
def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)

def render_html_with_playwright(url: str, timeout_ms=25000) -> str:
    """Renderitza la pàgina amb Chromium headless i retorna l'HTML resultant (JS inclòs)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="networkidle")
        try:
            page.wait_for_selector("table", timeout=timeout_ms)
        except Exception:
            pass
        html = page.content()
        browser.close()
        return html

def read_tables_from_html(html_text: str):
    for flavor in ("lxml", "html5lib"):
        try:
            tables = pd.read_html(io.StringIO(html_text), flavor=flavor)
            if tables:
                return tables
        except Exception:
            continue
    return []

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for tup in df.columns.values:
            parts = [str(x) for x in tup if not str(x).lower().startswith("unnamed")]
            name = " ".join(parts).strip()
            new_cols.append(name or "col")
        df.columns = new_cols
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df

def score_table(df: pd.DataFrame) -> int:
    kws = ["pos", "equipo", "equip", "team", "puntos", "points", "pj", "jug", "gan", "perd", "sets"]
    cols = [str(c).lower() for c in df.columns]
    score = sum(any(k in c for k in kws) for c in cols)
    score += min(len(df), 20)
    return score

def pick_standing_table(tables):
    best, best_s = None, -1
    for i, t in enumerate(tables):
        if t is None or t.empty:
            continue
        t = t.dropna(how="all")
        t = normalize_columns(t)
        s = score_table(t)
        print(f"  - Taula #{i} cols={list(t.columns)[:6]}… files={len(t)} -> score={s}")
        if s > best_s:
            best, best_s = t, s
    return best

def guess_columns(df: pd.DataFrame):
    cols = [c.lower() for c in df.columns]
    pos_i  = next((i for i,c in enumerate(cols) if re.search(r"\bpos", c)), 0)
    team_i = next((i for i,c in enumerate(cols) if any(k in c for k in ["equipo","equip","team"])), min(1, len(cols)-1))
    pts_i  = next((i for i,c in enumerate(cols) if any(k in c for k in ["puntos","points","pts","pt"])), len(cols)-1)
    return pos_i, team_i, pts_i

# ===== Sortides =====
def save_outputs(df: pd.DataFrame):
    ensure_dirs()
    df = df.dropna(how="all")
    df = normalize_columns(df)

    # CSV
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print("💾 CSV:", CSV_OUT, "files:", len(df))

    # TOP3
    pos_i, team_i, pts_i = guess_columns(df)
    top = df.iloc[:3].fillna("")
    lines = []
    for _, r in top.iterrows():
        pos   = str(r.iloc[pos_i]).strip()
        team  = str(r.iloc[team_i]).strip()
        punts = str(r.iloc[pts_i]).strip()
        lines.append(f"{pos} - {team} ({punts})")
    with open(TOP3_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("📝 TOP3:", TOP3_TXT)

    # Resum VSJ
    vsj_row = None
    for _, r in df.fillna("").iterrows():
        if TEAM_NAME.lower() in " ".join(map(str, r.values)).lower():
            vsj_row = r
            break
    with open(VSJ_TXT, "w", encoding="utf-8") as f:
        if vsj_row is not None:
            pos   = str(vsj_row.iloc[pos_i]).strip()
            team  = str(vsj_row.iloc[team_i]).strip()
            punts = str(vsj_row.iloc[pts_i]).strip()
            f.write(f"{pos} - {team} ({punts})\n")
        else:
            f.write(f"{TEAM_NAME}: no trobat\n")
    print("⭐ VSJ:", VS
