import sys
import queue
from PyQt5.QtWidgets import QApplication
from websocket_client import WebSocketClient
from models import TradeSimulator
from ui import TradeSimulatorUI

def main():
    # Initialize WebSocket client
    ws_url = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
    ws_client = WebSocketClient(ws_url)
    
    # Initialize trade simulator
    simulator = TradeSimulator()
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Connect WebSocket message signal to update orderbook
    def handle_ws_message(message):
        simulator.update_orderbook(message)
    ws_client.message_received.connect(handle_ws_message)
    
    ws_client.connect()
    
    def get_simulation_data(quantity, side, volatility_sens):
        # Currently volatility_sens is unused, but accepted for compatibility
        return simulator.calculate_all_metrics(quantity, side)
        
    # Create and show UI
    ui = TradeSimulatorUI(get_simulation_data)
    ui.show()
    
    # Start application loop
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
