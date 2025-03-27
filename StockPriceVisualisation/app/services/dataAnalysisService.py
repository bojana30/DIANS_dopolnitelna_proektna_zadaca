from fastapi import APIRouter, WebSocket, HTTPException
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, Optional
from fastapi import Query
import asyncio
from datetime import datetime
import traceback
import json
from app.database import get_db_connection
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
from fastapi.responses import StreamingResponse

router = APIRouter()

async def update_stock_data():
    """Fetches stock data for symbols in the database."""
    while True:    
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all unique stock symbols from the database
        cursor.execute("SELECT DISTINCT symbol FROM stock_data")
        symbols = [row["symbol"] for row in cursor.fetchall()]  # Adjusted to use tuple indexing
        print(f"Fetched symbols: {symbols}")

        conn.close()

        for symbol in symbols:
            try:
                # Fetch real-time stock data
                stock = yf.Ticker(symbol)
                current_price = stock.info["regularMarketPrice"]
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                print(f"Updating stock data for {symbol} at {current_time}")
                print(f"Current Price: {current_price}")

                # Insert the current stock data into the database
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO stock_data (symbol, date, close, volume)
                    VALUES (%s, %s, %s, %s)
                ''', (symbol, current_time, current_price, 0))  # Volume is set to 0 for real-time data
                conn.commit()
                conn.close()
                print(f"Updated stock data for {symbol}")
            except Exception as e:
                print(f"Error updating stock data for {symbol}: {e}")
        await asyncio.sleep(60)

    

# Global variable to store the background task reference
background_task = None

@router.on_event("startup")
async def start_background_task():
    """Starts the background task when the application starts."""
    global background_task
    if not background_task:
        background_task = asyncio.create_task(update_stock_data())
        print("Background task started.")

@router.on_event("shutdown")
async def stop_background_task():
    """Stops the background task when the application shuts down."""
    global background_task
    if background_task:
        background_task.cancel()  # Cancel the background task
        try:
            await background_task  # Wait for the task to finish cleanup
        except asyncio.CancelledError:
            print("Background task cancelled.")


clients = []


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint to send periodic stock trend updates for a specific symbol.
    """
    await websocket.accept()
    clients.append(websocket)
    print(f"WebSocket connection established for symbol: {symbol}")

    try:
        while True:
            # Fetch real-time stock data from yfinance
            try:
                stock = yf.Ticker(symbol)
                current_price = stock.info.get("regularMarketPrice", None)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if current_price is not None:
                    stock_update = {
                        "symbol": symbol,
                        "current_price": current_price,
                        "timestamp": current_time,
                    }
                    # Send the stock update to the client
                    await websocket.send_text(json.dumps(stock_update))
                    print(f"Sent update: {stock_update}")
                else:
                    print(f"No real-time data available for symbol: {symbol}")
                    await websocket.send_text(json.dumps({"error": "No real-time data available"}))
            except Exception as e:
                print(f"Error fetching stock data for {symbol}: {e}")
                await websocket.send_text(json.dumps({"error": str(e)}))

            # Wait for 5 seconds before fetching the next update
            await asyncio.sleep(5)
    except Exception as e:
        traceback.print_exc()  # Print the full traceback for debugging
        print(f"WebSocket connection closed for symbol: {symbol}. Reason: {e}")
    finally:
        clients.remove(websocket)
        print(f"WebSocket connection removed for symbol: {symbol}")