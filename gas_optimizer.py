"""
Gas Optimizer - Otimização Inteligente de Gas
Calcula o gas price ideal para transações rápidas com menor custo
"""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
from web3 import Web3
from config import *

class GasOptimizer:
    """
    Otimizador de gas que encontra o preço ideal para transações
    Balanceia velocidade vs custo
    """
    
    def __init__(self, web3: Web3):
        self.web3 = web3
        
        # Histórico de gas prices
        self.gas_history = deque(maxlen=100)
        self.last_update = 0
        self.update_interval = 15  # Segundos
        
        # Configurações
        self.speed_mode = os.getenv('GAS_SPEED_MODE', 'balanced').lower()  # fast/balanced/cheaper
        self.max_gas_price = float(os.getenv('MAX_GAS_PRICE', '1'))  # Max 1 gwei
        self.min_gas_price = float(os.getenv('MIN_GAS_PRICE', '0.01'))  # Min 0.01 gwei
        
        # Multiplicadores por modo
        self.speed_multipliers = {
            'fast': 1.5,      # Rápido = 150% do gas price
            'balanced': 1.2,   # Balanceado = 120%
            'cheaper': 1.0     # Barato = 100%
        }
        
        print(f"⛽ Gas Optimizer inicializado")
        print(f"   Modo: {self.speed_mode}")
        print(f"   Max gas: {self.max_gas_price} gwei")
    
    async def get_optimal_gas_price(self) -> int:
        """
        Calcula o gas price ideal baseado no modo
        Returns: gas price em wei
        """
        current_time = time.time()
        
        # Atualizar histórico se necessário
        if current_time - self.last_update > self.update_interval:
            await self._update_gas_history()
        
        # Obter gas base da rede
        base_gas = await self._get_current_gas_price()
        
        # Aplicar multiplicador baseado no modo
        multiplier = self.speed_multipliers.get(self.speed_mode, 1.2)
        optimal_gas = int(base_gas * multiplier)
        
        # Aplicar limites
        min_gas_wei = self.web3.to_wei(self.min_gas_price, 'gwei')
        max_gas_wei = self.web3.to_wei(self.max_gas_price, 'gwei')
        
        optimal_gas = max(min_gas_wei, min(optimal_gas, max_gas_wei))
        
        return optimal_gas
    
    async def _get_current_gas_price(self) -> int:
        """Obtém gas price atual da rede"""
        try:
            return self.web3.eth.gas_price
        except:
            return self.web3.to_wei(0.1, 'gwei')  # Fallback
    
    async def _update_gas_history(self):
        """Atualiza histórico de gas prices"""
        try:
            current = await self._get_current_gas_price()
            self.gas_history.append({
                'price': current,
                'timestamp': time.time()
            })
            self.last_update = time.time()
        except:
            pass
    
    async def predict_next_block_gas(self) -> Dict:
        """
        Prediz gas price para o próximo bloco
        """
        if len(self.gas_history) < 2:
            return {
                'current': await self._get_current_gas_price(),
                'predicted': await self._get_current_gas_price(),
                'trend': 'stable'
            }
        
        # Calcular tendência
        recent = list(self.gas_history)[-5:]
        if len(recent) < 2:
            trend = 'stable'
        elif recent[-1]['price'] > recent[0]['price'] * 1.1:
            trend = 'rising'
        elif recent[-1]['price'] < recent[0]['price'] * 0.9:
            trend = 'falling'
        else:
            trend = 'stable'
        
        # Média recente
        avg_gas = sum(h['price'] for h in recent) / len(recent)
        
        # Prever próximo
        if trend == 'rising':
            predicted = int(avg_gas * 1.1)
        elif trend == 'falling':
            predicted = int(avg_gas * 0.9)
        else:
            predicted = int(avg_gas)
        
        return {
            'current': recent[-1]['price'],
            'predicted': predicted,
            'trend': trend,
            'history': len(self.gas_history)
        }
    
    def set_speed_mode(self, mode: str):
        """Define modo de velocidade"""
        if mode in self.speed_multipliers:
            self.speed_mode = mode
            print(f"⛽ Modo de gas alterado para: {mode}")
    
    async def get_eip_1559_params(self) -> Dict:
        """
        Calcula parâmetros EIP-1559 (type 2 transaction)
        """
        try:
            block = await self.web3.eth.get_block('latest')
            
            if 'baseFeePerGas' not in block:
                # Rede não suporta EIP-1559
                return await self._get_legacy_params()
            
            base_fee = block['baseFeePerGas']
            
            # Priority fee (tip)
            max_priority = self.web3.to_wei(0.1, 'gwei')  # 0.1 gwei tip
            priority_fee = int(max_priority * self.speed_multipliers.get(self.speed_mode, 1.0))
            
            # Max fee = base + priority * 2 (para 2 blocos)
            max_fee = base_fee + (priority_fee * 2)
            
            # Limitar
            max_fee_limit = self.web3.to_wei(self.max_gas_price, 'gwei')
            max_fee = min(max_fee, max_fee_limit)
            
            return {
                'type': 2,  # EIP-1559
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': priority_fee,
                'baseFeePerGas': base_fee
            }
            
        except Exception as e:
            print(f"⚠️ Erro EIP-1559: {e}")
            return await self._get_legacy_params()
    
    async def _get_legacy_params(self) -> Dict:
        """Parâmetros para transação legacy (não EIP-1559)"""
        gas_price = await self.get_optimal_gas_price()
        
        return {
            'type': 0,  # Legacy
            'gasPrice': gas_price
        }
    
    def calculate_gas_cost(self, gas_limit: int, gas_price: int) -> float:
        """Calcula custo em ETH"""
        return self.web3.from_wei(gas_limit * gas_price, 'ether')
    
    async def should_wait_for_lower_gas(self) -> tuple[bool, str]:
        """
        Decide se deve esperar por gas mais baixo
        """
        prediction = await self.predict_next_block_gas()
        
        if prediction['trend'] == 'falling':
            wait_time = 30  # Esperar 30 segundos
            return True, f"Gas caindo ({prediction['trend']}), espere {wait_time}s"
        
        return False, "Gas atual é bom"


