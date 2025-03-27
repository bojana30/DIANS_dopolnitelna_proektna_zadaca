import { Component, OnDestroy, OnInit } from "@angular/core";
import { StockService } from "../services/dashboard-service";
import { StockData } from "../models/stock-data";
import { log } from "console";

@Component({
    selector: 'dashboard-component',
    templateUrl: './dashboard-component.html',
    styleUrls: ['./dashboard-component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {

    symbol: string = 'AAPL'; 
    startDate: string = '2025-03-20'; 
    private isConnected: boolean = false;
    realTimeData : any = [];

    constructor(private stockService: StockService) {}

    ngOnInit(): void {
       this.fetchData();
       this.startRealTimeUpdates();
    }

    public realTimePriceChart: { data: any[]; layout: any } = {
        data: [],
        layout: {
          width: 550,
          height: 300,
          title: { text: 'Real-Time Stock Price', font: { size: 18, color: 'black' } }
        }
      };
    
      public realTimeVolumeChart: { data: any[]; layout: any } = {
        data: [],
        layout: {
          title: { text: 'Real-Time Trading Volume', font: { size: 18, color: 'black' } },
          width: 550,
          height: 300
        }
      };
    
      public historicalPriceChart: { data: any[]; layout: any } = {
        data: [], 
        layout: {
            width: 550,
            height: 300,
            title: { text: 'Historical Stock Price', font: { size: 18, color: 'black' } }
        }
    };
    
    public historicalVolumeChart: { data: any[]; layout: any } = {
        data: [], 
        layout: {
            title: { text: 'Historical Trading Volume', font: { size: 18, color: 'black' } },
            width: 550,
            height: 300
        }
    };
    
      fetchData() {
        this.fetchHistoricalData();
        this.startRealTimeUpdates();
      }

    
      fetchHistoricalData() {
        this.stockService.getStockData(this.symbol, this.startDate).subscribe(data => {

        const dates = data?.data.map((item : any) => item.date);  
        const prices = data?.data.map((item : any) => item.close);
        const volumes = data?.data.map((item : any) => item.volume);

        this.historicalPriceChart.data = [{
            x: dates,       
            y: prices,    
            type: 'scatter',
            mode: 'lines+markers',
            marker: { color: 'orange' }
        }];

        this.historicalVolumeChart.data = [{
            x: dates,    
            y: volumes,     
            type: 'bar',
            marker: { color: 'purple' }
        }];
        });
      }

      followStock() {
        if (!this.symbol) return;

        this.stockService.followStock(this.symbol).subscribe(response => {
            console.log('Stock followed successfully:', response);
        }, error => {
            console.error('Error following stock:', error);
        });
    }

    ngOnDestroy(): void {
        this.stopRealTimeUpdates();
    }

    startRealTimeUpdates() {
        if (!this.isConnected) {
          this.stockService.connectToStockUpdates(this.symbol, (data: any) => {
            if (data.error) {
              console.error("WebSocket error:", data.error);
            } else {
                console.log(data)
              this.realTimeData.push(data)

                const dates = this.realTimeData.map((item : any) => item.timestamp);  
                const prices = this.realTimeData.map((item : any) => item.current_price);
    
                this.realTimePriceChart.data = [{
                    x: dates,       
                    y: prices,    
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: 'orange' }
                }];
        
                this.realTimeVolumeChart.data = [{
                    x: dates,    
                    y: prices,     
                    type: 'bar',
                    marker: { color: 'purple' }
                }];
            }
          });
          this.isConnected = true;
        }
      }
    
      stopRealTimeUpdates() {
        this.stockService.disconnectWebSocket();
        this.isConnected = false;
      }
}
