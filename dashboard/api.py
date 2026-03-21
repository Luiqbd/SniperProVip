"""
API Server for Dashboard
Provides endpoints for the web dashboard to connect
"""

from flask import Flask, jsonify, request
import threading
import json
from datetime import datetime

app = Flask(__name__)

# In-memory data store (in production, use Redis or database)
class DataStore:
    def __init__(self):
        self.data = {
            'bot_status': 'STOPPED',
            'eth_balance': 0.0,
            'total_trades': 0,
            'win_rate': 0,
            'total_profit': 0.0,
            'daily_pnl': 0.0,
            'active_positions': 0,
            'risk_level': 'LOW',
            'consecutive_losses': 0,
            'circuit_breaker': False,
            'trades': [],
            'positions': []
        }
        self.lock = threading.Lock()
    
    def update(self, key, value):
        with self.lock:
            self.data[key] = value
    
    def append_trade(self, trade):
        with self.lock:
            self.data['trades'].insert(0, trade)
            # Keep only last 100 trades
            self.data['trades'] = self.data['trades'][:100]
            self.data['total_trades'] = len(self.data['trades'])
    
    def get_all(self):
        with self.lock:
            return self.data.copy()

# Global data store
data_store = DataStore()

# ============ API Routes ============

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get bot status"""
    return jsonify(data_store.get_all())

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get recent trades"""
    data = data_store.get_all()
    return jsonify(data['trades'])

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get active positions"""
    data = data_store.get_all()
    return jsonify(data['positions'])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    data = data_store.get_all()
    return jsonify({
        'total_trades': data['total_trades'],
        'win_rate': data['win_rate'],
        'total_profit': data['total_profit'],
        'daily_pnl': data['daily_pnl']
    })

# ============ Bot Integration ============

def update_bot_status(status: str):
    """Update bot status from bot code"""
    data_store.update('bot_status', status)

def update_balance(balance: float):
    """Update ETH balance"""
    data_store.update('eth_balance', balance)

def record_trade(token: str, trade_type: str, amount: float, price: float, status: str, tx: str = ""):
    """Record a trade"""
    trade = {
        'token': token,
        'type': trade_type,
        'amount': amount,
        'price': price,
        'status': status,
        'tx': tx,
        'timestamp': datetime.now().isoformat()
    }
    data_store.append_trade(trade)

def update_positions(positions: list):
    """Update active positions"""
    data_store.update('active_positions', len(positions))
    data_store.update('positions', positions)

def update_risk(level: str, consecutive_losses: int, circuit_breaker: bool):
    """Update risk metrics"""
    data_store.update('risk_level', level)
    data_store.update('consecutive_losses', consecutive_losses)
    data_store.update('circuit_breaker', circuit_breaker)

# ============ Server ============

def run_server(port=5000):
    """Run the API server"""
    app.run(host='0.0.0.0', port=port, debug=False)

def start_api_server(port=5000):
    """Start API server in background thread"""
    thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    thread.start()
    return thread

# Example usage:
if __name__ == '__main__':
    print("🚀 Starting API Server on port 5000...")
    start_api_server()
    
    # Demo: simulate some data
    data_store.update('bot_status', 'RUNNING')
    data_store.update('eth_balance', 0.004512)
    
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
