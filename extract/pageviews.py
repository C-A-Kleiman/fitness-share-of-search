"""Pull daily Wikipedia pageviews and save them as monthly CSV files.

Usage:
  python extract/pageviews.py --mode backfill      # one time: full history
  python extract/pageviews.py --mode incremental   # daily: last 7 days
"""
import argparse
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

ARTICLES_FILE = Path("dbt_project/seeds/articles.csv")
RAW_DIR = Path("data/raw/pageviews")
API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
# Wikimedia requires a descriptive User-Agent with contact info
HEADERS = {"User-Agent": "fitness-share-of-search/1.0 (ckleiman905@gmail.com)"}
ACCESS_TYPES = ["desktop", "mobile-web", "mobile-app"]
BACKFILL_START = date(2015, 7, 1)  # earliest date the API has
INCREMENTAL_DAYS = 7               # re-pull a week to catch late or revised data


def fetch(project, article, access, start, end):
    """Return a list of daily rows for one article + access type."""
    title = requests.utils.quote(article.replace(" ", "_"), safe="")
    url = f"{API}/{project}/{access}/user/{title}/daily/{start:%Y%m%d}/{end:%Y%m%d}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code == 404:  # no data for this range, e.g. article too new
        print(f"  no data: {project} | {article} | {access}")
        return []
    resp.raise_for_status()
    rows = []
    for item in resp.json()["items"]:
        ts = item["timestamp"]  # format: YYYYMMDD00
        rows.append({
            "project": project,
            "article": article,
            "access": access,
            "view_date": f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}",
            "views": item["views"],
        })
    return rows


def write_months(df, start, end):
    """Save rows into one CSV per month, replacing any rows in the pulled window.

    Re-running for the same dates gives the same files (idempotent).
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df["month"] = df["view_date"].str[:7]
    for month, new_rows in df.groupby("month"):
        path = RAW_DIR / f"{month}.csv"
        new_rows = new_rows.drop(columns="month")
        if path.exists():
            old = pd.read_csv(path)
            in_window = (old["view_date"] >= start.isoformat()) & (old["view_date"] <= end.isoformat())
            new_rows = pd.concat([old[~in_window], new_rows])
        new_rows = new_rows.sort_values(["project", "article", "access", "view_date"])
        new_rows.to_csv(path, index=False)
        print(f"  wrote {path} ({len(new_rows):,} rows)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["backfill", "incremental"], default="incremental")
    mode = parser.parse_args().mode

    end = date.today() - timedelta(days=1)
    start = BACKFILL_START if mode == "backfill" else end - timedelta(days=INCREMENTAL_DAYS - 1)
    print(f"Mode: {mode} | {start} to {end}")

    articles = pd.read_csv(ARTICLES_FILE)
    rows = []
    for a in articles.itertuples():
        for access in ACCESS_TYPES:
            rows += fetch(a.project, a.article, access, start, end)
            time.sleep(0.1)  # be polite to the API

    if not rows:
        print("No rows fetched; nothing written.")
        return
    write_months(pd.DataFrame(rows), start, end)
    print(f"Done: {len(rows):,} rows fetched.")


if __name__ == "__main__":
    main()