"""Publish dbt mart tables to Google Sheets for Tableau Public."""
import json
import os

import duckdb
import gspread

SHEET_ID = "1furqHakB2IWCHyXMVtfZcXEP0KZUw5pJr2GOkj6-ROo"
TABLES = ["fct_weekly_share_of_search", "fct_event_impact"]


def get_client():
    # On GitHub Actions the credentials come from a secret; locally from the file
    if "GOOGLE_CREDS" in os.environ:
        return gspread.service_account_from_dict(json.loads(os.environ["GOOGLE_CREDS"]))
    return gspread.service_account(filename="google_creds.json")


def main():
    con = duckdb.connect("dbt_project/fitness.duckdb", read_only=True)
    sheet = get_client().open_by_key(SHEET_ID)
    for table in TABLES:
        df = con.sql(f"select * from {table}").df().astype(str)
        try:
            ws = sheet.worksheet(table)
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet(title=table, rows=1, cols=1)
        ws.clear()
        ws.update([df.columns.tolist()] + df.values.tolist(), value_input_option="USER_ENTERED")
        print(f"Published {table}: {len(df):,} rows")


if __name__ == "__main__":
    main()