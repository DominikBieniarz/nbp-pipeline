"""Fetch NBP exchange rates for a currency across an arbitrary date range."""

from datetime import date, timedelta
import logging
from pydantic import BaseModel
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


logger = logging.getLogger(__name__)


MAX_RANGE_DAYS = 93 # NBP API limits the maximum range of dates to 93 days. If the range is longer, the API will return an error.


class ExchangeRate(BaseModel):
    no: str
    effectiveDate: date
    mid: float
    currency: str


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
def _fetch_one_chunk(currency: str, date_from: date, date_to: date) -> list[ExchangeRate]:
    """Fetch and validate a single chunk of NBP table-A rates (<=MAX_RANGE_DAYS)."""
    url = (
        f"https://api.nbp.pl/api/exchangerates/rates/a/{currency.lower()}/"
        f"{date_from.isoformat()}/{date_to.isoformat()}/?format=json"
    )
    logger.info("Fetching %s rates from %s to %s", currency.upper(), date_from, date_to)

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    payload = response.json()

    raw_rates = payload.get("rates", [])
    if not raw_rates:
        logger.warning("No rates returned for %s to %s", date_from, date_to)
        return []

    rates = [ExchangeRate(**item, currency=currency.upper()) for item in raw_rates]
    logger.info("Parsed %d rates for %s to %s.", len(rates), date_from, date_to)
    return rates


def fetch_rates(currency: str, date_from: date, date_to: date) -> list[ExchangeRate]:
    """ Fetch NBP table-A exchange rates for `currency` across an arbitrary date range, splitting into <=93-day chunks as the NBP API requires."""
    all_rates: list[ExchangeRate] = []
    for chunk_start, chunk_end in _chunk_date_range(date_from, date_to):
        all_rates.extend(_fetch_one_chunk(currency, chunk_start, chunk_end))
    logger.info("Fetched %d total rates for %s(%s to %s).", len(all_rates), currency.upper(), date_from, date_to)
    return all_rates