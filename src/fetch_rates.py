"""Fetch NBP exchange rates for a currency across an arbitrary date range."""

from datetime import date, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import requests

MAX_RANGE_DAYS = 93 # NBP API limits the maximum range of dates to 93 days. If the range is longer, the API will return an error.


def _chunk_date_range(date_from: date, date_to: date) -> list[tuple[date, date]]:
    """ Splits the date range into chunks of MAX_RANGE_DAYS days. """
    chunks = []
    current_start = date_from
    while current_start <= date_to:
        current_end = min(current_start + timedelta(days=MAX_RANGE_DAYS - 1), date_to)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return chunks


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_one_chunk(currency: str, date_from: date, date_to: date) -> dict:
    url = f"https://api.nbp.pl/api/exchangerates/rates/a/{currency}/{date_from.isoformat()}/{date_to.isoformat()}/?format=json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_rates(currency: str, date_from: date, date_to: date) -> list[dict]:
    """ Fetch NBP table-A exchange rates for `currency` across an arbitrary date range, splitting into <=93-day chunks as the NBP API requires."""
    all_rates: list[dict] = []
    for chunk_start, chunk_end in _chunk_date_range(date_from, date_to):
        data = _fetch_one_chunk(currency, chunk_start, chunk_end)
        all_rates.extend(data['rates'])
    return all_rates