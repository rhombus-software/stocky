# Historical Data Storage with JSONB

This documentation covers the JSONB implementation for storing historical stock data in PostgreSQL via Supabase.

## Overview

The updated system allows you to:
1. **Fetch** historical stock data from yfinance
2. **Convert** DataFrames to JSON/JSONB format
3. **Store** data in PostgreSQL with symbol as primary key
4. **Query** and retrieve the data with full error handling

## Database Schema

```sql
CREATE TABLE historical_data (
    symbol TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Columns:
- **symbol** (TEXT, PK): Stock ticker symbol (e.g., "AAPL", "GOOGL")
- **data** (JSONB): Historical OHLC data in JSON format
- **created_at**: Record creation timestamp
- **updated_at**: Last update timestamp

## Setup Instructions

### 1. Create the Database Table

Run the SQL migration in Supabase:
```sql
-- See: migrations/001_create_historical_data_table.sql
CREATE TABLE IF NOT EXISTS historical_data (
    symbol TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### 2. Environment Setup

Ensure your `.env` file has:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Usage

### Basic Usage: Load and Store Data

```python
from jobs.HistoricDataLoder import HistoricDataLoader
from datetime import datetime, timedelta

# Initialize loader
loader = HistoricDataLoader(catalog="ind-nse-stocks.csv")

# Define date range
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

# Load and store data
results = loader.load_data(
    start_date=start_date,
    end_date=end_date,
    table_name="historical_data"
)

# Check results
print(f"Loaded: {results['loaded']}, Failed: {results['failed']}")
for error in results['errors']:
    print(f"Error: {error}")
```

### Retrieve Data

```python
from shared.HistoricalDataReader import HistoricalDataReader

reader = HistoricalDataReader()

# Get all data for a symbol
df = reader.get_symbol_data("AAPL")
print(df.head())

# Get all symbols in database
symbols = reader.get_all_symbols()

# Delete specific symbol's data
reader.delete_symbol_data("AAPL")
```

## Data Format (JSONB)

The data is stored as an array of records:
```json
[
  {
    "Date": "2023-01-01T00:00:00.000Z",
    "Open": 150.5,
    "High": 151.2,
    "Low": 150.1,
    "Close": 150.9,
    "Volume": 1000000
  },
  ...
]
```

## Error Handling

The implementation includes comprehensive error handling:

1. **Catalog Loading Errors**
   - Missing or invalid catalog files
   - CSV reading errors

2. **Data Fetching Errors**
   - Network failures
   - Invalid ticker symbols
   - Empty data responses

3. **Database Errors**
   - Connection failures
   - JSONB conversion errors
   - Insert/upsert failures

Each error is:
- Logged with details
- Tracked in results dictionary
- Includes symbol reference
- Allows partial success (other symbols continue loading)

## Return Values

### load_data() returns:
```python
{
    "success": bool,           # Overall operation success
    "total_symbols": int,      # Total symbols processed
    "loaded": int,             # Successfully loaded
    "failed": int,             # Failed to load
    "errors": [str, ...]       # Error messages
}
```

## Performance Considerations

1. **Batch Operations**: Consider loading data in batches for large symbol sets
2. **Date Ranges**: Use specific date ranges rather than "period='max'" for faster operations
3. **Indexing**: Indexes are created on `symbol` and `updated_at` for quick queries
4. **JSONB Queries**: PostgreSQL JSON operators can be used for advanced filtering

## Advanced Features

### Query Historical Data with Filters

```python
reader = HistoricalDataReader()
df = reader.get_symbol_with_filters(
    symbol="AAPL",
    filters={"Close": 150.0}  # Custom filters
)
```

### Monitor Updates

The `updated_at` timestamp tracks when data was last refreshed:

```python
# Get recently updated data
response = db.client.table("historical_data")\
    .select("*")\
    .order("updated_at", desc=True)\
    .limit(10)\
    .execute()
```

## Troubleshooting

### No data returned for symbol
- Check if symbol exists in catalog
- Verify yfinance has data for that symbol
- Check date range (too narrow may return empty)

### JSONB errors
- Ensure PostgreSQL version supports JSONB (9.4+)
- Verify Supabase version is recent enough
- Check DataFrame to JSON conversion

### Connection errors
- Verify SUPABASE_URL and SUPABASE_KEY in .env
- Check network connectivity
- Ensure Supabase project is active

## Files Modified/Created

- `shared/DB.py` - Added `write_jsonb_to_table()` method
- `jobs/HistoricDataLoder.py` - Complete rewrite with JSONB support
- `shared/HistoricalDataReader.py` - New file for querying data
- `migrations/001_create_historical_data_table.sql` - Database schema
- `examples/load_historical_data_example.py` - Usage example