class GasCalculator:
    """
    Calculadora de custos de gas para operações
    """
    
    # Estimativas de gas por operação
    GAS_ESTIMATES = {
        'swap_eth_to_token': 180000,
        'swap_token_to_eth': 200000,
        'swap_token_to_token': 250000,
        'approve': 50000,
        'transfer': 65000,
        'withdraw': 25000
    }
    
    def __init__(self, web3: Web3, optimizer: GasOptimizer):
        self.web3 = web3
        self.optimizer = optimizer
    
    async def estimate_swap_cost(self, is_buy: bool = True) -> Dict:
        """
        Estima custo de um swap
        """
        operation = 'swap_eth_to_token' if is_buy else 'swap_token_to_eth'
        gas_limit = self.GAS_ESTIMATES.get(operation, 150000)
        
        gas_price = await self.optimizer.get_optimal_gas_price()
        
        cost_wei = gas_limit * gas_price
        cost_eth = self.web3.from_wei(cost_wei, 'ether')
        
        # Com EIP-1559
        eip1559 = await self.optimizer.get_eip_1559_params()
        if eip1559.get('type') == 2:
            cost_eip1559 = gas_limit * eip1559['maxFeePerGas']
            cost_eip1559_eth = self.web3.from_wei(cost_eip1559, 'ether')
        else:
            cost_eip1559_eth = cost_eth
        
        return {
            'operation': operation,
            'gas_limit': gas_limit,
            'gas_price': gas_price,
            'cost_eth': cost_eth,
            'cost_eip1559_eth': cost_eip1559_eth,
            'eip1559_params': eip1559
        }
    
    def is_profitable_after_gas(self, profit_eth: float, cost_eth: float, min_profit: float = 0.000001) -> bool:
        """Verifica se ainda é lucrativo após pagar gas"""
        net_profit = profit_eth - cost_eth
        return net_profit >= min_profit
    
    def calculate_breakeven(self, gas_cost_eth: float, buy_amount_eth: float, target_profit_pct: float = 10) -> float:
        """
        Calcula quanto precisa vender para cobrir gas + lucro
        """
        target_profit = buy_amount_eth * (target_profit_pct / 100)
        breakeven = gas_cost_eth + target_profit
        return breakeven


async def get_optimal_gas(web3: Web3, mode: str = 'balanced') -> int:
    """Função convenience"""
    optimizer = GasOptimizer(web3)
    optimizer.set_speed_mode(mode)
    return await optimizer.get_optimal_gas_price()


# Exemplo de uso:
# optimizer = GasOptimizer(web3)
# gas_price = await optimizer.get_optimal_gas_price()
# eip1559 = await optimizer.get_eip_1559_params()
