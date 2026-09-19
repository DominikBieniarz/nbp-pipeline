"""Save NBP exchange rates to a local parquet file."""

from google.cloud import bigquery
from pathlib import Path
import pandas as pd
from src.fetch_rates import ExchangeRate
import logging

logger = logging.getLogger(__name__)


def rates_to_dataframe(rates: list[ExchangeRate]) -> pd.DataFrame:
    """Convert a list of ExchangeRate objects to a pandas DataFrame."""
    data_dicts = [rate.model_dump() for rate in rates]
    df = pd.DataFrame(data_dicts)

    df['effectiveDate'] = pd.to_datetime(df['effectiveDate'])

    return df


def save_to_parquet(df: pd.DataFrame, path:str) -> None:
    """Save the DataFrame to a parquet file."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False)

    logger.info("Saved %d rates to parquet file at %s", len(df), file_path)


def load_to_bigquery(df: pd.DataFrame, table_id: str) -> None:
    """Load the DataFrame to a BigQuery table."""
    client = bigquery.Client(project="REDACTED_PROJECT_ID")

    job = client.load_table_from_dataframe(df, table_id)
    job.result()

    logger.info("Loaded %d rates to BigQuery table %s", len(df), table_id)
