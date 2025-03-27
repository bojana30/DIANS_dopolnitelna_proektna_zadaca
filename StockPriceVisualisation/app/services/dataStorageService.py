import json
from fastapi import APIRouter, WebSocket
from app.database import get_db_connection

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to handle incoming stock data and store it in the database."""
    await websocket.accept()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        while True:
            message = await websocket.receive_text()
            stock_data = json.loads(message)
            
            # Insert data into PostgreSQL
            cursor.execute('''
                INSERT INTO stock_data (symbol, date, close, volume)
                VALUES (%s, %s, %s, %s)
            ''', (stock_data["symbol"], stock_data["date"], stock_data["close"], stock_data["volume"]))
            conn.commit()
            
            print(f"Stored in DB: {stock_data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        conn.close()