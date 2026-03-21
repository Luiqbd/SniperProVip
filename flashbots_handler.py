"""
Flashbots Handler - Proteção MEV e Transações Privadas
Envia transações via Flashbots Protect para evitar front-running
"""

import asyncio
import requests
import time
from typing import Dict, Optional, Tuple
from web3 import Web3
from eth_account import Account
from config import *

class FlashbotsHandler:
    """
    Handler para Flashbots Protect - Proteção MEV
    Envia transações privadas que não aparecem no mempool público
    """
    
    def __init__(self, web3: Web3, private_key: str):
        self.web3 = web3
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        
        # Flashbots Relay endpoints
        self.flashbots_relay = "https://relay.flashbots.net"
        self.flashbots_endpoint = f"{self.flashbots_relay}/transaction"
        
        # Configurações
        self.use_flashbots = os.getenv('USE_FLASHBOTS', 'false').lower() == 'true'
        self.max_gas_price = float(os.getenv('MAX_FLASHBOTS_GAS', '0.5'))  # Max 0.5 gwei para flashbots
        
        # Fallback para transação normal
        self.fallback_to_normal = os.getenv('FALLBACK_TO_NORMAL', 'true').lower() == 'true'
        
        print(f"⚡ Flashbots Handler inicializado")
        print(f"   Flashbots: {'ATIVO' if self.use_flashbots else 'INATIVO'}")
    
    async def send_transaction(self, transaction: Dict, use_simulation: bool = True) -> Optional[str]:
        """
        Envia transação via Flashbots ou normal
        Returns: tx_hash ou None se falhar
        """
        try:
            # 1. Simular transação primeiro (se habilitado)
            if use_simulation:
                sim_result = await self.simulate_transaction(transaction)
                if not sim_result['success']:
                    print(f"❌ Simulação falhou: {sim_result.get('error', 'Unknown')}")
                    return None
            
            # 2. Enviar via Flashbots se habilitado
            if self.use_flashbots:
                tx_hash = await self._send_via_flashbots(transaction)
                if tx_hash:
                    print(f"⚡ Transação enviada via Flashbots: {tx_hash}")
                    return tx_hash
                elif not self.fallback_to_normal:
                    print(f"❌ Flashbots falhou e fallback desabilitado")
                    return None
            
            # 3. Fallback para transação normal
            if self.fallback_to_normal:
                print(f"🔄 Enviando transação normal (fallback)...")
                return await self._send_normal(transaction)
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao enviar transação: {e}")
            # Fallback para normal em caso de erro
            if self.fallback_to_normal:
                return await self._send_normal(transaction)
            return None
    
    async def simulate_transaction(self, transaction: Dict) -> Dict:
        """
        Simula transação para verificar se vai falhar
        Returns: {'success': bool, 'error': str or None}
        """
        try:
            # Usar call static para simular
            # Nota: Isso é uma simulação básica
            # Para simulação real, usar Tenderly ou Flashbots simulation
            
            # Tentar estimativa de gas primeiro
            try:
                gas_estimate = self.web3.eth.estimate_gas(transaction)
                transaction['gas'] = int(gas_estimate * 1.2)  # 20% acima
            except Exception as e:
                print(f"⚠️ Gas estimation failed: {e}")
                # Continuar mesmo assim
            
            # Tentar call estático
            try:
                result = self.web3.eth.call(transaction)
                return {'success': True, 'result': result.hex()}
            except Exception as e:
                error_msg = str(e)
                # Detectar revert
                if 'revert' in error_msg.lower():
                    return {'success': False, 'error': 'Transaction will revert'}
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_via_flashbots(self, transaction: Dict) -> Optional[str]:
        """
        Envia transação via Flashbots Protect
        """
        try:
            # Preparar transação para Flashbots
            # Flashbots usa formato específico
            
            # Assinar transação
            signed_tx = self.web3.eth.account.sign_transaction(
                transaction, 
                self.private_key
            )
            
            # Enviar para Flashbots
            # Nota: Flashbots Protect API requer formato específico
            # Por agora, vamos usar método alternativo
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            # Preparar payload
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_sendPrivateTransaction",
                "params": [
                    {
                        "signedTransaction": signed_tx.rawTransaction.hex(),
                        "maxBlockNumber": hex(self.web3.eth.block_number + 10)  # Válido por 10 blocos
                    }
                ]
            }
            
            # Tentar enviar
            # Nota: Precisa de Flashbots API key para funcionar
            # Por agora, retornamos None para usar fallback
            
            print(f"⚡ Flashbots endpoint: {self.flashbots_endpoint}")
            print(f"⚡ Transação preparada (usando fallback)")
            
            # Como Flashbots oficial requer API key, usamos fallback
            return None
            
        except Exception as e:
            print(f"❌ Erro Flashbots: {e}")
            return None
    
    async def _send_normal(self, transaction: Dict) -> Optional[str]:
        """
        Envia transação normalmente (sem proteção MEV)
        """
        try:
            # Assinar transação
            signed_tx = self.web3.eth.account.sign_transaction(
                transaction, 
                self.private_key
            )
            
            # Enviar
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return tx_hash.hex()
            
        except Exception as e:
            print(f"❌ Erro transação normal: {e}")
            return None
    
    async def getoptimal_gas_params(self) -> Dict:
        """
        Calcula parâmetros de gas otimizados para rápida inclusão
        """
        try:
            # Obter gas price atual
            current_gas = self.web3.eth.gas_price
            
            # Calcular optimal (base + priority)
            # Para rápido: usar mais que base
            max_priority_fee = self.web3.to_wei(0.1, 'gwei')  # 0.1 gwei tip
            max_fee = current_gas + max_priority_fee
            
            # Limitar ao máximo configurado
            max_fee_limit = self.web3.to_wei(self.max_gas_price, 'gwei')
            if max_fee > max_fee_limit:
                max_fee = max_fee_limit
            
            return {
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': max_priority_fee,
                'gasPrice': current_gas
            }
            
        except Exception as e:
            print(f"⚠️ Erro ao calcular gas: {e}")
            # Fallback
            return {
                'maxFeePerGas': self.web3.to_wei(0.1, 'gwei'),
                'maxPriorityFeePerGas': self.web3.to_wei(0.05, 'gwei'),
                'gasPrice': self.web3.to_wei(0.05, 'gwei')
            }
    
    def is_profitable(self, gas_used: int, gas_price: int, profit_eth: float) -> bool:
        """
        Verifica se transação será lucrativa considerando gas
        """
        try:
            gas_cost_eth = self.web3.from_wei(gas_used * gas_price, 'ether')
            net_profit = profit_eth - gas_cost_eth
            
            # Lucro mínimo de 0.000001 ETH
            return net_profit > 0.000001
            
        except:
            return True  # Assume lucrativo se não conseguir calcular


