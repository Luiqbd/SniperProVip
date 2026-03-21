"""
Sistema de Logging para Sniper Bot
Registra erros de transações, falhas e eventos importantes
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Configurações de logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Nome do arquivo de log com data
LOG_FILE = LOG_DIR / f"sniper_{datetime.now().strftime('%Y%m%d')}.log"
ERROR_FILE = LOG_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
TRADE_FILE = LOG_DIR / f"trades_{datetime.now().strftime('%Y%m%d')}.log"

# Configuração do logger principal
def setup_logger(name: str = "sniper") -> logging.Logger:
    """Configura e retorna um logger"""
    logger = logging.getLogger(name)
    
    # Se já foi configurado, retorna
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo principal
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler para erros (apenas ERROR e CRITICAL)
    error_handler = logging.FileHandler(ERROR_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Adiciona handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger


# Logger principal
logger = setup_logger("sniper")

# ============================================
# Dashboard Integration - Integração com Dashboard
# ============================================
try:
    from dashboard.api import data_store, log_info as dashboard_log, log_error as dashboard_error, log_warning as dashboard_warning
    DASHBOARD_ENABLED = True
except ImportError:
    DASHBOARD_ENABLED = False
    dashboard_log = None
    dashboard_error = None
    dashboard_warning = None

def send_to_dashboard(level: str, message: str):
    """Envia log para o dashboard"""
    if not DASHBOARD_ENABLED:
        return
    try:
        if level == 'ERROR' and dashboard_error:
            dashboard_error(message)
        elif level == 'WARNING' and dashboard_warning:
            dashboard_warning(message)
        elif dashboard_log:
            dashboard_log(message)
    except:
        pass  # Silencioso se falhar


def log_trade(action: str, token_symbol: str, amount: float, tx_hash: str = None, status: str = "PENDING"):
    """Registra operação de trade"""
    log_entry = f"TRADE | {action} | {token_symbol} | {amount:.6f} ETH | Status: {status}"
    if tx_hash:
        log_entry += f" | TX: {tx_hash}"
    
    logger.info(log_entry)
    send_to_dashboard('INFO', log_entry)
    
    # Também salva no arquivo de trades
    with open(TRADE_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {log_entry}\n")


def log_error(error_type: str, message: str, exception: Exception = None, tx_hash: str = None):
    """Registra erro com detalhes"""
    log_entry = f"ERROR | {error_type} | {message}"
    if tx_hash:
        log_entry += f" | TX: {tx_hash}"
    if exception:
        log_entry += f" | Exception: {str(exception)}"
    
    logger.error(log_entry)
    send_to_dashboard('ERROR', log_entry)
    
    # Log adicional para tracking
    if exception:
        logger.debug(f"Stack trace: {exception.__class__.__name__}")


def log_buy_attempt(token_symbol: str, amount: float, reason: str = ""):
    """Registra tentativa de compra"""
    msg = f"BUY ATTEMPT | {token_symbol} | {amount:.6f} ETH | {reason}"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_buy_success(token_symbol: str, amount: float, tx_hash: str, dex: str):
    """Registra compra bem-sucedida"""
    log_trade("BUY", token_symbol, amount, tx_hash, "SUCCESS")
    msg = f"✅ BUY SUCCESS | {token_symbol} | {amount:.6f} ETH | DEX: {dex}"
    logger.info(msg)
    send_to_dashboard('SUCCESS', msg)


def log_buy_failure(token_symbol: str, amount: float, reason: str):
    """Registra falha na compra"""
    log_trade("BUY", token_symbol, amount, None, f"FAILED: {reason}")
    msg = f"❌ BUY FAILED | {token_symbol} | {amount:.6f} ETH | Reason: {reason}"
    logger.error(msg)
    send_to_dashboard('ERROR', msg)


def log_sell_attempt(token_symbol: str, amount: float):
    """Registra tentativa de venda"""
    msg = f"SELL ATTEMPT | {token_symbol} | {amount:.6f} tokens"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_sell_success(token_symbol: str, amount: float, tx_hash: str, profit: float = None):
    """Registra venda bem-sucedida"""
    log_trade("SELL", token_symbol, amount, tx_hash, "SUCCESS")
    profit_str = f" | Profit: {profit:.6f} ETH" if profit else ""
    msg = f"✅ SELL SUCCESS | {token_symbol} | {amount:.6f} tokens{profit_str}"
    logger.info(msg)
    send_to_dashboard('SUCCESS', msg)


def log_sell_failure(token_symbol: str, amount: float, reason: str):
    """Registra falha na venda"""
    log_trade("SELL", token_symbol, amount, None, f"FAILED: {reason}")
    msg = f"❌ SELL FAILED | {token_symbol} | {amount:.6f} tokens | Reason: {reason}"
    logger.error(msg)
    send_to_dashboard('ERROR', msg)


def log_tx_reverted(tx_hash: str, reason: str = ""):
    """Registra transação revertida"""
    msg = f"🔴 TX REVERTED | {tx_hash} | {reason}"
    logger.error(msg)
    send_to_dashboard('ERROR', msg)
    log_error("TX_REVERTED", reason, tx_hash=tx_hash)


def log_insufficient_balance(token_symbol: str, required: float, available: float, balance_type: str = "ETH"):
    """Registra saldo insuficiente"""
    msg = f"⚠️ INSUFFICIENT BALANCE | {balance_type} | Required: {required:.6f} | Available: {available:.6f}"
    logger.warning(msg)
    send_to_dashboard('WARNING', msg)
    log_error("INSUFFICIENT_BALANCE", f"Need {required:.6f} {balance_type}, have {available:.6f}")


def log_gas_too_low(tx_hash: str = None):
    """Registra problema de gas muito baixo"""
    msg = "⚠️ GAS_TOO_LOW"
    if tx_hash:
        msg += f" | TX: {tx_hash}"
    logger.warning(msg)
    send_to_dashboard('WARNING', msg)
    log_error("GAS_TOO_LOW", "Gas price too low for confirmation")


def log_rate_limit(retry_after: int = 0):
    """Registra rate limit atingido"""
    retry_msg = f" | Retry after: {retry_after}s" if retry_after else ""
    msg = f"🚫 RATE LIMIT{retry_msg}"
    logger.warning(msg)
    send_to_dashboard('WARNING', msg)
    log_error("RATE_LIMIT", f"RPC rate limit hit, retry after {retry_after}s")


def log_rpc_error(rpc_url: str, error: str):
    """Registra erro de conexão RPC"""
    msg = f"🌐 RPC ERROR | {rpc_url[:30]}... | {error}"
    logger.error(msg)
    send_to_dashboard('ERROR', msg)
    log_error("RPC_ERROR", error)


def log_token_detected(token_symbol: str, token_address: str, liquidity: float = None):
    """Registra token detectado"""
    liq_str = f" | Liquidity: {liquidity:.4f} ETH" if liquidity else ""
    msg = f"🔍 TOKEN DETECTED | {token_symbol} | {token_address[:10]}...{liq_str}"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_analysis(token_symbol: str, score: int, prediction: str, reason: str):
    """Registra análise de token"""
    msg = f"🧠 AI ANALYSIS | {token_symbol} | Score: {score}/100 | Prediction: {prediction} | {reason}"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_buy_decision(token_symbol: str, decision: str, reason: str):
    """Registra decisão de compra"""
    msg = f"🎯 BUY DECISION | {token_symbol} | {decision} | {reason}"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_sell_decision(token_symbol: str, decision: str, reason: str):
    """Registra decisão de venda"""
    msg = f"💰 SELL DECISION | {token_symbol} | {decision} | {reason}"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_bot_start():
    """Registra início do bot"""
    logger.info("=" * 50)
    logger.info("🚀 SNIPER BOT STARTED")
    logger.info("=" * 50)
    send_to_dashboard('INFO', "🚀 SNIPER BOT INICIADO!")


def log_bot_stop():
    """Registra parada do bot"""
    msg = "🛑 SNIPER BOT STOPPED"
    logger.info(msg)
    logger.info("=" * 50)
    send_to_dashboard('WARNING', msg)


def log_config_loaded():
    """Registra configurações carregadas"""
    msg = "📋 Configuration loaded"
    logger.info(msg)
    send_to_dashboard('INFO', msg)


def log_balance_check(balance_eth: float, balance_token: str = None):
    """Registra verificação de saldo"""
    msg = f"💰 BALANCE CHECK | ETH: {balance_eth:.6f}"
    if balance_token:
        msg += f" | Token: {balance_token}"
    logger.debug(msg)
    send_to_dashboard('DEBUG', msg)


def get_recent_errors(lines: int = 50) -> str:
    """Retorna erros recentes do log"""
    try:
        with open(ERROR_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except FileNotFoundError:
        return "Nenhum erro encontrado"


def get_recent_trades(lines: int = 50) -> str:
    """Retorna trades recentes do log"""
    try:
        with open(TRADE_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except FileNotFoundError:
        return "Nenhum trade encontrado"


def get_error_count() -> dict:
    """Conta erros por tipo"""
    error_counts = {}
    try:
        with open(ERROR_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if 'ERROR |' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        error_type = parts[1].strip()
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
    except FileNotFoundError:
        pass
    return error_counts
