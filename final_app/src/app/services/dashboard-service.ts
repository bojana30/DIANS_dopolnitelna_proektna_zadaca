import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { WebSocketSubject } from "rxjs/webSocket";

@Injectable({
    providedIn: 'root'
  })
  export class StockService {
    private baseUrl = 'http://localhost:8000/integration';
    private websocket?: WebSocket;
  
    constructor(private http: HttpClient) {}
  
    getStockData(symbol: string, startTime: string): Observable<any> {
      const url = `${this.baseUrl}/get-stock-data/${symbol}?start_time=${startTime}`;
      return this.http.get<any>(url);
    }
  
    followStock(symbol: string): Observable<any> {
      const url = `${this.baseUrl}/follow-stock/${symbol}`;
      return this.http.get<any>(url);
    }

    
  connectToStockUpdates(symbol: string, onMessage: (data: any) => void, onError?: (err: any) => void) {
    const url = `ws://localhost:8000/analysis/ws?symbol=${symbol}`;
    this.websocket = new WebSocket(url);

    this.websocket.onopen = () => console.log("WebSocket connected to:", url);
    
    this.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      if (onError) onError(error);
    };

    this.websocket.onclose = () => console.log("WebSocket closed.");
  }

  disconnectWebSocket() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = undefined;
    }
  }
  }