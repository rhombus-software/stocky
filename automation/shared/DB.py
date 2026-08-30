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

# db = DB()  # Create a default DB instance using environment variables
# df = db.read_csv("stock_lists", "ind-nse-stocks.csv")
# print(df.head())
# db.write_csv("stock_lists", "example.csv", df.head())