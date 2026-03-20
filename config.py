import os
from dotenv import load_dotenv
from web3 import Web3

# Tentar carregar .env se existir, mas não falhar se não existir
try:
    load_dotenv()
except:
    pass

# Base Network Configuration
BASE_RPC_URL = os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')
BASE_RPC_BACKUP = os.getenv('BASE_RPC_BACKUP', 'https://base-mainnet.public.blastapi.io')
BASE_RPC_3 = os.getenv('BASE_RPC_3', 'https://base-rpc.publicnode.com')
BASE_RPC_4 = os.getenv('BASE_RPC_4', 'https://1rpc.io/base')
CHAIN_ID = int(os.getenv('CHAIN_ID', '8453'))

# Wallet Configuration
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')

# Trading Configuration - OTIMIZADO PARA BASE NETWORK - MODO SEGURO
INITIAL_WETH_BALANCE = float(os.getenv('INITIAL_WETH_BALANCE', '0.001990'))  # Saldo inicial real
TRADE_AMOUNT_WETH = float(os.getenv('TRADE_AMOUNT_WETH', '0.000200'))  # 10% do saldo (mais conservador)
MAX_GAS_PRICE = int(os.getenv('MAX_GAS_PRICE', '2'))  # 2 gwei mínimo na Base
SLIPPAGE_TOLERANCE = float(os.getenv('SLIPPAGE_TOLERANCE', '25'))  # 25% slippage 
MAX_PRIORITY_FEE = int(os.getenv('MAX_PRIORITY_FEE', '2'))  # Priority fee 

# Sistema de Crescimento Inteligente - AUTO-PROGRAMÁVEL
SMART_SCALING_ENABLED = os.getenv('SMART_SCALING_ENABLED', 'true').lower() == 'true'
PROFIT_REINVESTMENT_RATE = float(os.getenv('PROFIT_REINVESTMENT_RATE', '0.5'))  # 50% dos lucros reinvestidos (mais conservador)
MAX_TRADE_PERCENTAGE = float(os.getenv('MAX_TRADE_PERCENTAGE', '20'))  # Máximo 20% do saldo por trade
MIN_TRADE_AMOUNT = float(os.getenv('MIN_TRADE_AMOUNT', '0.000050'))  # Mínimo para garantir execução

# Auto-scaling - Crescimento automático baseado em PERFORMANCE
AUTO_SCALE_ENABLED = os.getenv('AUTO_SCALE_ENABLED', 'true').lower() == 'true'
SCALE_UP_THRESHOLD = float(os.getenv('SCALE_UP_THRESHOLD', '0.003000'))  # Quando saldo chegar a 0.003, aumentar trades
SCALE_DOWN_THRESHOLD = float(os.getenv('SCALE_DOWN_THRESHOLD', '0.001200'))  # Se saldo cair para 0.0012, diminuir trades
WIN_RATE_SCALE_UP = float(os.getenv('WIN_RATE_SCALE_UP', '0.70'))  # 70% win rate para aumentar
WIN_RATE_SCALE_DOWN = float(os.getenv('WIN_RATE_SCALE_DOWN', '0.40'))  # 40% win rate para diminuir

