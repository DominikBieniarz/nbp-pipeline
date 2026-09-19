"Test storage functions."

from datetime import date
from src.fetch_rates import ExchangeRate
from src.storage import rates_to_dataframe, save_to_parquet, load_to_bigquery
import pandas as pd
from unittest.mock import patch, MagicMock


def _sample_rates() -> list[ExchangeRate]:
    """Return a sample list of ExchangeRate objects for testing."""
    return [
        ExchangeRate(no="001/A/NBP/2026", effectiveDate=date(2026, 1, 2), mid=4.21, currency="EUR"),
        ExchangeRate(no="002/A/NBP/2026", effectiveDate=date(2026, 1, 3), mid=4.22, currency="EUR"),
        ExchangeRate(no="003/A/NBP/2026", effectiveDate=date(2026, 1, 4), mid=4.23, currency="EUR"),
    ]


def test_rates_to_dataframe():
    rates = _sample_rates()
    df = rates_to_dataframe(rates)

    assert list(df.columns) == ["no", "effectiveDate", "mid", "currency"]
    assert pd.api.types.is_datetime64_any_dtype(df["effectiveDate"])
    assert df["mid"].iloc[0] == 4.21


def test_save_to_parquet_round_trip(tmp_path):
    rates = _sample_rates()
    df = rates_to_dataframe(rates)

    parquet_path = tmp_path / "eur_rates.parquet"
    save_to_parquet(df, parquet_path)

    read_back = pd.read_parquet(parquet_path)

    assert df["effectiveDate"].dt.date.equals(read_back["effectiveDate"].dt.date)
    assert df["mid"].equals(read_back["mid"])


def test_save_to_parquet_creates_missing_directories(tmp_path):
    rates = _sample_rates()
    df = rates_to_dataframe(rates)

    nested_path = tmp_path / "nested" / "dir" / "eur_rates.parquet"
    save_to_parquet(df, nested_path)

    assert nested_path.exists()


@patch("src.storage.PROJECT_ID", "test-project")
@patch("src.storage.BIGQUERY_DATASET", "test_dataset")
@patch("src.storage.bigquery.Client")
def test_load_to_bigquery_builds_correct_table_id(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    rates = _sample_rates()
    df = rates_to_dataframe(rates)

    load_to_bigquery(df, "eur_rates")

    assert mock_client.load_table_from_dataframe.call_args[0][1] == "test-project.test_dataset.eur_rates"
    mock_client.load_table_from_dataframe.return_value.result.assert_called_once() 