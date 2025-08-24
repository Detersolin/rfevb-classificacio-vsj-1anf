# -*- coding: utf-8 -*-
"""
VSJ 1a Nacional Femení — RFEVB Classificació per OBS

Guarda a:
  C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\classificacio.csv
  C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\classificacio_top3.txt
  C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF\classificacio_vsj.txt   (resum CV Sant Just)
"""

import os, sys, io, time, re
import pandas as pd
import requests

OUT_DIR   = r"C:\Guillem\Temporada 25-26\Overlay\VSJ\1ANF"
CSV_OUT   = os.path.join(OUT_DIR, "classificacio.csv")
TOP3_TXT  = os.path.join(OUT_DIR, "classificacio_top3.txt")
VSJ_TXT   = os.path.join(OUT_DIR, "classificacio_vsj.txt")
TEAM_NAME = "CV Sant Just"  # equip a ressaltar

# URL oficial de la RFEVB (actualitza-la si canviés)
URLS = [
    "https://www.rfevb.com/primera-division-femenina-grupo-b-clasificacion",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def read_html_tables(html_text: str):
    """Intenta llegir taules amb lxml i, si cal, html5lib."""
    tries = [("lxml", "lxml"), ("html5lib", "html5lib")]
    for label, flavor in tries:
        try:
            tables = pd.read_html(io.StringIO(html_text), flavor=flavor)
            if tables:
                return tables
        except Exception:
            continue
    return []

def score_table(df: pd.DataFrame) -> int:
    """Heurística per detectar taula de classificació."""
    kws = ["pos", "equipo", "equip", "team", "puntos", "points", "pj", "jug", "gan", "perd", "sets"]
    cols = [str(c).lower() for c in df.columns]
    score = 0
    for c in cols:
        for k in kws:
            if k in c:
                score += 1
    # més files => més puntuació
    score += min(len(df), 20)
    return score

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplana MultiIndex i neteja noms de columna."""
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

def pick_standing_table(tables):
    """Tria la millor taula."""
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

def fetch_table():
    for url in URLS:
        try:
            print(f"➡️  Baixant: {url}")
            r = requests.get(url, headers=HEADERS, timeout=25)
            r.raise_for_status()
            html = r.text
            tables = read_html_tables(html)
            print(f"   → trobades {len(tables)} taules")
            if not tables:
                continue
            df = pick_standing_table(tables)
            if df is not None and not df.empty:
                return df
            else:
                print("   ⚠️  cap taula vàlida en aquesta URL.")
        except Exception as e:
            print(f"   ✖️  Error: {e}")
    return None

def guess_columns(df: pd.DataFrame):
    """Endevina columnes clau: posició, equip, punts."""
    cols = [c.lower() for c in df.columns]
    # pos
    pos_idx = next((i for i,c in enumerate(cols) if re.search(r"\bpos", c)), 0)
    # equip
    team_idx = next((i for i,c in enumerate(cols) if any(k in c for k in ["equipo","equip","team"])), 1 if len(cols)>1 else 0)
    # punts
    pts_idx = next((i for i,c in enumerate(cols) if any(k in c for k in ["puntos","points","pts","pt"])), len(cols)-1)
    return pos_idx, team_idx, pts_idx

def save_outputs(df: pd.DataFrame):
    os.makedirs(OUT_DIR, exist_ok=True)

    # neteja bàsica
    df = df.dropna(how="all")
    df = normalize_columns(df)

    # guarda CSV
    df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    print("💾 CSV:", CSV_OUT, "files:", len(df))

    # TOP-3
    pos_i, team_i, pts_i = guess_columns(df)
    top = df.iloc[:3].fillna("")
    lines = []
    for _, r in top.iterrows():
        try:
            pos   = str(r.iloc[pos_i]).strip()
            team  = str(r.iloc[team_i]).strip()
            punts = str(r.iloc[pts_i]).strip()
        except Exception:
            pos = team = punts = ""
        lines.append(f"{pos} - {team} ({punts})")
    with open(TOP3_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("📝 TOP3:", TOP3_TXT)

    # Resaltat CV Sant Just
    vsj_row = None
    for _, r in df.fillna("").iterrows():
        row_team = " ".join(map(str, r.values)).lower()
        if TEAM_NAME.lower() in row_team:
            vsj_row = r
            break

    with open(VSJ_TXT, "w", encoding="utf-8") as f:
        if vsj_row is None:
            f.write(f"{TEAM_NAME}: no trobat a la taula\n")
            print(f"ℹ️  {TEAM_NAME} no trobat a la taula (encara).")
        else:
            try:
                pos   = str(vsj_row.iloc[pos_i]).strip()
                team  = str(vsj_row.iloc[team_i]).strip()
                punts = str(vsj_row.iloc[pts_i]).strip()
                # Intenta també PJ/Gan/Perd si existeixen
                cols_l = [c.lower() for c in df.columns]
                def v(col_keywords, default=""):
                    idx = next((i for i,c in enumerate(cols_l) if any(k in c for k in col_keywords)), None)
                    return str(vsj_row.iloc[idx]).strip() if idx is not None else default
                pj   = v(["jugados","pj"])
                gan  = v(["ganados","gan"])
                per  = v(["perdidos","perd"])
                f.write(f"{pos} - {team} — Punts: {punts}  PJ:{pj}  G:{gan}  P:{per}\n")
                print("⭐ VSJ:", VSJ_TXT)
            except Exception:
                f.write(f"{TEAM_NAME}: trobat, però no s'han pogut llegir totes les columnes\n")

def run_once():
    df = fetch_table()
    if df is not None and not df.empty:
        save_outputs(df)
    else:
        print("⚠️  No s'ha pogut obtenir cap taula de classificació.")

def main_loop(poll_seconds=300):
    while True:
        try:
            run_once()
        except Exception as e:
            print("✖️  Error inesperat:", e)
        time.sleep(poll_seconds)

if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        main_loop(300)
