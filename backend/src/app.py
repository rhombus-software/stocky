from fastapi import FastAPI
from pydantic import BaseModel
from src.handlers.get_symbols_price import get_symbols_price

app = FastAPI(title="Stocky Backend")


class SymbolsPayload(BaseModel):
	symbols: list[str]
	country: str = "US"  # Default country is set to "US"


@app.get("/")
async def read_root():
	return {"message": "Hello from Stocky backend (src.app)!"}

@app.post("/symbols")
async def read_symbols(payload: SymbolsPayload):
	symbols = [s.upper() for s in payload.symbols] if payload.country == "US" else [s.upper() + ".NS" for s in payload.symbols]
	return get_symbols_price(symbols)


@app.get("/health")
async def health_check():
	return {"status": "ok"}
