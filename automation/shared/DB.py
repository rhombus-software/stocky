import io
import os
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

try:
    from supabase import create_client
except ImportError:  # pragma: no cover - handled at runtime when dependency is absent
    create_client = None


class DB:
    """Thin wrapper around a Supabase client with CSV helpers for storage."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        client: Any | None = None,
        bucket: str | None = None,
    ) -> None:
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")

        if client is not None:
            self.client = client
        elif self.url and self.key:
            if create_client is None:
                raise ModuleNotFoundError(
                    "The 'supabase' package is not installed. Add it to your project dependencies."
                )
            self.client = create_client(self.url, self.key)
        else:
            raise ValueError(
                "Supabase connection requires a URL and key, or a prebuilt client instance."
            )

        self.bucket = bucket
        self.storage = self.client.storage

    def get_bucket(self, bucket_name: str | None = None):
        target_bucket = bucket_name or self.bucket
        if target_bucket is None:
            raise ValueError("A bucket name must be provided or set during initialization.")
        return self.storage.from_(target_bucket)

    def read_csv(
        self,
        bucket_name: str,
        file_path: str,
        *,
        encoding: str = "utf-8",
    ) -> pd.DataFrame:
        blob = self.get_bucket(bucket_name).download(file_path)
        csv_text = blob.decode(encoding) if isinstance(blob, (bytes, bytearray)) else str(blob)
        return pd.read_csv(io.StringIO(csv_text))

    def write_csv(
        self,
        bucket_name: str,
        file_path: str,
        data: pd.DataFrame | Iterable[dict[str, Any]],
        *,
        encoding: str = "utf-8",
    ) -> dict[str, Any]:
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(list(data))

        buffer = io.StringIO()
        df.to_csv(buffer, index=False, encoding=encoding)

        csv_bytes = buffer.getvalue().encode(encoding)
        return self.get_bucket(bucket_name).upload(
            file_path,
            csv_bytes,
            {"contentType": "text/csv", "upsert": "true"},
        )

    def _flatten_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flatten MultiIndex columns to strings."""
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ["_".join(str(col).strip() for col in cols if str(col).strip()) 
                         for cols in df.columns.values]
        return df

    def write_jsonb_to_table(
        self,
        table_name: str,
        isin: str,
        symbol: str,
        value: dict[str, Any] | list[dict[str, Any]] | pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Write historical data as JSONB to a PostgreSQL table.
        
        :param table_name: The name of the table (e.g., 'historical_data')
        :param isin: The stock ISIN (primary key)
        :param symbol: The stock ticker symbol
        :param value: JSON-compatible data or a DataFrame to store
        :return: The response from the insert operation
        """
        return self.write_jsonb_batch_to_table(
            table_name,
            [(isin, symbol, value)],
        )

    def write_jsonb_batch_to_table(
        self,
        table_name: str,
        records: list[tuple[str, str, dict[str, Any] | list[dict[str, Any]] | pd.DataFrame]],
    ) -> dict[str, Any]:
        """
        Write multiple historical data records as JSONB to a PostgreSQL table in a single batch.
        
        :param table_name: The name of the table (e.g., 'historical_data')
        :param records: List of (isin, symbol, value) tuples
        :return: The response from the batch insert operation
        """
        try:
            batch_records = []
            for isin, symbol, value in records:
                # Convert DataFrame to dict if needed
                if isinstance(value, pd.DataFrame):
                    # Flatten MultiIndex columns to prevent tuple keys
                    value = self._flatten_column_names(value)
                    value = value.reset_index().to_dict('records')

                batch_records.append({
                    "isin": isin,
                    "symbol": symbol,
                    "value": value,
                })

            if not batch_records:
                return {}

            response = self.client.table(table_name).upsert(
                batch_records,
                on_conflict="isin",
            ).execute()
            return response.data if response else {}
        except Exception as exc:
            raise ValueError(
                f"Error writing batch JSONB data to table {table_name}: {exc}"
            ) from exc

    def clear_table(self, table_name: str) -> None:
        """Delete all rows from a table before starting a new load."""
        try:
            self.client.table(table_name).delete().neq("isin", "").execute()
        except Exception as exc:
            raise ValueError(
                f"Error clearing table {table_name}: {exc}"
            ) from exc

    def read_symbol_bulk(
        self,
        table_name: str,
        symbol: str,
    ) -> dict[str, Any] | None:
        """
        Read historical data from a PostgreSQL table as JSONB.
        
        :param table_name: The name of the table (e.g., 'historical_data')
        :param symbol: The stock symbol (primary key)
        :return: The data as a dict or None if not found
        """
        try:
            response = self.client.table(table_name).select("value").in_("symbol", [symbol]).execute()
            if response and response.data:
                return response.data[0].get("value")
            return None
        except Exception as exc:
            raise ValueError(
                f"Error reading JSONB data for {symbol} from table {table_name}: {exc}"
            ) from exc

# db = DB()  # Create a default DB instance using environment variables
# df = db.read_csv("stock_lists", "ind-nse-stocks.csv")
# print(df.head())
# db.write_csv("stock_lists", "example.csv", df.head())