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
CHAIN_ID = int(os.getenv('CHAIN_ID', '8453'))

# Wallet Configuration
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS')

# Trading Configuration - OTIMIZADO PARA BASE NETWORK - MODO CRESCIMENTO RÁPIDO
INITIAL_WETH_BALANCE = float(os.getenv('INITIAL_WETH_BALANCE', '0.001990'))  # Saldo inicial real
TRADE_AMOUNT_WETH = float(os.getenv('TRADE_AMOUNT_WETH', '0.000398'))  # 20% do saldo (agressivo para crescimento)
MAX_GAS_PRICE = int(os.getenv('MAX_GAS_PRICE', '50'))  # Aumentado para Base Network (mais competitivo)
SLIPPAGE_TOLERANCE = float(os.getenv('SLIPPAGE_TOLERANCE', '20'))  # Aumentado para memecoins muito voláteis
MAX_PRIORITY_FEE = int(os.getenv('MAX_PRIORITY_FEE', '5'))  # Aumentado para velocidade na Base Network

# Sistema de Crescimento Inteligente - CONFIGURAÇÃO AGRESSIVA
SMART_SCALING_ENABLED = os.getenv('SMART_SCALING_ENABLED', 'true').lower() == 'true'
PROFIT_REINVESTMENT_RATE = float(os.getenv('PROFIT_REINVESTMENT_RATE', '0.6'))  # 60% dos lucros reinvestidos (mais agressivo)
MAX_TRADE_PERCENTAGE = float(os.getenv('MAX_TRADE_PERCENTAGE', '30'))  # Máximo 30% do saldo por trade (agressivo)
MIN_TRADE_AMOUNT = float(os.getenv('MIN_TRADE_AMOUNT', '0.000050'))  # Mínimo para trades pequenos

# Modo de Emergência para Saldos Baixos
EMERGENCY_MODE_THRESHOLD = float(os.getenv('EMERGENCY_MODE_THRESHOLD', '0.00001'))  # Ativar modo emergência se ETH < 0.00001
EMERGENCY_TRADE_AMOUNT = float(os.getenv('EMERGENCY_TRADE_AMOUNT', '0.000020'))  # Trade ULTRA mínimo em modo emergência
EMERGENCY_GAS_PRICE = int(os.getenv('EMERGENCY_GAS_PRICE', '1'))  # Gas price ULTRA baixo em emergência (0.1 gwei)
BALANCE_GROWTH_THRESHOLD = float(os.getenv('BALANCE_GROWTH_THRESHOLD', '0.003980'))  # Quando dobrar trade size

# Configurações de Trading Inteligente - MODO AGRESSIVO PARA CRESCIMENTO RÁPIDO
MEMECOIN_MODE = os.getenv('MEMECOIN_MODE', 'true').lower() == 'true'  # Habilitado para memecoins
ALL_TOKENS_MODE = os.getenv('ALL_TOKENS_MODE', 'true').lower() == 'true'  # Detectar TODOS os tokens
MIN_TOKEN_AGE_MINUTES = int(os.getenv('MIN_TOKEN_AGE_MINUTES', '0'))  # Tokens brand new
MAX_TOKEN_AGE_HOURS = int(os.getenv('MAX_TOKEN_AGE_HOURS', '72'))  # Expandido para mais oportunidades
TARGET_PROFIT_PERCENTAGE = float(os.getenv('TARGET_PROFIT_PERCENTAGE', '25'))  # Lucro mais agressivo (25% para crescimento rápido)
AGGRESSIVE_TRADING = os.getenv('AGGRESSIVE_TRADING', 'true').lower() == 'true'  # Trading agressivo
QUICK_PROFIT_MODE = os.getenv('QUICK_PROFIT_MODE', 'true').lower() == 'true'  # Lucros rápidos

# DEX Configuration
ENABLE_UNISWAP_V3 = os.getenv('ENABLE_UNISWAP_V3', 'true').lower() == 'true'
ENABLE_AERODROME = os.getenv('ENABLE_AERODROME', 'true').lower() == 'true'
ENABLE_BASESWAP = os.getenv('ENABLE_BASESWAP', 'true').lower() == 'true'
ENABLE_SUSHISWAP = os.getenv('ENABLE_SUSHISWAP', 'true').lower() == 'true'

# Security Settings - Otimizado para memecoins com crescimento rápido
ENABLE_MEV_PROTECTION = os.getenv('ENABLE_MEV_PROTECTION', 'true').lower() == 'true'
MIN_LIQUIDITY_USD = float(os.getenv('MIN_LIQUIDITY_USD', '1500'))  # Mais agressivo para memecoins (reduzido para mais oportunidades)
MAX_TRADE_IMPACT = float(os.getenv('MAX_TRADE_IMPACT', '10'))  # Mais flexível para oportunidades
MIN_SCORE_TO_BUY = int(os.getenv('MIN_SCORE_TO_BUY', '30'))  # Score reduzido para mais trades (crescimento rápido)
ENABLE_HONEYPOT_CHECK = os.getenv('ENABLE_HONEYPOT_CHECK', 'true').lower() == 'true'
RISK_TOLERANCE = os.getenv('RISK_TOLERANCE', 'high').lower()  # high, medium, low

# Trading Mode - MODO REAL HABILITADO
SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'  # DESABILITADO - TRADING REAL
REAL_TRADING_ENABLED = os.getenv('REAL_TRADING_ENABLED', 'true').lower() == 'true'  # HABILITADO
FAST_MODE = os.getenv('FAST_MODE', 'true').lower() == 'true'  # Modo rápido para oportunidades
MEV_PROTECTION = os.getenv('MEV_PROTECTION', 'true').lower() == 'true'  # Proteção MEV

# Performance Settings
TRANSACTION_TIMEOUT = int(os.getenv('TRANSACTION_TIMEOUT', '30'))  # Timeout para transações
CONFIRMATION_BLOCKS = int(os.getenv('CONFIRMATION_BLOCKS', '1'))  # Confirmações necessárias
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # Tentativas máximas
SCAN_INTERVAL = float(os.getenv('SCAN_INTERVAL', '0.5'))  # Intervalo de scan em segundos
PRIORITY_FEE = int(os.getenv('PRIORITY_FEE', '2'))  # Priority fee em Gwei

# Security Thresholds
MIN_LIQUIDITY_ETH = float(os.getenv('MIN_LIQUIDITY_ETH', '0.5'))  # Liquidez mínima em ETH
MIN_HOLDERS = int(os.getenv('MIN_HOLDERS', '10'))  # Holders mínimos
MIN_TOKEN_AGE = int(os.getenv('MIN_TOKEN_AGE', '0'))  # Idade mínima do token em segundos
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

# Gas Configuration - OTIMIZADO PARA BASE NETWORK
DEFAULT_GAS_LIMIT = 400000  # Aumentado para Base Network
PRIORITY_GAS_LIMIT = 600000  # Aumentado para transações complexas
APPROVAL_GAS_LIMIT = 100000  # Gas específico para aprovações
SWAP_GAS_LIMIT = 350000     # Gas específico para swaps

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