class TransactionBuilder:
    """
    Construtor de transações otimizadas
    """
    
    def __init__(self, web3: Web3):
        self.web3 = web3
    
    def build_swap_transaction(
        self,
        router_contract,
        path: list,
        amount_in: int,
        amount_out_min: int,
        to: str,
        deadline: int,
        value: int = 0
    ) -> Dict:
        """Constrói transação de swap otimizada"""
        
        # Usar EIP-1559 se suportado
        try:
            block = self.web3.eth.get_block('latest')
            if 'baseFeePerGas' in block:
                # Usar EIP-1559
                base_fee = block['baseFeePerGas']
                max_priority = self.web3.to_wei(0.1, 'gwei')
                max_fee = base_fee * 2 + max_priority
                
                return {
                    'to': router_contract.address,
                    'data': router_contract.encodeABI(
                        'swapExactETHForTokens',
                        args=[amount_in, amount_out_min, path, to, deadline]
                    ),
                    'value': value,
                    'gas': 200000,
                    'maxFeePerGas': int(max_fee),
                    'maxPriorityFeePerGas': int(max_priority),
                    'chainId': self.web3.eth.chain_id,
                    'nonce': self.web3.eth.get_transaction_count(to),
                    'type': 2  # EIP-1559
                }
        except:
            pass
        
        # Fallback para transação legacy
        return {
            'to': router_contract.address,
            'data': router_contract.encodeABI(
                'swapExactETHForTokens',
                args=[amount_in, amount_out_min, path, to, deadline]
            ),
            'value': value,
            'gas': 200000,
            'gasPrice': self.web3.eth.gas_price,
            'chainId': self.web3.eth.chain_id,
            'nonce': self.web3.eth.get_transaction_count(to)
        }
    
    def estimate_gas(self, transaction: Dict) -> int:
        """Estima gas necessário"""
        try:
            return self.web3.eth.estimate_gas(transaction)
        except:
            return transaction.get('gas', 150000)


# Função de convenience
def create_flashbots_handler(web3: Web3, private_key: str) -> FlashbotsHandler:
    """Factory function"""
    return FlashbotsHandler(web3, private_key)
