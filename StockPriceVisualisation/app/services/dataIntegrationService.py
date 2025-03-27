from fastapi import APIRouter, HTTPException, Query
import yfinance as yf
import json
import asyncio
import websockets
from app.database import get_db_connection  # Import your database connection function
from datetime import datetime  # Import datetime module
import traceback  # Import traceback module for debugging
import pandas as pd  # Import pandas library for data manipulation

# Create a router instance
router = APIRouter()

async def send_stock_data(stock_data):
    async with websockets.connect("ws://localhost:8000/storage/ws") as websocket:
        await websocket.send(json.dumps(stock_data))
        print(f"Sent to WebSocket: {stock_data}")

@router.get("/follow-stock/{symbol}")
async def fetch_stock(symbol: str):
    """
    Fetches stock market data from Yahoo Finance, adds it to the database,
    and sends the latest data via WebSocket.
    """
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1wk", interval="1m")  # Fetch 7 days of minute-level data

        if data.empty:
            return {"error": "Invalid stock symbol or no data available"}

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Add data to the database
        for timestamp, row in data.iterrows():
            # Convert numpy types to native Python types
            close = float(row["Close"]) if not pd.isna(row["Close"]) else None
            volume = int(row["Volume"]) if not pd.isna(row["Volume"]) else None

            cursor.execute('''
                INSERT INTO stock_data (symbol, date, close, volume)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', (symbol, timestamp, close, volume))

        conn.commit()
        conn.close()

        # Get the latest stock data
        latest = data.iloc[-1]
        stock_data = {
            "symbol": symbol,
            "timestamp": int(latest.name.timestamp()),  # Convert the date to a Unix timestamp
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"])
        }

        # Send the latest data via WebSocket
        await send_stock_data(stock_data)

        return {"message": f"Stock {symbol} followed successfully", "status": "success", "data": stock_data}
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        traceback.print_exc()  # Print the full traceback for debugging
        return {"error": str(e)}

@router.get("/get-stock-data/{symbol}")
def get_stock_data(symbol: str, start_time: datetime = Query(...)):
    """
    Fetches all stock data for a specific symbol from the database
    starting from a specified time to the present.
    """
    print(f"Fetching data for symbol: {symbol} from {start_time}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query the database for the specified symbol and time range
        query = """
        SELECT symbol, date, close, volume
        FROM stock_data
        WHERE symbol = %s AND date >= %s
        ORDER BY date ASC
        """
        cursor.execute(query, (symbol, start_time))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            raise HTTPException(status_code=404, detail="No data found for the specified symbol and time range")

        # Format the results as a list of dictionaries
        result = [
            {"symbol": row["symbol"], "date": row["date"], "close": row["close"], "volume": row["volume"]}
            for row in rows
        ]
        return {"symbol": symbol, "data": result}
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        traceback.print_exc()  # Print the full traceback for debugging
        raise HTTPException(status_code=500, detail=str(e))