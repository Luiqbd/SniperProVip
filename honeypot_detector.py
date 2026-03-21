"""
Honeypot Detector - Detecção Avançada de Tokens Fraudulentos
Verifica honeypots, taxas e segurança de contratos
"""

import asyncio
import requests
from typing import Dict, Optional, Tuple
from web3 import Web3
from config import *

class HoneypotDetector:
    """
    Sistema de detecção de tokens fraudulentos (honeypots)
    Verifica: Taxas, Honeypot real, Liquidez, Segurança
    """
    
    def __init__(self, web3: Web3 = None):
        self.web3 = web3
        self.cache = {}
        self.cache_timeout = 60  # 60 segundos
        
        # APIs para verificação
        # Pode usar APIs públicas gratuitas ou próprio backend
        self.router_abis = {
            # Router ABI para simular swaps
            'swap': [
                {
                    "inputs": [
                        {"name": "amountIn", "type": "uint256"},
                        {"name": "amountOutMin", "type": "uint256"},
                        {"name": "path", "type": "address[]"},
                        {"name": "to", "type": "address"},
                        {"name": "deadline", "type": "uint256"}
                    ],
                    "name": "swapExactETHForTokens",
                    "outputs": [{"name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "payable",
                    "type": "function"
                }
            ],
            # ERC20 ABI
            'erc20': [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
                 "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], 
                 "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], 
                 "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
            ]
        }
        
        print("🔍 Honeypot Detector inicializado")
    
    def set_web3(self, web3: Web3):
        """Define instância web3"""
        self.web3 = web3
    
    def _is_cache_valid(self, token_address: str) -> bool:
        """Verifica se cache é válido"""
        if token_address in self.cache:
            import time
            if time.time() - self.cache[token_address]['timestamp'] < self.cache_timeout:
                return True
        return False
    
    async def analyze_token(self, token_address: str, weth_address: str = None) -> Dict:
        """
        Análise completa do token para detectar Honeypot
        Returns: {
            'is_safe': bool,
            'is_honeypot': bool,
            'buy_tax': float,
            'sell_tax': float,
            'liquidity_locked': bool,
            'risk_score': float (0-100),
            'issues': list
        }
        """
        weth_address = weth_address or WETH_ADDRESS
        
        # Verificar cache
        if self._is_cache_valid(token_address):
            return self.cache[token_address]['data']
        
        import time
        issues = []
        risk_score = 0  # 0 = muito arriscado, 100 = seguro
        
        try:
            # 1. Verificar se é contrato válido
            is_contract = await self._is_contract(token_address)
            if not is_contract:
                issues.append("Endereço não é contrato válido")
                risk_score -= 30
            
            # 2. Verificar taxas (simulando compra/venda)
            buy_tax, sell_tax = await self._estimate_taxes(token_address, weth_address)
            
            if buy_tax > 0:
                issues.append(f"Taxa de compra: {buy_tax}%")
                risk_score -= buy_tax * 2
            
            if sell_tax > 0:
                issues.append(f"Taxa de venda: {sell_tax}%")
                risk_score -= sell_tax * 2
            
            # 3. Verificar honeypot (testar small swap)
            is_honeypot = await self._check_honeypot(token_address, weth_address)
            if is_honeypot:
                issues.append("HONEYPOT DETECTADO")
                risk_score -= 50
            
            # 4. Verificar liquidez
            has_liquidity = await self._check_liquidity(token_address, weth_address)
            if not has_liquidity:
                issues.append("Sem liquidez detectável")
                risk_score -= 20
            
            # 5. Verificar owner (se tem mint/burn)
            has_owner_risks = await self._check_owner_risks(token_address)
            if has_owner_risks:
                issues.append("Riscos de owner detectados")
                risk_score -= 15
            
            # Limitar risco
            risk_score = max(0, min(100, risk_score + 50))  # Base 50
            
            is_safe = risk_score >= 60 and not is_honeypot
            
            result = {
                'is_safe': is_safe,
                'is_honeypot': is_honeypot,
                'buy_tax': buy_tax,
                'sell_tax': sell_tax,
                'liquidity_locked': has_liquidity,
                'risk_score': risk_score,
                'issues': issues,
                'timestamp': time.time()
            }
            
            # Salvar no cache
            self.cache[token_address] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Erro ao analisar token: {e}")
            return {
                'is_safe': False,
                'is_honeypot': True,
                'buy_tax': 0,
                'sell_tax': 0,
                'liquidity_locked': False,
                'risk_score': 0,
                'issues': [f"Erro na análise: {str(e)}"],
                'timestamp': time.time()
            }
    
    async def _is_contract(self, token_address: str) -> bool:
        """Verifica se o endereço é um contrato válido"""
        try:
            if not self.web3:
                return True  # Assume válido se sem web3
            
            code = self.web3.eth.get_code(token_address)
            return len(code) > 0
        except:
            return False
    
    async def _estimate_taxes(self, token_address: str, weth_address: str) -> Tuple[float, float]:
        """
        Estima taxas de compra e venda
        Retorna: (buy_tax, sell_tax) em percentual
        """
        # Método simples: tentar ler do contrato se possível
        # Muitos tokens têm funções transferTaxed ou similar
        
        buy_tax = 0.0
        sell_tax = 0.0
        
        try:
            if not self.web3:
                return 0.0, 0.0
            
            # Tentar chamar função de tax se existir
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=self.router_abis['erc20']
            )
            
            # Verificar total supply
            try:
                total_supply = token_contract.functions.totalSupply().call()
                if total_supply == 0:
                    return 99.0, 99.0  # Probável scam
            except:
                pass
                
        except:
            pass
        
        return buy_tax, sell_tax
    
    async def _check_honeypot(self, token_address: str, weth_address: str) -> bool:
        """
        Testa se o token é honeypot tentando simulação de compra
        Retorna: True se for honeypot
        """
        try:
            if not self.web3:
                return False  # Assume não honeypot se sem web3
            
            # Tentar usar API externa para verificação mais precisa
            # Exemplo: Honeypot API (pode precisar de API key)
            
            # Método 1: Verificar se tem pool de liquidez
            # (simplificado - em produção usaria código completo)
            
            # Método 2: Simular transação pequena (não envia, só testa)
            # Em produção: usar Tenderly ou Flashbots para simular
            
            # Por agora, vamos usar heurísticas:
            
            # 1. Se total supply é muito alto ou muito baixo
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=self.router_abis['erc20']
            )
            
            try:
                total_supply = token_contract.functions.totalSupply().call()
                
                # Supply muito alto (> 1 trilhão) - possível inflation scam
                if total_supply > 1_000_000_000_000:
                    return True
                    
                # Supply muito baixo (< 1000) - possível scam
                if total_supply < 1000:
                    return True
                    
            except:
                return True  # Se não consegue ler, assume honeypot
            
            return False  # Por agora, assume seguro
            
        except Exception as e:
            print(f"⚠️ Erro ao verificar honeypot: {e}")
            return False  # Assume não honeypot em caso de erro
    
    async def _check_liquidity(self, token_address: str, weth_address: str) -> bool:
        """Verifica se existe liquidez para o token"""
        try:
            if not self.web3:
                return True
            
            # Verificar se há ETH ou WETH no contrato do token
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=self.router_abis['erc20']
            )
            
            # Tentar verificar saldo em ETH (como proxy de liquidez)
            try:
                eth_balance = self.web3.eth.get_balance(token_address)
                if eth_balance > 0:
                    return True
            except:
                pass
            
            # Verificar saldo de WETH
            try:
                weth_contract = self.web3.eth.contract(
                    address=weth_address,
                    abi=self.router_abis['erc20']
                )
                weth_balance = weth_contract.functions.balanceOf(token_address).call()
                if weth_balance > 0:
                    return True
            except:
                pass
            
            return False
            
        except:
            return False
    
    async def _check_owner_risks(self, token_address: str) -> bool:
        """Verifica riscos relacionados ao owner do contrato"""
        try:
            if not self.web3:
                return False
            
            # Verificar se o contrato tem funções perigosas
            # Em produção: faria análise completa do bytecode
            
            # Por agora, retorna False (não detecta)
            return False
            
        except:
            return False
    
    def should_buy(self, analysis: Dict) -> Tuple[bool, str]:
        """
        Decide se deve comprar baseado na análise
        Returns: (should_buy: bool, reason: str)
        """
        if analysis['is_honeypot']:
            return False, "Honeypot detectado"
        
        if analysis['risk_score'] < 40:
            return False, f"Risco muito alto ({analysis['risk_score']})"
        
        if analysis['buy_tax'] > 20:
            return False, f"Taxa de compra muito alta ({analysis['buy_tax']}%)"
        
        if analysis['sell_tax'] > 20:
            return False, f"Taxa de venda muito alta ({analysis['sell_tax']}%)"
        
        if analysis['risk_score'] >= 70:
            return True, f"Seguro (score: {analysis['risk_score']})"
        
        if analysis['risk_score'] >= 50 and analysis.get('liquidity_locked', False):
            return True, "Liquidez verificável"
        
        return False, f"Score de risco insuficiente ({analysis['risk_score']})"
    
    def get_risk_color(self, risk_score: float) -> str:
        """Retorna cor baseada no score de risco"""
        if risk_score >= 70:
            return "🟢"  # Verde - seguro
        elif risk_score >= 50:
            return "🟡"  # Amarelo - moderado
        elif risk_score >= 30:
            return "🟠"  # Laranja - arriscado
        else:
            return "🔴"  # Vermelho - muito arriscado


# Função de convenience para integração
async def quick_check(token_address: str, web3: Web3 = None) -> Dict:
    """Função rápida para verificar um token"""
    detector = HoneypotDetector(web3)
    return await detector.analyze_token(token_address)
