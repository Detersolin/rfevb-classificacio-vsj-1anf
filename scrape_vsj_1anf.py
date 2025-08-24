# -*- coding: utf-8 -*-
"""
VSJ 1a Nacional Femení — Classificació RFEVB per OBS (amb Playwright)
Guarda:
  C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\classificacio.csv
  C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\classificacio_top3.txt
  C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\classificacio_vsj.txt
"""

import os, sys, io, re, time
import pandas as pd

OUT_DIR   = r"C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF"
CSV_OUT   = os.path.join(OUT_DIR, "classificacio.csv")
TOP3_TXT  = os.path.join(OUT_DIR, "classificacio_top3.txt")
VSJ_TXT   = os.path.join(OUT_DIR, "classificacio_vsj.txt")
TEAM_NAME = "CV Sant Just"
# Colors del club (canvia'ls si cal)
TEAM_PRIMARY = "#0B3A82"   # blau VSJ (exemple)
TEAM_ACCENT  = "#F2C300"   # groc VSJ (exemple)


URL = "https://www.rfevb.com/primera-division-femenina-grupo-b-clasificacion"

def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)

def render_html_with_playwright(url: str, timeout_ms=20000) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="networkidle")
        # espera que aparegui alguna taula
        try:
            page.wait_for_selector("table", timeout=timeout_ms)
        except Exception:
            pass
        html = page.content()
        browser.close()
        return html

def read_tables_from_html(html_text: str):
    # prova lxml i html5lib
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
    team_i = next((i for i,c in enumerate(cols) if any(k in c for k in ["equipo","equip","team"])), min(1,len(cols)-1))
    pts_i  = next((i for i,c in enumerate(cols) if any(k in c for k in ["puntos","points","pts","pt"])), len(cols)-1)
    return pos_i, team_i, pts_i

def save_outputs(df: pd.DataFrame):
    ensure_dirs()
    df = df.dropna(how="all")
    df = normalize_columns(df)
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print("💾 CSV:", CSV_OUT, "files:", len(df))

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

    # Seguiment CV Sant Just
    vsj_row = None
    for _, r in df.fillna("").iterrows():
        row_team = " ".join(map(str, r.values)).lower()
        if TEAM_NAME.lower() in row_team:
            vsj_row = r
            break
    with open(VSJ_TXT, "w", encoding="utf-8") as f:
        if vsj_row is None:
            f.write(f"{TEAM_NAME}: no trobat a la taula\n")
            print(f"ℹ️  {TEAM_NAME} no trobat a la taula.")
        else:
            cols_l = [c.lower() for c in df.columns]
            def find_val(keywords):
                idx = next((i for i,c in enumerate(cols_l) if any(k in c for k in keywords)), None)
                return (str(vsj_row.iloc[idx]).strip() if idx is not None else "")
            pos   = str(vsj_row.iloc[pos_i]).strip()
            team  = str(vsj_row.iloc[team_i]).strip()
            punts = str(vsj_row.iloc[pts_i]).strip()
            pj    = find_val(["jugados","pj"])
            gan   = find_val(["ganados","gan"])
            per   = find_val(["perdidos","perd"])
            f.write(f"{pos} - {team} — Punts: {punts}  PJ:{pj}  G:{gan}  P:{per}\n")
            print("⭐ VSJ:", VSJ_TXT)

def run_once():
    try:
        print(f"➡️  Renderitzant: {URL}")
        html = render_html_with_playwright(URL, timeout_ms=25000)
        tables = read_tables_from_html(html)
        print(f"   → trobades {len(tables)} taules")
        df = pick_standing_table(tables) if tables else None
        if df is not None and not df.empty:
            save_outputs(df)
        else:
            print("⚠️  No s'ha pogut obtenir cap taula de classificació.")
    except Exception as e:
        print("✖️  Error inesperat:", e)

def main_loop(poll_seconds=300):
    while True:
        run_once()
        time.sleep(poll_seconds)

if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        main_loop(300)