# Configurações de Trading Inteligente - MODO SEGURO COM AUTO-AJUSTE
MEMECOIN_MODE = os.getenv('MEMECOIN_MODE', 'true').lower() == 'true'  # Habilitado para memecoins
ALL_TOKENS_MODE = os.getenv('ALL_TOKENS_MODE', 'false').lower() == 'true'  # Detectar TODOS os tokens - DESABILITADO para evitar scams
MIN_TOKEN_AGE_MINUTES = int(os.getenv('MIN_TOKEN_AGE_MINUTES', '5'))  # Tokens com pelo menos 5 min de vida
MAX_TOKEN_AGE_HOURS = int(os.getenv('MAX_TOKEN_AGE_HOURS', '24'))  # Máximo 24h para evitar rugs
TARGET_PROFIT_PERCENTAGE = float(os.getenv('TARGET_PROFIT_PERCENTAGE', '8'))  # Lucro de 8% (mais realista)
AGGRESSIVE_TRADING = os.getenv('AGGRESSIVE_TRADING', 'false').lower() == 'true'  # Desabilitado - modo seguro
QUICK_PROFIT_MODE = os.getenv('QUICK_PROFIT_MODE', 'true').lower() == 'true'  # Lucros rápidos
QUICK_EXIT_PERCENTAGE = float(os.getenv('QUICK_EXIT_PERCENTAGE', '5'))  # Saída rápida com 5%
STOP_LOSS_PERCENTAGE = float(os.getenv('STOP_LOSS_PERCENTAGE', '15'))  # Stop loss 15% (mais apertado para preservar capital)

# DEX Configuration
ENABLE_UNISWAP_V3 = os.getenv('ENABLE_UNISWAP_V3', 'true').lower() == 'true'
ENABLE_AERODROME = os.getenv('ENABLE_AERODROME', 'true').lower() == 'true'
ENABLE_BASESWAP = os.getenv('ENABLE_BASESWAP', 'true').lower() == 'true'
ENABLE_SUSHISWAP = os.getenv('ENABLE_SUSHISWAP', 'true').lower() == 'true'

# Security Settings - OTIMIZADO PARA EVITAR SCAMS E HONEYPOTS
ENABLE_MEV_PROTECTION = os.getenv('ENABLE_MEV_PROTECTION', 'true').lower() == 'true'  # Habilitado para proteção
MIN_LIQUIDITY_USD = float(os.getenv('MIN_LIQUIDITY_USD', '1000'))  # Mínimo $1000 de liquidez (mais seguro)
MAX_TRADE_IMPACT = float(os.getenv('MAX_TRADE_IMPACT', '20'))  # Máximo 20% impacto no preço
MIN_SCORE_TO_BUY = int(os.getenv('MIN_SCORE_TO_BUY', '60'))  # Score mínimo 60/100 (mais seletivo)
ENABLE_HONEYPOT_CHECK = os.getenv('ENABLE_HONEYPOT_CHECK', 'true').lower() == 'true'  # HABILITADO - verificar se token permite venda
RISK_TOLERANCE = os.getenv('RISK_TOLERANCE', 'medium').lower()  # medium, não high

# Trading Mode - MODO SEGURO HABILITADO
SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'  # DESABILITADO - TRADING REAL
REAL_TRADING_ENABLED = os.getenv('REAL_TRADING_ENABLED', 'true').lower() == 'true'  # HABILITADO
FAST_MODE = os.getenv('FAST_MODE', 'true').lower() == 'true'  # Modo rápido para oportunidades
MEV_PROTECTION = os.getenv('MEV_PROTECTION', 'true').lower() == 'true'  # Habilitado para proteção

# Performance Settings - OTIMIZADO PARA TRANSAÇÕES CONFIRMADAS
TRANSACTION_TIMEOUT = int(os.getenv('TRANSACTION_TIMEOUT', '60'))  # Timeout maior para confirmar
CONFIRMATION_BLOCKS = int(os.getenv('CONFIRMATION_BLOCKS', '2'))  # Esperar 2 confirmações
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '5'))  # Mais tentativas
SCAN_INTERVAL = float(os.getenv('SCAN_INTERVAL', '1.0'))  # Scan mais seguro (1s)
PRIORITY_FEE = int(os.getenv('PRIORITY_FEE', '1'))  # Priority fee 1 gwei

# Telegram - Não esperar resposta
TELEGRAM_WAIT_RESPONSE = os.getenv('TELEGRAM_WAIT_RESPONSE', 'false').lower() == 'true'

