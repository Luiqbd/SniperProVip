"""
API Server for Dashboard - Sniper Bot Pro
Servidor API para conectar o dashboard ao bot
"""

from flask import Flask, jsonify, request
import threading
import os
from datetime import datetime
from collections import deque

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ============================================
# Data Store - Armazenamento de Dados
# ============================================
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
            'positions': [],
            'logs': deque(maxlen=1000)
        }
        self.lock = threading.Lock()
    
    def add_log(self, level: str, message: str):
        """Adicionar entrada de log"""
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': level.upper(),
            'message': message
        }
        with self.lock:
            self.data['logs'].append(log_entry)
        return log_entry
    
    def update(self, key, value):
        with self.lock:
            self.data[key] = value
    
    def append_trade(self, trade):
        with self.lock:
            self.data['trades'].insert(0, trade)
            self.data['trades'] = self.data['trades'][:100]
            self.data['total_trades'] = len(self.data['trades'])
    
    def get_all(self):
        with self.lock:
            return dict(self.data)
    
    def get_logs(self):
        with self.lock:
            return list(self.data['logs'])
    
    def load_logs_from_file(self, log_file_path: str, lines: int = 100):
        """Carrega logs diretamente do arquivo de log do bot"""
        try:
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    
                    with self.lock:
                        for line in recent:
                            line = line.strip()
                            if not line:
                                continue
                            # Parse log line
                            parts = line.split(' | ')
                            if len(parts) >= 3:
                                time = parts[0][-8:] if len(parts[0]) > 8 else parts[0]
                                level = parts[1] if len(parts) > 1 else 'INFO'
                                message = ' | '.join(parts[2:]) if len(parts) > 2 else line
                                
                                log_entry = {
                                    'time': time,
                                    'level': level.upper(),
                                    'message': message
                                }
                                # Avoid duplicates
                                if log_entry not in self.data['logs']:
                                    self.data['logs'].append(log_entry)
        except Exception as e:
            print(f"Erro ao carregar logs: {e}")

# Global data store
data_store = DataStore()

# Carregar logs do arquivo ao iniciar
LOG_FILE = f"logs/sniper_{datetime.now().strftime('%Y%m%d')}.log"
data_store.load_logs_from_file(LOG_FILE, 50)

# ============================================
# API Routes - Rotas da API
# ============================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Obter status completo do bot"""
    return jsonify(data_store.get_all())

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Obter trades recentes"""
    data = data_store.get_all()
    return jsonify(data['trades'])

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Obter posições ativas"""
    data = data_store.get_all()
    return jsonify(data['positions'])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obter estatísticas"""
    data = data_store.get_all()
    return jsonify({
        'total_trades': data['total_trades'],
        'win_rate': data['win_rate'],
        'total_profit': data['total_profit'],
        'daily_pnl': data['daily_pnl']
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Obter logs em tempo real"""
    return jsonify(data_store.get_logs())

@app.route('/api/logs', methods=['POST'])
def post_log():
    """Adicionar log (usado pelo bot)"""
    data = request.json
    level = data.get('level', 'INFO')
    message = data.get('message', '')
    log = data_store.add_log(level, message)
    return jsonify(log)

# ============================================
# Bot Integration Functions
# Funções de Integração com o Bot
# ============================================

def update_bot_status(status: str):
    """Atualizar status do bot"""
    data_store.update('bot_status', status)
    data_store.add_log('INFO', f'Status do bot: {status}')

def update_balance(balance: float):
    """Atualizar saldo ETH"""
    data_store.update('eth_balance', balance)

def record_trade(token: str, trade_type: str, amount: float, price: float, status: str, tx: str = ""):
    """Registrar trade"""
    trade = {
        'token': token,
        'type': trade_type,
        'amount': amount,
        'price': price,
        'status': status,
        'tx': tx,
        'time': datetime.now().strftime('%H:%M:%S'),
        'timestamp': datetime.now().isoformat()
    }
    data_store.append_trade(trade)
    data_store.add_log(
        'SUCCESS' if status == 'SUCCESS' else 'ERROR',
        f'{trade_type} {token} - {amount} ETH - {status}'
    )

def update_positions(positions: list):
    """Atualizar posições ativas"""
    data_store.update('active_positions', len(positions))
    data_store.update('positions', positions)

def update_risk(level: str, consecutive_losses: int, circuit_breaker: bool):
    """Atualizar métricas de risco"""
    data_store.update('risk_level', level)
    data_store.update('consecutive_losses', consecutive_losses)
    data_store.update('circuit_breaker', circuit_breaker)

def log_info(message: str):
    """Registrar log INFO"""
    data_store.add_log('INFO', message)

def log_error(message: str):
    """Registrar log ERROR"""
    data_store.add_log('ERROR', message)

def log_warning(message: str):
    """Registrar log WARNING"""
    data_store.add_log('WARNING', message)

# ============================================
# Server - Servidor
# ============================================

def run_server(port=5000):
    """Rodar o servidor API"""
    print(f"🚀 Servidor API iniciado na porta {port}")
    print(f"📊 Dashboard: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def start_api_server(port=5000):
    """Iniciar servidor API em background"""
    thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    thread.start()
    return thread

# ============================================
# Main - Executar
# ============================================

if __name__ == '__main__':
    print("=" * 50)
    print("🎯 Sniper Bot Pro - API Server")
    print("=" * 50)
    print("🚀 Iniciando servidor...")
    
    # Demo: simulate initial state
    data_store.update('bot_status', 'RUNNING')
    data_store.update('eth_balance', 0.004512)
    data_store.add_log('INFO', '🎯 Sniper Bot Dashboard iniciado!')
    data_store.add_log('INFO', '🌐 Conectado à Base Network')
    data_store.add_log('INFO', '💼 Carteira configurada')
    data_store.add_log('INFO', '🤖 Módulos avançados carregados')
    data_store.add_log('INFO', '🛡️ Risk Manager ativo')
    data_store.add_log('INFO', '🔍 Monitoramento iniciado')
    
    start_api_server()
    
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Servidor parado")
