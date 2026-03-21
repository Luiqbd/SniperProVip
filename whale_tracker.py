"""
Whale Tracker - Rastreamento de Baleias e Carteiras Grandes
Detecta movimentos de carteiras grandes para copiar trades
"""

import asyncio
import time
from typing import Dict, List, Optional, Set
from collections import deque
from web3 import Web3
from config import *

class WhaleTracker:
    """
    Rastreia movimentos de baleias (carteiras grandes)
    e alerta quando detecta compras/vendas significativas
    """
    
    def __init__(self, web3: Web3):
        self.web3 = web3
        
        # Configurações
        self.min_whale_balance = float(os.getenv('MIN_WHALE_BALANCE', '10'))  # 10 ETH mínimo
        self.min_whale_tx = float(os.getenv('MIN_WHALE_TX', '1'))  # 1 ETH por transação
        self.alert_threshold = float(os.getenv('WHALE_ALERT_THRESHOLD', '0.5'))  # 0.5 ETH mínimo
        
        # Histórico de baleias conhecidas (endereços de exchanges e carteiras grandes)
        self.whale_addresses: Set[str] = set()
        self._load_known_whales()
        
        # Cache de transações recentes
        self.tx_cache = deque(maxlen=1000)
        self.last_check = 0
        self.check_interval = 10  # Segundos entre verificações
        
        # Alertas
        self.recent_alerts = deque(maxlen=50)
        
        # Estatísticas
        self.total_whale_trades = 0
        self.watched_tokens = {}  # token_address -> whale activity
        
        print(f"🐋 Whale Tracker inicializado")
        print(f"   Baleias conhecidas: {len(self.whale_addresses)}")
        print(f"   Mínimo para alerta: {self.alert_threshold} ETH")
    
    def _load_known_whales(self):
        """Carrega lista de baleias conhecidas (exchanges, carteiras grandes)"""
        # Endereços de exchanges conocidos (exemplos)
        known_exchanges = [
            "0x8EB8a3b98659C6B723283978Af853b1C4e8C1eE4",  # Binance Hot Wallet
            "0x28C6c06298d514Db089934071355E5743bf21d61",  # Binance Cold
            "0xF977814e90dA44bFA03b6295A0616a897441aceC",  # Binance
            "0x47ac0Fb4F2D84898e4D9E7b4DaB3C75907c89E2e",  # Kraken
            "0xCOINBASE",  # Coinbase (adicionar address real)
            "0x76E6E5E8b13e93dE94A60aaE6473C657Fe9dC6A",  # Gemini
            "0x6aC5d21dcc0155E6f24B6F30eb35B86e62b2114",  # Bitfinex
        ]
        
        for addr in known_exchanges:
            if addr != "0xCOINBASE":
                self.whale_addresses.add(addr.lower())
    
    def add_whale_address(self, address: str):
        """Adiciona um endereço para monitorar"""
        addr = address.lower()
        if addr not in self.whale_addresses:
            self.whale_addresses.add(addr)
            print(f"🐋 Nova baleia adicionada: {addr[:10]}...")
    
    def remove_whale_address(self, address: str):
        """Remove um endereço da lista"""
        addr = address.lower()
        if addr in self.whale_addresses:
            self.whale_addresses.discard(addr)
    
    def is_whale(self, address: str) -> bool:
        """Verifica se um endereço é uma baleia conhecida"""
        return address.lower() in self.whale_addresses
    
    async def check_for_whale_trades(self, token_address: str = None) -> List[Dict]:
        """
        Verifica se há movimentações de baleias
        Returns: lista de transações de baleias
        """
        current_time = time.time()
        if current_time - self.last_check < self.check_interval:
            return []
        
        self.last_check = current_time
        whale_trades = []
        
        try:
            # Verificar últimas transações do token
            # Em produção: usar API de indexação (The Graph, Alchemy, etc.)
            
            # Por agora, verificar se há baleias conhecidas operando
            # Isso é uma implementação simplificada
            
            # Verificar baleias na mempool
            # (simplificado - em produção usaria mempool scanner)
            
            return whale_trades
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar baleias: {e}")
            return []
    
    async def get_top_holders(self, token_address: str, limit: int = 10) -> List[Dict]:
        """
        Obtém os maiores holders de um token
        Returns: lista de {address, balance}
        """
        holders = []
        
        try:
            if not self.web3:
                return holders
            
            # ERC20 balanceOf
            erc20_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
                 "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
            ]
            
            contract = self.web3.eth.contract(
                address=token_address,
                abi=erc20_abi
            )
            
            # Verificar alguns endereços conhecidos
            test_addresses = list(self.whale_addresses)[:limit]
            
            for addr in test_addresses:
                try:
                    balance = contract.functions.balanceOf(addr).call()
                    if balance > 0:
                        balance_eth = self.web3.from_wei(balance, 'ether')
                        holders.append({
                            'address': addr,
                            'balance': balance_eth,
                            'is_whale': True
                        })
                except:
                    continue
            
            # Ordenar por balance
            holders.sort(key=lambda x: x['balance'], reverse=True)
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar holders: {e}")
        
        return holders[:limit]
    
    async def analyze_whale_activity(self, token_address: str) -> Dict:
        """
        Analisa atividade de baleias em um token
        Returns: {
            'whale_holders': int,
            'whale_balance_total': float,
            'whale_concentration': float,
            'signal': 'STRONG_BUY'/'BUY'/'NEUTRAL'/'SELL'
        }
        """
        try:
            holders = await self.get_top_holders(token_address)
            
            if not holders:
                return {
                    'whale_holders': 0,
                    'whale_balance_total': 0,
                    'whale_concentration': 0,
                    'signal': 'NEUTRAL'
                }
            
            total_whale_balance = sum(h['balance'] for h in holders)
            whale_count = len(holders)
            
            # Calcular concentração (quanto maior, mais baleias têm o token)
            concentration = total_whale_balance if whale_count > 0 else 0
            
            # Determinar sinal
            if concentration > 100:  # Muita baleia
                signal = 'STRONG_BUY'
            elif concentration > 10:
                signal = 'BUY'
            elif concentration < 0.1:
                signal = 'SELL'
            else:
                signal = 'NEUTRAL'
            
            return {
                'whale_holders': whale_count,
                'whale_balance_total': total_whale_balance,
                'whale_concentration': concentration,
                'signal': signal,
                'top_holders': holders[:5]
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao analisar atividade: {e}")
            return {
                'whale_holders': 0,
                'whale_balance_total': 0,
                'whale_concentration': 0,
                'signal': 'NEUTRAL'
            }
    
    def should_follow_whale(self, whale_address: str, token_address: str, amount_eth: float) -> tuple[bool, str]:
        """
        Decide se deve seguir uma baleia
        Returns: (should_follow: bool, reason: str)
        """
        # Verificar se é baleia conhecida
        if not self.is_whale(whale_address):
            return False, "Endereço não é baleia conhecida"
        
        # Verificar tamanho da transação
        if amount_eth < self.alert_threshold:
            return False, f"Transação muito pequena ({amount_eth} ETH)"
        
        # Verificar se já estamos alertas
        recent = [a for a in self.recent_alerts 
                  if a['token'] == token_address 
                  and time.time() - a['timestamp'] < 300]  # 5 min
        
        if len(recent) > 3:
            return False, "Muitos alertas recentes para este token"
        
        return True, f"Baleia movimentação {amount_eth} ETH"
    
    def add_alert(self, alert_type: str, token_address: str, amount: float, details: str = ""):
        """Adiciona um alerta"""
        alert = {
            'type': alert_type,
            'token': token_address,
            'amount': amount,
            'details': details,
            'timestamp': time.time()
        }
        self.recent_alerts.append(alert)
        self.total_whale_trades += 1
        
        print(f"🐋 ALERTA DE BALEIA: {alert_type} {amount} ETH em {token_address[:10]}...")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Retorna alertas recentes"""
        return list(self.recent_alerts)[-limit:]
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas"""
        return {
            'total_whale_trades': self.total_whale_trades,
            'whale_addresses_count': len(self.whale_addresses),
            'recent_alerts': len(self.recent_alerts),
            'watched_tokens': len(self.watched_tokens)
        }


class MempoolScanner:
    """
    Scanner de Mempool para detectar transações antes da confirmação
    """
    
    def __init__(self, web3: Web3):
        self.web3 = web3
        self.pending_txs = {}
        self.new_tx_callback = None
        
        print(f"🔍 Mempool Scanner inicializado")
    
    def set_callback(self, callback):
        """Define callback para novas transações"""
        self.new_tx_callback = callback
    
    async def start_monitoring(self):
        """Inicia monitoramento da mempool"""
        print(f"🔍 Monitorando mempool...")
        
        last_block = self.web3.eth.block_number
        
        while True:
            try:
                current_block = self.web3.eth.block_number
                
                if current_block > last_block:
                    # Novos blocos confirmados
                    last_block = current_block
                
                # Verificar pending transactions
                # (simplificado - em produção usaria filter)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"⚠️ Erro no scanner: {e}")
                await asyncio.sleep(5)
    
    async def get_pending_tx_count(self) -> int:
        """Retorna número de transações pendentes"""
        try:
            # Contagem简易
            return len(self.pending_txs)
        except:
            return 0


def create_whale_tracker(web3: Web3) -> WhaleTracker:
    """Factory function"""
    return WhaleTracker(web3)
