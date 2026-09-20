# nbp-pipeline

A small ETL pipeline that fetches historical exchange rates from the National Bank of Poland (NBP) public API, validates and transforms them, and loads them into Google BigQuery.

## What it does

Given a currency and a date range, the pipeline:

1. **Fetches** exchange rates from the [NBP API](https://api.nbp.pl), automatically splitting the request into ≤93-day chunks (the API's hard limit) and retrying transient failures with exponential backoff
2. **Validates** each rate against a schema (Pydantic) before it enters the pipeline
3. **Transforms** the validated data into a pandas DataFrame with proper datetime typing
4. **Saves** the result locally as a Parquet file
5. **Loads** the same data into a BigQuery table

## Tech stack

- **Python 3.13**
- `requests` + `tenacity` — HTTP requests with retry/backoff
- `pydantic` — data validation
- `pandas` + `pyarrow` — transformation and Parquet I/O
- `google-cloud-bigquery` — loading into BigQuery
- `python-dotenv` — configuration via environment variables
- `pytest` + `responses` — testing, with all external calls mocked

## Project structure

```
nbp-pipeline/
├── src/
│   ├── main.py          # CLI entry point — wires the whole pipeline together
│   ├── fetch_rates.py   # NBP API client: chunking, retry, validation
│   ├── storage.py       # DataFrame conversion, Parquet, BigQuery load
│   └── config.py        # Loads GCP project/dataset from .env
├── tests/
│   ├── test_fetch_rates.py
│   └── test_storage.py
├── data/                 # local Parquet output (gitignored)
├── .env.example          # template for required environment variables
├── requirements.txt
└── pyproject.toml
```

## Setup

**1. Clone and create a virtual environment**

```bash
git clone https://github.com/DominikBieniarz/nbp-pipeline.git
cd nbp-pipeline
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Configure environment variables**

```bash
cp .env.example .env
```

Then fill in `.env` with your own GCP project and BigQuery dataset:

```
GCP_PROJECT_ID=your-gcp-project-id
BQ_DATASET=your-bigquery-dataset
```

**3. Authenticate with Google Cloud**

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project <your-gcp-project-id>
```

The BigQuery dataset must already exist; the destination table is created automatically on first load.

## Usage

Run the full pipeline from the project root:

```bash
python -m src.main \
  --currency eur \
  --date-from 2026-01-01 \
  --date-to 2026-01-31 \
  --output data/eur_rates.parquet \
  --table eur_rates
```

Run it as a module (`python -m src.main`), not as a script (`python src/main.py`) — the latter breaks the package's internal imports.

| Argument | Description |
|---|---|
| `--currency` | Currency code, e.g. `eur`, `usd` |
| `--date-from` | Start date, `YYYY-MM-DD` |
| `--date-to` | End date, `YYYY-MM-DD` |
| `--output` | Local path for the Parquet file |
| `--table` | Destination BigQuery table name |

## Running tests

```bash
pytest tests/ -v
```

All 9 tests run offline — HTTP calls to the NBP API and the BigQuery client are both mocked, so the suite never touches the network or a real GCP project.

## Design notes

A few decisions worth calling out, since they're the actual point of the project rather than incidental detail:

- **Chunking, not a single request.** The NBP API rejects any request spanning more than 93 days, so `fetch_rates` transparently splits longer ranges into valid chunks and stitches the results back together — the caller never needs to know the limit exists.
- **Retry only where it makes sense.** Each chunk request retries up to 3 times with exponential backoff on network/HTTP failures — but an HTTP error still raises after retries are exhausted, rather than failing silently and returning incomplete data.
- **Validation at the boundary.** Every record from the API is parsed into a Pydantic model before anything else touches it, so a malformed response fails loudly and immediately, not three steps later as a confusing type error.
- **Config vs. parameters.** GCP project and dataset live in environment variables (constant for a given environment); currency, date range, and table name are CLI arguments (different on every run). Nothing GCP-specific is hardcoded in the source.

## Known limitations

- `load_to_bigquery` currently appends data (BigQuery's default `WRITE_APPEND`). Running the pipeline twice for an overlapping date range will duplicate rows — there's no deduplication logic yet.
- Only NBP table A (average rates) is supported.

## Possible next steps

- Deduplicate on load, or switch to `WRITE_TRUNCATE` for a given partition
- Orchestrate with Airflow instead of manual CLI runs
- Support additional NBP tables (B, C)