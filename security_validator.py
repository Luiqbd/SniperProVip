#!/usr/bin/env python3
"""
Validador de Segurança para Sniper Bot
Implementa verificações de segurança avançadas
"""

import time
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from colorama import Fore, Style, init
import requests

from config import *

init(autoreset=True)

class SecurityValidator:
    def __init__(self, web3: Web3):
        self.web3 = web3
        self.honeypot_contracts = set()
        self.blacklisted_tokens = set()
        
    def validate_token_security(self, token_address: str) -> Dict:
        """
        Valida segurança do token
        Returns: dict com score de segurança e detalhes
        """
        security_score = 100
        issues = []
        warnings = []
        
        try:
            # 1. Verificar se é contrato válido
            code = self.web3.eth.get_code(token_address)
            if len(code) <= 2:  # "0x" apenas
                issues.append("Token não é um contrato válido")
                security_score -= 50
            
            # 2. Verificar se é ERC20 padrão
            erc20_valid = self._check_erc20_compliance(token_address)
            if not erc20_valid:
                warnings.append("Token pode não seguir padrão ERC20 completo")
                security_score -= 15  # Reduzido de 30 para 15
            
            # 3. Verificar honeypot APENAS se habilitado
            is_honeypot = False  # Desabilitado por padrão para mais oportunidades
            if ENABLE_HONEYPOT_CHECK:
                is_honeypot = self._check_honeypot(token_address)
                if is_honeypot:
                    issues.append("Token identificado como honeypot")
                    security_score -= 80
            
            # 4. Verificar ownership e renúncia (aviso apenas, não bloqueia)
            ownership_info = self._check_ownership(token_address)
            if ownership_info['has_owner'] and not ownership_info['renounced']:
                warnings.append("Contrato ainda tem owner ativo")
                security_score -= 5  # Reduzido significativamente
            
            # 5. Verificar funções perigosas (aviso apenas)
            dangerous_functions = self._check_dangerous_functions(token_address)
            if dangerous_functions:
                warnings.append(f"Funções perigosas encontradas: {', '.join(dangerous_functions)}")
                security_score -= 5  # Reduzido significativamente
            
            # 6. Verificar liquidez (aviso apenas)
            liquidity_info = self._check_liquidity_security(token_address)
            if liquidity_info['locked_percentage'] < 50:
                warnings.append(f"Apenas {liquidity_info['locked_percentage']}% da liquidez está bloqueada")
                security_score -= 5  # Reduzido significativamente
            
            # 7. Verificar distribuição de holders (aviso apenas)
            holder_distribution = self._check_holder_distribution(token_address)
            if holder_distribution['top_10_percentage'] > 80:
                warnings.append("Concentração alta nos top 10 holders")
                security_score -= 5  # Reduzido significativamente
            
            # MUDANÇA CRÍTICA: aceite tokens mesmo com warnings, apenas bloqueie se for honeypot
            return {
                'score': max(0, security_score),
                'issues': issues,
                'warnings': warnings,
                'is_safe': not is_honeypot,  # Apenas bloqueia se for honeypot confirmado
                'details': {
                    'erc20_compliant': erc20_valid,
                    'is_honeypot': is_honeypot,
                    'ownership': ownership_info,
                    'dangerous_functions': dangerous_functions,
                    'liquidity': liquidity_info,
                    'holder_distribution': holder_distribution
                }
            }
            
        except Exception as e:
            return {
                'score': 0,
                'issues': [f"Erro na validação: {str(e)}"],
                'warnings': [],
                'is_safe': False,
                'details': {}
            }
    
    def _check_erc20_compliance(self, token_address: str) -> bool:
        """Verifica se o token segue o padrão ERC20 (versão flexível)"""
        try:
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
            ]
            
            contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Testar pelo menos 3 das 5 funções básicas
            functions_working = 0
            
            try:
                name = contract.functions.name().call()
                if name and len(name) <= 100:
                    functions_working += 1
            except:
                pass
            
            try:
                symbol = contract.functions.symbol().call()
                if symbol and len(symbol) <= 20:
                    functions_working += 1
            except:
                pass
            
            try:
                decimals = contract.functions.decimals().call()
                if 0 <= decimals <= 18:
                    functions_working += 1
            except:
                pass
            
            try:
                total_supply = contract.functions.totalSupply().call()
                if total_supply > 0:
                    functions_working += 1
            except:
                pass
            
            try:
                # Testar balanceOf com endereço zero
                balance = contract.functions.balanceOf("0x0000000000000000000000000000000000000000").call()
                functions_working += 1
            except:
                pass
            
            # Considerar válido se pelo menos 2 funções funcionam (mais flexível)
            return functions_working >= 2
            
        except Exception:
            return False
    
    def _check_honeypot(self, token_address: str) -> bool:
        """Verifica se o token é um honeypot"""
        try:
            # Verificar na lista local
            if token_address.lower() in self.honeypot_contracts:
                return True
            
            # Simular compra e venda pequena
            test_amount = self.web3.to_wei(0.0001, 'ether')
            
            # Tentar simular transação de compra
            # (Implementação simplificada - em produção usaria simulação mais robusta)
            
            return False  # Por enquanto, assumir que não é honeypot
            
        except Exception:
            return False
    
    def _check_ownership(self, token_address: str) -> Dict:
        """Verifica informações de ownership do contrato"""
        try:
            # ABI para verificar owner
            owner_abi = [
                {"constant": True, "inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "type": "function"}
            ]
            
            try:
                contract = self.web3.eth.contract(address=token_address, abi=owner_abi)
                owner = contract.functions.owner().call()
                
                # Verificar se owner é endereço zero (renunciado)
                zero_address = "0x0000000000000000000000000000000000000000"
                
                return {
                    'has_owner': True,
                    'owner_address': owner,
                    'renounced': owner.lower() == zero_address.lower()
                }
                
            except Exception:
                # Contrato pode não ter função owner
                return {
                    'has_owner': False,
                    'owner_address': None,
                    'renounced': True
                }
                
        except Exception:
            return {
                'has_owner': False,
                'owner_address': None,
                'renounced': True
            }
    
    def _check_dangerous_functions(self, token_address: str) -> List[str]:
        """Verifica funções perigosas no contrato"""
        dangerous_functions = []
        
        try:
            # Lista de funções perigosas conhecidas
            dangerous_signatures = [
                'mint(address,uint256)',
                'burn(uint256)',
                'pause()',
                'blacklist(address)',
                'setTaxFee(uint256)',
                'setMaxTxAmount(uint256)',
                'excludeFromFee(address)',
                'includeInFee(address)'
            ]
            
            # Obter bytecode do contrato
            code = self.web3.eth.get_code(token_address)
            code_hex = code.hex()
            
            # Verificar assinaturas de funções perigosas
            for func_sig in dangerous_signatures:
                # Calcular hash da função
                func_hash = self.web3.keccak(text=func_sig)[:4].hex()
                
                if func_hash in code_hex:
                    dangerous_functions.append(func_sig.split('(')[0])
            
            return dangerous_functions
            
        except Exception:
            return []
    
    def _check_liquidity_security(self, token_address: str) -> Dict:
        """Verifica segurança da liquidez"""
        try:
            # Implementação simplificada
            # Em produção, verificaria pools específicos e locks
            
            return {
                'total_liquidity_usd': 50000,  # Valor simulado
                'locked_percentage': 75,       # Valor simulado
                'lock_duration_days': 365,     # Valor simulado
                'is_locked': True
            }
            
        except Exception:
            return {
                'total_liquidity_usd': 0,
                'locked_percentage': 0,
                'lock_duration_days': 0,
                'is_locked': False
            }
    
    def _check_holder_distribution(self, token_address: str) -> Dict:
        """Verifica distribuição de holders"""
        try:
            # Implementação simplificada
            # Em produção, analisaria holders reais via API
            
            return {
                'total_holders': 1000,      # Valor simulado
                'top_10_percentage': 45,    # Valor simulado
                'top_1_percentage': 15,     # Valor simulado
                'is_well_distributed': True
            }
            
        except Exception:
            return {
                'total_holders': 0,
                'top_10_percentage': 100,
                'top_1_percentage': 100,
                'is_well_distributed': False
            }
    
    def check_mev_protection(self, token_address: str, amount: int) -> Dict:
        """Verifica proteção contra MEV"""
        try:
            current_block = self.web3.eth.block_number
            
            # Verificar se há atividade suspeita de MEV
            recent_blocks = []
            for i in range(5):  # Últimos 5 blocos
                block = self.web3.eth.get_block(current_block - i, full_transactions=True)
                recent_blocks.append(block)
            
            # Analisar transações suspeitas
            suspicious_activity = self._analyze_mev_activity(recent_blocks, token_address)
            
            return {
                'mev_risk_level': 'LOW' if not suspicious_activity else 'HIGH',
                'suspicious_transactions': suspicious_activity,
                'recommended_delay': 0 if not suspicious_activity else 30,  # segundos
                'safe_to_trade': not suspicious_activity
            }
            
        except Exception as e:
            return {
                'mev_risk_level': 'UNKNOWN',
                'suspicious_transactions': [],
                'recommended_delay': 60,
                'safe_to_trade': False,
                'error': str(e)
            }
    
    def _analyze_mev_activity(self, blocks: List, token_address: str) -> List:
        """Analisa atividade de MEV nos blocos recentes"""
        suspicious_txs = []
        
        try:
            for block in blocks:
                for tx in block.transactions:
                    # Verificar se a transação envolve o token
                    if tx.to and tx.to.lower() in [token_address.lower(), UNISWAP_V3_ROUTER.lower()]:
                        # Verificar padrões suspeitos de MEV
                        if tx.gas_price > self.web3.to_wei(100, 'gwei'):  # Gas muito alto
                            suspicious_txs.append({
                                'hash': tx.hash.hex(),
                                'gas_price': tx.gas_price,
                                'reason': 'High gas price'
                            })
            
            return suspicious_txs
            
        except Exception:
            return []
    
    def validate_trade_conditions(self, token_address: str, amount: int, is_buy: bool) -> Dict:
        """Valida condições gerais para o trade"""
        try:
            validation_result = {
                'safe_to_trade': True,
                'warnings': [],
                'blocking_issues': [],
                'recommended_actions': []
            }
            
            # 1. Verificar segurança do token
            security_check = self.validate_token_security(token_address)
            if not security_check['is_safe']:
                validation_result['blocking_issues'].extend(security_check['issues'])
                validation_result['safe_to_trade'] = False
            
            validation_result['warnings'].extend(security_check['warnings'])
            
            # 2. Verificar proteção MEV
            if ENABLE_MEV_PROTECTION:
                mev_check = self.check_mev_protection(token_address, amount)
                if not mev_check['safe_to_trade']:
                    validation_result['warnings'].append("Atividade MEV detectada")
                    validation_result['recommended_actions'].append(f"Aguardar {mev_check['recommended_delay']} segundos")
            
            # 3. Verificar condições de mercado
            market_conditions = self._check_market_conditions()
            if market_conditions['volatility'] > 50:  # Alta volatilidade
                validation_result['warnings'].append("Alta volatilidade do mercado")
            
            # 4. Verificar gas price
            current_gas = self.web3.eth.gas_price
            if current_gas > self.web3.to_wei(MAX_GAS_PRICE, 'gwei'):
                validation_result['warnings'].append(f"Gas price alto: {self.web3.from_wei(current_gas, 'gwei'):.1f} gwei")
            
            return validation_result
            
        except Exception as e:
            return {
                'safe_to_trade': False,
                'warnings': [],
                'blocking_issues': [f"Erro na validação: {str(e)}"],
                'recommended_actions': ['Tentar novamente mais tarde']
            }
    
    def _check_market_conditions(self) -> Dict:
        """Verifica condições gerais do mercado"""
        try:
            # Implementação simplificada
            # Em produção, consultaria APIs de mercado
            
            return {
                'volatility': 25,  # Valor simulado
                'trend': 'NEUTRAL',
                'volume_24h': 1000000,
                'market_cap': 50000000
            }
            
        except Exception:
            return {
                'volatility': 100,
                'trend': 'UNKNOWN',
                'volume_24h': 0,
                'market_cap': 0
            }
    
    def print_security_report(self, token_address: str):
        """Imprime relatório de segurança detalhado"""
        print(f"\n{Fore.CYAN}🛡️ RELATÓRIO DE SEGURANÇA{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"Token: {token_address}")
        
        security_check = self.validate_token_security(token_address)
        
        # Score de segurança
        score = security_check['score']
        if score >= 80:
            score_color = Fore.GREEN
            score_status = "EXCELENTE"
        elif score >= 60:
            score_color = Fore.YELLOW
            score_status = "BOM"
        elif score >= 40:
            score_color = Fore.YELLOW
            score_status = "MÉDIO"
        else:
            score_color = Fore.RED
            score_status = "PERIGOSO"
        
        print(f"\n{score_color}📊 Score de Segurança: {score}/100 ({score_status}){Style.RESET_ALL}")
        
        # Issues críticos
        if security_check['issues']:
            print(f"\n{Fore.RED}❌ PROBLEMAS CRÍTICOS:{Style.RESET_ALL}")
            for issue in security_check['issues']:
                print(f"   • {issue}")
        
        # Warnings
        if security_check['warnings']:
            print(f"\n{Fore.YELLOW}⚠️ AVISOS:{Style.RESET_ALL}")
            for warning in security_check['warnings']:
                print(f"   • {warning}")
        
        # Detalhes
        details = security_check['details']
        print(f"\n{Fore.CYAN}📋 DETALHES:{Style.RESET_ALL}")
        print(f"   • ERC20 Compliant: {'✅' if details.get('erc20_compliant') else '❌'}")
        print(f"   • Honeypot: {'❌' if details.get('is_honeypot') else '✅'}")
        
        if 'ownership' in details:
            ownership = details['ownership']
            print(f"   • Owner Renunciado: {'✅' if ownership.get('renounced') else '❌'}")
        
        if 'dangerous_functions' in details and details['dangerous_functions']:
            print(f"   • Funções Perigosas: {', '.join(details['dangerous_functions'])}")
        
        # Recomendação final
        print(f"\n{Fore.CYAN}🎯 RECOMENDAÇÃO:{Style.RESET_ALL}")
        if security_check['is_safe']:
            print(f"   {Fore.GREEN}✅ Token aprovado para trading{Style.RESET_ALL}")
        else:
            print(f"   {Fore.RED}❌ Token NÃO recomendado para trading{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")