"""CLI entry point for the NBP exchange rate pipeline."""


import argparse
from datetime import date
import logging
from src.fetch_rates import fetch_rates
from src.storage import save_to_parquet, load_to_bigquery, rates_to_dataframe


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def parse_args() -> argparse.Namespace:
    "Parse command-line arguments"
    parser = argparse.ArgumentParser(description="NBP exchange rate pipeline")
    parser.add_argument("--currency", required=True, help="Currency code (e.g., eur, usd)")
    parser.add_argument("--date-from", required=True, type=date.fromisoformat, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--date-to", required=True, type=date.fromisoformat, help="End date in YYYY-MM-DD format")
    parser.add_argument("--output", required=True, help="Path to save the local Parquet file")
    parser.add_argument("--table", required=True, help="BigQuery table name to load into")
    return parser.parse_args()


def main() -> None:
    args = parse_args()


    rates = fetch_rates(args.currency, args.date_from, args.date_to)
    df = rates_to_dataframe(rates)
    save_to_parquet(df, args.output)
    load_to_bigquery(df, args.table)


if __name__ == "__main__": 
    main()