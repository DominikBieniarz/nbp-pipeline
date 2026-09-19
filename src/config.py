"""Load environment-specific configuration from a .env file."""

from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env file

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BQ_DATASET")