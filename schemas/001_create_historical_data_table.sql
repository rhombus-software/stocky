-- Create stock_historical table with JSONB column
-- Run this migration in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS stock_historical (
    isin TEXT NOT NULL,
    symbol TEXT NOT NULL,
    value JSONB NULL,
    CONSTRAINT stock_historical_pkey PRIMARY KEY (isin)
);

-- Create index on symbol for faster lookups
CREATE INDEX IF NOT EXISTS idx_stock_historical_symbol ON stock_historical(symbol);
