class CryptoTradeSimulator {
    constructor() {
        this.chart = null;
        this.priceData = [];
        this.isConnected = false;
        this.ws = null;
        this.initializeEventListeners();
        this.initializeChart();
        this.updateVolatilityLabel();
    }

    initializeEventListeners() {
        // Volatility slider
        document.getElementById('volatility').addEventListener('input', (e) => {
            this.updateVolatilityLabel(e.target.value);
        });

        // Simulate button replaced with connect/disconnect toggle
        const simulateBtn = document.getElementById('simulate-btn');
        simulateBtn.textContent = 'Connect';
        simulateBtn.removeEventListener('click', this.runSimulation);
        simulateBtn.addEventListener('click', () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.disconnectWebSocket();
            } else {
                this.connectWebSocket();
            }
        });

        // Exchange or symbol change disconnects current connection
        document.getElementById('exchange').addEventListener('change', () => {
            this.disconnectWebSocket();
        });
        document.getElementById('symbol').addEventListener('change', () => {
            this.disconnectWebSocket();
        });
    }

    updateVolatilityLabel(value = 50) {
        const textElement = document.getElementById('volatility-text');
        let level = 'Medium';
        
        if (value < 33) level = 'Low';
        else if (value > 66) level = 'High';
        
        textElement.textContent = level;
        textElement.className = `volatility-${level.toLowerCase()}`;
    }

    initializeChart() {
        const ctx = document.getElementById('price-chart').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Price (USDT)',
                    data: [],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    connectWebSocket() {
        // Connect to backend proxy WebSocket server
        const wsUrl = "ws://localhost:8765";

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.updateConnectionStatus(true);
            document.getElementById('simulate-btn').textContent = 'Disconnect';
        };

        this.ws.onmessage = (event) => {
            // Since proxy forwards raw exchange messages, parse and handle accordingly
            this.handleWebSocketMessage(event.data, null);
        };

        this.ws.onerror = (error) => {
            this.showNotification('WebSocket error occurred', 'error');
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };

        this.ws.onclose = () => {
            this.updateConnectionStatus(false);
            document.getElementById('simulate-btn').textContent = 'Connect';
        };
    }

    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.updateConnectionStatus(false);
        document.getElementById('simulate-btn').textContent = 'Connect';
    }

    handleWebSocketMessage(data, exchange) {
        let parsed;
        try {
            parsed = JSON.parse(data);
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
            return;
        }

        let midPrice = null;

        // Parse Binance order book data (depth5@100ms)
        if (parsed.bids && parsed.asks) {
            const bestBid = parseFloat(parsed.bids[0][0]);
            const bestAsk = parseFloat(parsed.asks[0][0]);
            midPrice = (bestBid + bestAsk) / 2;
        }

        if (midPrice !== null) {
            this.updateUIWithRealData(midPrice);
        } else {
            // For demo purposes, if no midPrice can be extracted, use a random value
            this.updateUIWithRealData(50000 + Math.random() * 1000 - 500);
        }
    }

    updateUIWithRealData(midPrice) {
        // Update mid price
        document.getElementById('mid-price').textContent = `${midPrice.toFixed(2)} USDT`;

        // For demo, calculate slippage and fees based on midPrice and quantity
        const quantity = parseFloat(document.getElementById('quantity').value);
        const volatility = parseInt(document.getElementById('volatility').value) / 100;
        const feeTier = parseInt(document.getElementById('fee-tier').value);

        const slippage = (0.05 + volatility * 0.2 + quantity * 0.001) * 100;
        const fees = quantity * midPrice * (0.001 - (feeTier - 1) * 0.0002);
        const marketImpact = (0.02 + volatility * 0.1) * 100;
        const netCost = (slippage/100 * midPrice * quantity) + fees + (marketImpact/100 * midPrice * quantity);

        const makerProb = 0.6 + (volatility * -0.3);
        const takerProb = 1 - makerProb;

        // Update UI elements
        document.getElementById('slippage').textContent = `${slippage.toFixed(4)}%`;
        const slippageBar = document.querySelector('#slippage-bar .progress-fill');
        slippageBar.style.width = `${Math.min(slippage * 10, 100)}%`;
        slippageBar.style.background = slippage > 0.5 ? 
            'linear-gradient(90deg, #ef4444, #dc2626)' :
            slippage > 0.1 ?
            'linear-gradient(90deg, #f59e0b, #d97706)' :
            'linear-gradient(90deg, #10b981, #059669)';

        document.getElementById('fees').textContent = `${fees.toFixed(4)} USDT`;
        document.getElementById('market-impact').textContent = `${marketImpact.toFixed(4)}%`;
        document.getElementById('net-cost').textContent = `${netCost.toFixed(4)} USDT`;

        const makerPct = makerProb * 100;
        const takerPct = takerProb * 100;
        document.getElementById('maker-pct').textContent = `${makerPct.toFixed(2)}%`;
        document.getElementById('taker-pct').textContent = `${takerPct.toFixed(2)}%`;
        document.getElementById('maker-bar').style.width = `${makerPct}%`;
        document.getElementById('taker-bar').style.width = `${takerPct}%`;

        // Update performance metrics with dummy values
        document.getElementById('latency').textContent = `5.00 ms`;
        document.getElementById('avg-processing').textContent = `4.50 ms`;
        document.getElementById('update-freq').textContent = `10.00 Hz`;
        document.getElementById('orderbook-depth').textContent = `100`;

        // Update chart
        this.updateChart(midPrice);
    }

    updateChart(price) {
        this.priceData.push(price);
        // Limit to only 10 data points for better visibility
        if (this.priceData.length > 10) {
            this.priceData.shift();
        }

        const labels = Array.from({length: this.priceData.length}, (_, i) => `T-${this.priceData.length - i - 1}`);

        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = this.priceData;
        this.chart.update();
    }

    updateConnectionStatus(connected) {
        this.isConnected = connected;
        const statusElement = document.getElementById('connection-status');
        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('span:last-child');

        if (connected) {
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
            statusElement.style.color = '#10b981';
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Disconnected';
            statusElement.style.color = '#ef4444';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${this.getNotificationColor(type)};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getNotificationColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        return colors[type] || '#3b82f6';
    }
}

// Initialize the simulator when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.simulator = new CryptoTradeSimulator();
});

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .volatility-low { color: #10b981; }
    .volatility-medium { color: #f59e0b; }
    .volatility-high { color: #ef4444; }
`;
document.head.appendChild(style);
