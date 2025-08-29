import json
import websocket
import threading
import time
from queue import Queue
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton, QDoubleSpinBox,
                            QFormLayout, QGroupBox, QSlider, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
import sys
from utils import logger

class WebSocketClient(QObject):
    """
    WebSocket client that runs in a separate thread and emits signals when messages are received
    """
    message_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.ws = None
        self.connected = False
        self.keep_running = True
        self.message_drop_count = 0
        self.max_queue_size = 1000
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def on_open(self, ws):
        logger.info("WebSocket connection opened")
        self.connected = True
        self.reconnect_attempts = 0
        self.connection_changed.emit(True)
        
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.message_received.emit(data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message: {e}")
            
    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        self.connection_changed.emit(False)
        
    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket connection closed: {close_msg} (code: {close_status_code})")
        self.connected = False
        self.connection_changed.emit(False)
        
        if self.keep_running and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
            time.sleep(5)
            self.connect()
            
    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        self.wst = threading.Thread(target=self.ws.run_forever)
        self.wst.daemon = True
        self.wst.start()
        
    def disconnect(self):
        self.keep_running = False
        if self.ws:
            self.ws.close()
            
    def is_connected(self):
        return self.connected

class TradeSimulatorUI(QMainWindow):
    def __init__(self, simulator_callback):
        super().__init__()
        self.simulator_callback = simulator_callback
        self.init_ui()
        self.setup_timer()
        self.setup_websocket()
        
    def init_ui(self):
        self.setWindowTitle('Cryptocurrency Trade Simulator')
        self.setGeometry(100, 100, 1000, 700)
        
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Left panel - Input parameters
        input_group = QGroupBox("Input Parameters")
        input_layout = QFormLayout()
        
        # Exchange selection
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(['OKX', 'Binance', 'Coinbase'])
        self.exchange_combo.currentTextChanged.connect(self.on_exchange_changed)
        
        # Symbol selection
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP'])
        
        # Order parameters
        self.side_combo = QComboBox()
        self.side_combo.addItems(['Buy', 'Sell'])
        
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.001, 1000)
        self.quantity_input.setValue(0.1)
        self.quantity_input.setDecimals(8)
        
        # Volatility control
        self.volatility_slider = QSlider(Qt.Horizontal)
        self.volatility_slider.setRange(0, 100)
        self.volatility_slider.setValue(50)
        self.volatility_label = QLabel('Medium')
        
        # Fee tier
        self.fee_tier_combo = QComboBox()
        self.fee_tier_combo.addItems(['Tier 1 (VIP0)', 'Tier 2 (VIP1)', 'Tier 3 (VIP2)'])
        
        # Connection status
        self.connection_status = QLabel('Disconnected')
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        
        input_layout.addRow('Exchange:', self.exchange_combo)
        input_layout.addRow('Symbol:', self.symbol_combo)
        input_layout.addRow('Side:', self.side_combo)
        input_layout.addRow('Quantity:', self.quantity_input)
        input_layout.addRow('Volatility Sensitivity:', self.volatility_slider)
        input_layout.addRow('', self.volatility_label)
        input_layout.addRow('Fee Tier:', self.fee_tier_combo)
        input_layout.addRow('Connection:', self.connection_status)
        
        input_group.setLayout(input_layout)
        
        # Right panel - Output parameters
        output_group = QGroupBox("Simulation Results")
        output_layout = QFormLayout()
        
        # Price and cost metrics
        self.mid_price_label = QLabel('0.00')
        self.slippage_label = QLabel('0.00%')
        self.slippage_bar = QProgressBar()
        self.slippage_bar.setRange(0, 1000)  # 0-10% in 0.01% increments
        
        self.fees_label = QLabel('0.00 USDT')
        self.market_impact_label = QLabel('0.00%')
        self.net_cost_label = QLabel('0.00 USDT')
        
        # Maker/Taker visualization
        self.maker_progress = QProgressBar()
        self.taker_progress = QProgressBar()
        
        # Performance metrics
        self.latency_label = QLabel('0.00 ms')
        self.avg_processing_label = QLabel('0.00 ms')
        self.update_freq_label = QLabel('0.00 Hz')
        self.orderbook_depth_label = QLabel('0')
        
        # Add to layout with visual grouping
        output_layout.addRow(QLabel('<b>Price Metrics</b>'))
        output_layout.addRow('Mid Price:', self.mid_price_label)
        output_layout.addRow('Expected Slippage:', self.slippage_label)
        output_layout.addRow('', self.slippage_bar)
        
        output_layout.addRow(QLabel('<b>Cost Breakdown</b>'))
        output_layout.addRow('Expected Fees:', self.fees_label)
        output_layout.addRow('Expected Market Impact:', self.market_impact_label)
        output_layout.addRow('Net Cost:', self.net_cost_label)
        
        output_layout.addRow(QLabel('<b>Market State</b>'))
        output_layout.addRow('Maker Proportion:', self.maker_progress)
        output_layout.addRow('Taker Proportion:', self.taker_progress)
        
        output_layout.addRow(QLabel('<b>Performance</b>'))
        output_layout.addRow('Processing Latency:', self.latency_label)
        output_layout.addRow('Avg Processing Time:', self.avg_processing_label)
        output_layout.addRow('Update Frequency:', self.update_freq_label)
        output_layout.addRow('Orderbook Depth:', self.orderbook_depth_label)
        
        output_group.setLayout(output_layout)
        
        # Add panels to main layout
        main_layout.addWidget(input_group, 1)
        main_layout.addWidget(output_group, 2)
        main_widget.setLayout(main_layout)
        
        self.setCentralWidget(main_widget)
        
        # Connect signals
        self.volatility_slider.valueChanged.connect(self.update_volatility_label)
        
    def on_exchange_changed(self, exchange):
        """Handle exchange selection change"""
        # Here you would update the WebSocket URL based on the selected exchange
        logger.info(f"Exchange changed to {exchange}")
        if self.ws_client:
            self.ws_client.disconnect()
            self.setup_websocket()
        
    def update_volatility_label(self, value):
        """Update volatility sensitivity label"""
        if value < 33:
            self.volatility_label.setText('Low')
        elif value < 66:
            self.volatility_label.setText('Medium')
        else:
            self.volatility_label.setText('High')
    
    def setup_websocket(self):
        """Initialize WebSocket connection"""
        exchange = self.exchange_combo.currentText()
        symbol = self.symbol_combo.currentText()
        
        # This would be replaced with actual WebSocket URLs for each exchange
        ws_urls = {
            'OKX': f"wss://ws.okx.com:8443/ws/v5/public?symbol={symbol}",
            'Binance': f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth",
            'Coinbase': f"wss://ws-feed.pro.coinbase.com"
        }
        
        self.ws_client = WebSocketClient(ws_urls.get(exchange, ws_urls['OKX']))
        self.ws_client.message_received.connect(self.handle_ws_message)
        self.ws_client.connection_changed.connect(self.update_connection_status)
        self.ws_client.connect()
        
    def handle_ws_message(self, message):
        """Handle incoming WebSocket messages"""
        # Process the order book update
        self.simulator_callback(message)  # Pass the message to the simulator
        
    def update_connection_status(self, connected):
        """Update UI based on connection status"""
        if connected:
            self.connection_status.setText('Connected')
            self.connection_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_status.setText('Disconnected')
            self.connection_status.setStyleSheet("color: red; font-weight: bold;")
    
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_metrics)
        self.timer.start(500)  # Update every 500ms
        
    def update_metrics(self):
        """Update all displayed metrics"""
        quantity = self.quantity_input.value()
        side = 'buy' if self.side_combo.currentText() == 'Buy' else 'sell'
        volatility_sens = self.volatility_slider.value() / 100
        
        metrics = self.simulator_callback(quantity, side, volatility_sens)
        if not metrics:
            return
            
        # Update price metrics
        self.mid_price_label.setText(f"{metrics['mid_price']:,.2f} USDT")
        
        # Update slippage with visual feedback
        slippage = metrics['slippage']
        self.slippage_label.setText(f"{slippage:.4f}%")
        self.slippage_bar.setValue(int(slippage * 100))  # Convert % to 0.01% units
        
        # Color slippage bar based on severity
        palette = self.slippage_bar.palette()
        if slippage > 0.5:
            palette.setColor(QPalette.Highlight, QColor(255, 0, 0))
        elif slippage > 0.1:
            palette.setColor(QPalette.Highlight, QColor(255, 165, 0))
        else:
            palette.setColor(QPalette.Highlight, QColor(0, 255, 0))
        self.slippage_bar.setPalette(palette)
        
        # Update cost metrics
        self.fees_label.setText(f"{metrics['fees']:,.4f} USDT")
        self.market_impact_label.setText(f"{metrics['market_impact']:.4f}%")
        self.net_cost_label.setText(f"{metrics['net_cost']:,.4f} USDT")
        
        # Update maker/taker visualization
        maker_pct = metrics['maker_taker_proportion'][0] * 100
        taker_pct = metrics['maker_taker_proportion'][1] * 100
        self.maker_progress.setFormat(f"{maker_pct:.2f}%")
        self.maker_progress.setValue(int(maker_pct))
        self.taker_progress.setFormat(f"{taker_pct:.2f}%")
        self.taker_progress.setValue(int(taker_pct))
        
        # Update performance metrics
        self.latency_label.setText(f"{metrics['processing_time']:.2f} ms")
        self.avg_processing_label.setText(f"{metrics['avg_processing_time']:.2f} ms")
        update_freq = 1/metrics['update_frequency'] if metrics['update_frequency'] > 0 else 0
        self.update_freq_label.setText(f"{update_freq:.2f} Hz")
        self.orderbook_depth_label.setText(f"{metrics['orderbook_depth']}")
        
    def closeEvent(self, event):
        """Clean up resources when closing the window"""
        self.timer.stop()
        if hasattr(self, 'ws_client'):
            self.ws_client.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mock simulator callback for testing
    def simulator_callback(quantity, side, volatility_sens):
        return {
            'mid_price': 50000.0,
            'slippage': 0.12,
            'fees': 5.0,
            'market_impact': 0.05,
            'net_cost': 10.0,
            'maker_taker_proportion': (0.6, 0.4),
            'processing_time': 2.5,
            'avg_processing_time': 3.0,
            'update_frequency': 0.1,
            'orderbook_depth': 50
        }
    
    window = TradeSimulatorUI(simulator_callback)
    window.show()
    sys.exit(app.exec_())