# Security Thresholds - OTIMIZADO PARA TOKENES SEGUROS
MIN_LIQUIDITY_ETH = float(os.getenv('MIN_LIQUIDITY_ETH', '0.5'))  # Mínimo 0.5 ETH de liquidez
MIN_HOLDERS = int(os.getenv('MIN_HOLDERS', '50'))  # Mínimo 50 holders (mais distribuído)
MIN_TOKEN_AGE = int(os.getenv('MIN_TOKEN_AGE', '300'))  # Mínimo 5 minutos (em segundos)
PRIMARY_DEX = os.getenv('PRIMARY_DEX', 'Uniswap V3')  # DEX preferida

# Monitoring
ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_AUTHORIZED_USERS = os.getenv('TELEGRAM_AUTHORIZED_USERS', '123456789')  # IDs dos usuários autorizados

# Base Network Token Addresses
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
USDT_ADDRESS = "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2"

# DEX Router Addresses on Base
UNISWAP_V3_ROUTER = "0x2626664c2603336E57B271c5C0b26F421741e481"
AERODROME_ROUTER = "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"
BASESWAP_ROUTER = "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86"
SUSHISWAP_ROUTER = "0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891"

# DEX Factory Addresses
UNISWAP_V3_FACTORY = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"
BASESWAP_FACTORY = "0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB"

# Gas Configuration - OTIMIZADO PARA TRANSAÇÕES CONFIRMADAS
DEFAULT_GAS_LIMIT = 200000  # Padrão para Base
PRIORITY_GAS_LIMIT = 250000  # Para transações prioritárias
APPROVAL_GAS_LIMIT = 60000   # Para aprovações
SWAP_GAS_LIMIT = 200000     # Para swaps

# ========== IA AUTO-PROGRAMÁVEL - NOVAS CONFIGURAÇÕES ==========
# Sistema que ajusta automaticamente baseado em performance
AI_AUTO_ADJUST = os.getenv('AI_AUTO_ADJUST', 'true').lower() == 'true'
AI_LEARNING_RATE = float(os.getenv('AI_LEARNING_RATE', '0.1'))  # Taxa de aprendizado
AI_MIN_CONFIDENCE = float(os.getenv('AI_MIN_CONFIDENCE', '0.6'))  # Mínimo 60% de confiança
AI_ADJUST_INTERVAL = int(os.getenv('AI_ADJUST_INTERVAL', '10'))  # Ajustar a cada 10 trades
AI_MAX_TRADE_AMOUNT = float(os.getenv('AI_MAX_TRADE_AMOUNT', '0.000500'))  # Máximo 0.0005 WETH por trade
AI_MIN_TRADE_AMOUNT = float(os.getenv('AI_MIN_TRADE_AMOUNT', '0.000100'))  # Mínimo 0.0001 WETH por trade

# Auto-otimização de parâmetros
AI_OPTIMIZE_GAS = os.getenv('AI_OPTIMIZE_GAS', 'true').lower() == 'true'  # Auto ajustar gas
AI_OPTIMIZE_SLIPPAGE = os.getenv('AI_OPTIMIZE_SLIPPAGE', 'true').lower() == 'true'  # Auto ajustar slippage
AI_OPTIMIZE_SCORE = os.getenv('AI_OPTIMIZE_SCORE', 'true').lower() == 'true'  # Auto ajustar score mínimo
AI_OPTIMIZE_STOPLOSS = os.getenv('AI_OPTIMIZE_STOPLOSS', 'true').lower() == 'true'  # Auto ajustar stop loss

def validate_config():
    """Validate essential configuration"""
    if not PRIVATE_KEY:
        raise ValueError("PRIVATE_KEY não configurada")
    if not WALLET_ADDRESS:
        raise ValueError("WALLET_ADDRESS não configurado")
    if len(PRIVATE_KEY) != 64:
        raise ValueError("PRIVATE_KEY deve ter 64 caracteres")
    if not Web3.is_address(WALLET_ADDRESS):
        raise ValueError("WALLET_ADDRESS inválido")
    
    print("✅ Configuração validada com sucesso!")
    return True