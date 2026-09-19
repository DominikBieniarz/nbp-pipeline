"""Tests for fetch_rates — all HTTP calls are mocked, no real network access."""

from datetime import date
import responses
from src.fetch_rates import fetch_rates, _chunk_date_range


def test_chunk_date_range_split_long_span():
    chunks = _chunk_date_range(date(2026, 1, 1), date(2026, 6, 1))
    assert len(chunks) == 2
    assert chunks[0] == (date(2026, 1, 1), date(2026, 4, 3))
    assert chunks[1] == (date(2026, 4, 4), date(2026, 6, 1))


def test_chunk_date_range_single_chunk_when_short():
    chunks = _chunk_date_range(date(2026, 1, 1), date(2026, 1, 31))
    assert chunks == [(date(2026, 1, 1), date(2026, 1, 31))]


@responses.activate
def test_fetch_rates_parses_valid_response():
    responses.add(
        responses.GET,
        "https://api.nbp.pl/api/exchangerates/rates/a/eur/2026-01-01/2026-01-05/?format=json",
        json={
            "table": "A",
            "currency": "euro",
            "code": "EUR",
            "rates": [
                {"no": "001/A/NBP/2026", "effectiveDate": "2026-01-02", "mid": 4.21},
            ],
        },
        status=200,
    )

    rates = fetch_rates("eur", date(2026, 1, 1), date(2026, 1, 5))


    assert len(rates) == 1
    assert rates[0].mid == 4.21


@responses.activate
def test_fetch_rates_returns_empty_list_on_empty_response():
    responses.add(
        responses.GET,
        "https://api.nbp.pl/api/exchangerates/rates/a/eur/2026-01-01/2026-01-05/?format=json",
        json={
            "table": "A",
            "currency": "euro",
            "code": "EUR",
            "rates": [],
        },
        status=200,
    )

    rates = fetch_rates("eur", date(2026, 1, 1), date(2026, 1, 5))


    assert rates == []


@responses.activate
def test_fetch_rates_raises_on_http_error():
    responses.add(
        responses.GET,
        "https://api.nbp.pl/api/exchangerates/rates/a/eur/2026-01-01/2026-01-05/?format=json",
        status=500,
    )

    try:
        fetch_rates("eur", date(2026, 1, 1), date(2026, 1, 5))
        assert False, "Expected an exception to be raised"
    except Exception:
        pass