import asyncio
import time
import random
from typing import Dict, Optional
from web3 import Web3
from eth_account import Account
from colorama import Fore, Style, init
import logging
from datetime import datetime

from config import *
from dex_handler import DEXHandler
from token_monitor import TokenMonitor
from security_validator import SecurityValidator
from aggressive_strategy import AggressiveStrategy

# Inicializar colorama
init(autoreset=True)

class SniperBot:
    def __init__(self):
        self.web3 = None
        self.dex_handler = None
        self.token_monitor = None
        self.security_validator = None
        self.account = None
        self.running = False
        self.trades_executed = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        
        # Sistema de trading inteligente com crescimento automático
        self.auto_mode = True
        self.current_trade_amount = TRADE_AMOUNT_WETH
        self.dynamic_strategy = True
        self.profit_reinvestment = True
        self.initial_balance = INITIAL_WETH_BALANCE
        self.balance_history = []
        self.profit_history = []
        self.smart_scaling = SMART_SCALING_ENABLED
        self.last_balance_check = 0
        
        # Cache para saldos (evitar rate limit)
        self._weth_balance_cache = 0.0
        self._weth_balance_time = 0
        
        # Estratégia agressiva para crescimento rápido
        self.aggressive_strategy = None
        
        # Configurar logging primeiro
        if ENABLE_LOGGING:
            logging.basicConfig(
                level=getattr(logging, LOG_LEVEL),
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('sniper_bot.log'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logging.getLogger(__name__)
        
        # Inicializar Telegram Bot SIMPLES (sem conflitos)
        try:
            from simple_telegram import simple_telegram
            self.telegram_bot = simple_telegram
            print("📱 Usando Telegram SIMPLES (sem conflitos)")
        except Exception as e:
            self.logger.warning(f"Telegram bot não disponível: {e}")
            # Criar um mock do telegram bot para evitar erros
            self.telegram_bot = self._create_telegram_mock()
    
    def _create_telegram_mock(self):
        """Cria um mock do telegram bot para funcionar sem Telegram"""
        class TelegramMock:
            async def send_notification(self, message, priority="normal"):
                print(f"📱 Notificação [{priority}]: {message}")
            
            async def send_trade_alert(self, token_address, token_name, action, details=None):
                print(f"🚨 Trade Alert [{action}]: {token_name} ({token_address[:10]}...)")
            
            async def start(self):
                print("📱 Telegram Mock: Funcionando sem Telegram")
        
        return TelegramMock()
        
    def initialize(self):
        """Inicializa o bot"""
        try:
            print(f"{Fore.CYAN}🚀 Inicializando Sniper Bot para Base Network...{Style.RESET_ALL}")
            
            # Log de inicialização
            print("🚀 Inicializando Sniper Bot V7...")
            print("🔧 Validando configurações...")
            print("🌐 Conectando à Base Network...")
            
            # Validar configuração
            validate_config()
            
            # Conectar à Base Network
            self.web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
            if not self.web3.is_connected():
                raise Exception("Não foi possível conectar à Base Network")
            
            print(f"{Fore.GREEN}✅ Conectado à Base Network{Style.RESET_ALL}")
            
            # Log de conexão bem-sucedida
            print("✅ Base Network: Conectado")
            print("🔗 RPC: Operacional")
            
            # Configurar conta
            self.account = Account.from_key(PRIVATE_KEY)
            if self.account.address.lower() != WALLET_ADDRESS.lower():
                raise Exception("Private key não corresponde ao endereço da carteira")
            
            print(f"{Fore.GREEN}✅ Carteira configurada: {WALLET_ADDRESS}{Style.RESET_ALL}")
            
            # Log de configuração da carteira
            print(f"💰 Carteira configurada: {WALLET_ADDRESS[:6]}...{WALLET_ADDRESS[-4:]}")
            print("🔐 Chave privada: Validada ✅")
            
            # Inicializar handlers
            self.dex_handler = DEXHandler(self.web3)
            self.token_monitor = TokenMonitor(self.web3, self._process_new_token)
            self.security_validator = SecurityValidator(self.web3)
            
            # Inicializar estratégia agressiva
            self.aggressive_strategy = AggressiveStrategy(self)
            # Reset posições antigas para começar limpo
            self.aggressive_strategy.reset_positions()
            print(f"{Fore.GREEN}🚀 Estratégia agressiva ativada para crescimento rápido{Style.RESET_ALL}")
            
            # Verificar saldo ETH
            balance = self.web3.eth.get_balance(WALLET_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance, 'ether'))
            
            print(f"{Fore.YELLOW}💰 Saldo ETH: {balance_eth:.6f} ETH{Style.RESET_ALL}")
            
            # Verificar saldo WETH (versão síncrona para inicialização)
            weth_balance = self._get_weth_balance_sync()
            print(f"{Fore.YELLOW}💰 Saldo WETH: {weth_balance:.6f} WETH{Style.RESET_ALL}")
            
            # Log de saldos
            print(f"💰 Saldos verificados:")
            print(f"⛽ ETH (Gas): {balance_eth:.6f}")
            print(f"💎 WETH (Trading): {weth_balance:.6f}")
            print(f"📊 Total: {balance_eth + weth_balance:.6f} ETH")
            
            # Calcular saldo total disponível
            total_balance = balance_eth + weth_balance
            print(f"{Fore.CYAN}💰 Saldo total disponível: {total_balance:.6f} ETH{Style.RESET_ALL}")
            
            # Verificar se tem WETH suficiente para trading e ETH para gas
            min_eth_for_gas = 0.000001  # Mínimo ETH para gas (mais flexível)
            
            # Calcular quantos trades são possíveis
            possible_trades = int(weth_balance / TRADE_AMOUNT_WETH) if weth_balance > 0 else 0
            
            if weth_balance >= TRADE_AMOUNT_WETH:
                print(f"{Fore.GREEN}✅ Saldo otimizado para trading!{Style.RESET_ALL}")
                print(f"{Fore.GREEN}   WETH disponível: {weth_balance:.6f}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}   Valor por trade: {TRADE_AMOUNT_WETH:.6f} WETH{Style.RESET_ALL}")
                print(f"{Fore.GREEN}   Trades possíveis: {possible_trades} operações{Style.RESET_ALL}")
                if balance_eth >= min_eth_for_gas:
                    print(f"{Fore.GREEN}   ETH para gas: {balance_eth:.6f} ✅{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}   ETH para gas baixo: {balance_eth:.6f} (pode limitar trades){Style.RESET_ALL}")
                
                # Log bot pronto para operar
                print("🚀 BOT PRONTO PARA OPERAR!")
                print(f"✅ Inicialização completa")
                print(f"💰 Trades possíveis: {possible_trades}")
                print(f"🎯 Valor por trade: {TRADE_AMOUNT_WETH:.6f} WETH")
                print(f"⛽ Gas disponível: {'✅' if balance_eth >= min_eth_for_gas else '⚠️'}")
                print("🔍 Aguardando novos tokens...")
            else:
                print(f"{Fore.YELLOW}⚠️ Saldo baixo mas continuará monitorando!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}   WETH disponível: {weth_balance:.6f}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}   Necessário para 1 trade: {TRADE_AMOUNT_WETH:.6f}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}   💡 Bot aguardará mais saldo ou tokens com menor valor{Style.RESET_ALL}")
                
                # Log saldo baixo
                print("⚠️ BOT INICIADO - SALDO BAIXO")
                print(f"💰 WETH disponível: {weth_balance:.6f}")
                print(f"🎯 Necessário: {TRADE_AMOUNT_WETH:.6f} WETH")
                print("🔍 Monitorando tokens...")
                print("💡 Aguardando saldo suficiente")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na inicialização: {str(e)}{Style.RESET_ALL}")
            return False
    
    def test_connections(self):
        """Testa conexões com todas as DEXs"""
        print(f"{Fore.CYAN}🔍 Testando conexões com DEXs...{Style.RESET_ALL}")
        
        results = self.dex_handler.test_all_dexs()
        
        working_dexs = sum(1 for working in results.values() if working)
        total_dexs = len(results)
        
        print(f"{Fore.YELLOW}📊 Resultado: {working_dexs}/{total_dexs} DEXs funcionando{Style.RESET_ALL}")
        
        if working_dexs == 0:
            print(f"{Fore.RED}❌ Nenhuma DEX está funcionando! Verifique a configuração.{Style.RESET_ALL}")
            return False
        
        return True
    
    async def _process_new_token(self, token_address: str, token_info: Dict, priority: str = "MEDIUM"):
        """Processa novo token detectado com prioridade"""
        try:
            priority_emoji = "🚀" if priority == "HIGH" else "📊"
            print(f"{Fore.MAGENTA}{priority_emoji} Analisando novo token [{priority}]: {token_info['symbol']} ({token_address}){Style.RESET_ALL}")
            
            # Notificar detecção de novo token via sistema de notificações em tempo real
            await self.telegram_bot.send_trade_alert(token_address, token_info.get('symbol', 'UNK'), "DETECTED")
            await self.telegram_bot.send_notification(
                f"🔍 Iniciando análise [{priority}] para {token_info['symbol']}", 
                "high" if priority == "HIGH" else "normal"
            )
            
            # Validação de segurança primeiro
            security_validation = self.security_validator.validate_trade_conditions(
                token_address, self.web3.to_wei(TRADE_AMOUNT_WETH, 'ether'), is_buy=True
            )
            
            if not security_validation['safe_to_trade']:
                print(f"{Fore.RED}🚫 Token rejeitado por questões de segurança:{Style.RESET_ALL}")
                issues_text = "\n".join([f"• {issue}" for issue in security_validation['blocking_issues']])
                await self.telegram_bot.send_notification(
                    f"🚫 **Token rejeitado: {token_info['symbol']}**\n"
                    f"⚠️ **Problemas de segurança:**\n{issues_text}", 
                    "high"
                )
                for issue in security_validation['blocking_issues']:
                    print(f"   • {issue}")
                return
            
            # Mostrar warnings se houver
            if security_validation['warnings']:
                print(f"{Fore.YELLOW}⚠️ Avisos de segurança:{Style.RESET_ALL}")
                warnings_text = "\n".join([f"• {warning}" for warning in security_validation['warnings']])
                await self.telegram_bot.send_notification(
                    f"⚠️ **Avisos para {token_info['symbol']}:**\n{warnings_text}", 
                    "normal"
                )
                for warning in security_validation['warnings']:
                    print(f"   • {warning}")
            
            # Análise IA do token
            ai_analysis = await self.analyze_token_with_ai(token_address, token_info)
            
            # Análise tradicional como backup
            traditional_analysis = self.token_monitor.analyze_token_potential(token_address)
            
            # Combinar análises (IA tem peso maior)
            combined_score = int(ai_analysis['score'] * 0.7 + traditional_analysis['score'] * 0.3)
            
            # Boost para tokens com prioridade HIGH (pares com WETH)
            if priority == "HIGH":
                combined_score = min(100, combined_score + 15)  # +15 pontos para pares WETH
                print(f"{Fore.GREEN}🚀 Boost de prioridade HIGH: +15 pontos{Style.RESET_ALL}")
            
            final_recommendation = ai_analysis['recommendation']
            
            print(f"{Fore.CYAN}🧠 Score IA: {ai_analysis['score']}/100 (confiança: {ai_analysis['confidence']}%){Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Score tradicional: {traditional_analysis['score']}/100{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🎯 Score final: {combined_score}/100{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📈 Recomendação: {final_recommendation}{Style.RESET_ALL}")
            
            # Notificar resultado da análise
            factors_text = "\n".join([f"• {k}: {v} pts" for k, v in ai_analysis.get('factors', {}).items()])
            await self.telegram_bot.send_notification(
                f"🧠 **Análise IA: {token_info['symbol']}**\n"
                f"🎯 **Score IA:** {ai_analysis['score']}/100\n"
                f"📊 **Score Final:** {combined_score}/100\n"
                f"📈 **Recomendação:** {final_recommendation}\n"
                f"🔍 **Fatores:**\n{factors_text}\n"
                f"💡 **Decisão:** {'✅ Comprando' if final_recommendation in ['STRONG_BUY', 'BUY'] and combined_score >= 50 else '❌ Ignorando'}", 
                "high"
            )
            
            # Usar estratégia agressiva para decidir compra
            if self.aggressive_strategy:
                should_buy, reason = self.aggressive_strategy.should_buy_token(
                    token_address, token_info, ai_analysis['score'], traditional_analysis['score']
                )
                
                if should_buy:
                    print(f"{Fore.GREEN}🚀 ESTRATÉGIA AGRESSIVA: Comprando {token_info['symbol']}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}   Razão: {reason}{Style.RESET_ALL}")
                    
                    # Executar estratégia de compra
                    if await self.aggressive_strategy.execute_buy_strategy(token_address, token_info):
                        await self._execute_buy_order(token_address, token_info)
                    else:
                        print(f"{Fore.RED}❌ Falha na estratégia de compra{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⏭️ ESTRATÉGIA AGRESSIVA: Token ignorado{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}   Razão: {reason}{Style.RESET_ALL}")
                    await self.telegram_bot.send_notification(
                        f"⏭️ **Token ignorado: {token_info['symbol']}**\n"
                        f"🧠 Estratégia: {reason}\n"
                        f"💡 Aguardando melhores oportunidades", 
                        "low"
                    )
            else:
                # Fallback para lógica original se estratégia não estiver disponível
                from config import MIN_SCORE_TO_BUY, MEMECOIN_MODE
                
                min_score = 40 if MEMECOIN_MODE else MIN_SCORE_TO_BUY
                
                if final_recommendation in ['STRONG_BUY', 'BUY'] and combined_score >= min_score:
                    await self._execute_buy_order(token_address, token_info)
                elif final_recommendation == 'WEAK_BUY' and combined_score >= 30 and MEMECOIN_MODE:
                    print(f"{Fore.YELLOW}🎲 Comprando token de risco moderado (memecoin mode){Style.RESET_ALL}")
                    await self._execute_buy_order(token_address, token_info)
                else:
                    print(f"{Fore.YELLOW}⏭️ Token ignorado - Score: {combined_score}, Mínimo: {min_score}{Style.RESET_ALL}")
                    await self.telegram_bot.send_notification(
                        f"⏭️ **Token ignorado: {token_info['symbol']}**\n"
                        f"📊 Score: {combined_score}/{min_score} (mínimo)\n"
                        f"🧠 IA: {final_recommendation}\n"
                        f"💡 Aguardando tokens com melhor potencial", 
                        "low"
                    )
                
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao processar novo token: {str(e)}{Style.RESET_ALL}")
            await self.telegram_bot.send_notification(
                f"❌ **Erro na análise**\n"
                f"🔗 Token: {token_address[:10]}...{token_address[-10:]}\n"
                f"⚠️ Erro: {str(e)}", 
                "high"
            )
    
    async def _execute_buy_order(self, token_address: str, token_info: Dict):
        """Executa ordem de compra"""
        try:
            print(f"{Fore.GREEN}💰 Executando compra de {token_info['symbol']}...{Style.RESET_ALL}")
            
            # Usar valor dinâmico da estratégia agressiva
            if self.aggressive_strategy:
                trade_amount = self.aggressive_strategy.calculate_dynamic_trade_amount()
            else:
                trade_amount = self.current_trade_amount
            
            # Notificar início da compra
            await self.telegram_bot.send_notification(
                f"💰 **Iniciando compra!**\n"
                f"📛 **{token_info['symbol']}**\n"
                f"💎 Valor: {trade_amount:.6f} WETH\n"
                f"🧠 Estratégia: {'Dinâmica' if self.dynamic_strategy else 'Fixa'}\n"
                f"🔍 Verificando saldos...", 
                "high"
            )
            
            # Verificar saldo antes de executar
            balance = self.web3.eth.get_balance(WALLET_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance, 'ether'))
            weth_balance = await self._get_weth_balance()
            
            # Log detalhado dos saldos
            print(f"{Fore.CYAN}💰 Verificação de saldos:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   ETH (gas): {balance_eth:.6f} ETH{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   WETH (trading): {weth_balance:.6f} WETH{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Trade amount: {trade_amount:.6f} WETH{Style.RESET_ALL}")
            
            # Verificar modo de emergência
            emergency_mode = balance_eth < EMERGENCY_MODE_THRESHOLD
            min_eth_for_gas = 0.000001  # Mínimo ultra baixo após conversão automática
            
            if emergency_mode:
                print(f"{Fore.YELLOW}🚨 MODO EMERGÊNCIA ATIVADO - ETH baixo: {balance_eth:.6f}{Style.RESET_ALL}")
                trade_amount = min(trade_amount, EMERGENCY_TRADE_AMOUNT)
                await self.telegram_bot.send_notification(
                    f"🚨 **MODO EMERGÊNCIA**\n"
                    f"⚠️ ETH baixo: {balance_eth:.6f}\n"
                    f"💰 Trade reduzido: {trade_amount:.6f} WETH\n"
                    f"🔧 Tentando conversão WETH->ETH...", 
                    "high"
                )
                
                # FORÇAR conversão WETH->ETH quando em modo emergência
                print(f"{Fore.CYAN}🔄 Forçando conversão WETH->ETH para modo emergência...{Style.RESET_ALL}")
                conversion_success = await self.dex_handler.convert_weth_to_eth_if_needed(0.00005)  # Forçar conversão
                
                if conversion_success:
                    # Atualizar saldo ETH após conversão
                    balance_eth = self.web3.from_wei(self.web3.eth.get_balance(WALLET_ADDRESS), 'ether')
                    print(f"{Fore.GREEN}✅ Conversão realizada! Novo saldo ETH: {balance_eth:.6f}{Style.RESET_ALL}")
                    await self.telegram_bot.send_notification(
                        f"✅ **Conversão WETH->ETH realizada!**\n"
                        f"💰 Novo saldo ETH: {balance_eth:.6f}\n"
                        f"🚀 Continuando com o trade...", 
                        "medium"
                    )
                else:
                    print(f"{Fore.YELLOW}⚠️ Conversão WETH->ETH não realizada - continuando com saldo atual{Style.RESET_ALL}")
            
            # Se o saldo total é muito baixo, usar estratégia de micro-trades
            total_balance = balance_eth + weth_balance
            if total_balance < 0.001:  # Menos de 0.001 ETH total
                print(f"{Fore.YELLOW}💡 Saldo baixo detectado - usando micro-trades{Style.RESET_ALL}")
                # Usar apenas 10% do WETH disponível para preservar gas
                trade_amount = min(trade_amount, weth_balance * 0.1)
                print(f"{Fore.YELLOW}   Ajustando trade para: {trade_amount:.6f} WETH{Style.RESET_ALL}")
            
            # Verificar se ainda tem saldo suficiente
            if weth_balance < trade_amount:
                # Tentar usar o máximo disponível se for pelo menos 50% do planejado
                if weth_balance >= trade_amount * 0.5:
                    trade_amount = weth_balance * 0.9  # Usar 90% do disponível
                    print(f"{Fore.YELLOW}💡 Ajustando trade para saldo disponível: {trade_amount:.6f} WETH{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⚠️ WETH insuficiente para trade!{Style.RESET_ALL}")
                    await self.telegram_bot.send_notification(
                        f"⚠️ **Compra cancelada: {token_info['symbol']}**\n"
                        f"💰 WETH insuficiente\n"
                        f"📊 Disponível: {weth_balance:.6f} WETH\n"
                        f"📊 Necessário: {trade_amount:.6f} WETH", 
                        "high"
                    )
                    return
            
            # Verificar gas - se muito baixo, cancelar para preservar fundos
            if balance_eth < min_eth_for_gas:
                print(f"{Fore.RED}❌ ETH insuficiente para gas!{Style.RESET_ALL}")
                print(f"{Fore.RED}   ETH disponível: {balance_eth:.6f}{Style.RESET_ALL}")
                print(f"{Fore.RED}   ETH mínimo necessário: {min_eth_for_gas:.6f}{Style.RESET_ALL}")
                
                await self.telegram_bot.send_notification(
                    f"❌ **Compra cancelada: {token_info['symbol']}**\n"
                    f"⛽ ETH insuficiente para gas\n"
                    f"📊 Disponível: {balance_eth:.6f} ETH\n"
                    f"📊 Necessário: {min_eth_for_gas:.6f} ETH\n"
                    f"💡 Adicione mais ETH para continuar trading", 
                    "high"
                )
                return
            
            # Calcular quantidade a comprar
            amount_in = self.web3.to_wei(trade_amount, 'ether')
            
            # Notificar busca por melhor preço
            await self.telegram_bot.send_notification(
                f"🔍 **Buscando melhor preço...**\n"
                f"📛 {token_info['symbol']}\n"
                f"🌐 Consultando 4 DEXs...", 
                "normal"
            )
            
            # Encontrar melhor preço
            best_dex, best_price, best_router = await self.dex_handler.get_best_price(
                token_address, amount_in, is_buy=True
            )
            
            if not best_dex or best_price == 0:
                print(f"{Fore.YELLOW}⚠️ Preço não confirmado - executando compra agressiva{Style.RESET_ALL}")
                # Não cancelar mais - modo agressivo sempre tenta
                if not best_dex:
                    best_dex = "uniswap_v3"
                    best_router = self.dex_handler.dexs['uniswap_v3']['router']
            
            print(f"{Fore.CYAN}🎯 Melhor preço encontrado na {best_dex}{Style.RESET_ALL}")
            
            # Notificar execução
            await self.telegram_bot.send_notification(
                f"🎯 **Executando compra!**\n"
                f"📛 {token_info['symbol']}\n"
                f"🏪 DEX: {best_dex}\n"
                f"⚡ Enviando transação...", 
                "high"
            )
            
            # Executar swap
            tx_hash = await self.dex_handler.execute_swap(
                token_address, amount_in, best_router, is_buy=True
            )
            
            if tx_hash:
                self.trades_executed += 1
                print(f"{Fore.GREEN}✅ Compra executada! TX: {tx_hash}{Style.RESET_ALL}")
                
                # Notificar via sistema em tempo real
                await self.telegram_bot.send_trade_alert("BUY", token_address, trade_amount, best_price)
                await self.telegram_bot.send_notification(
                    f"TX Hash: {tx_hash[:10]}...{tx_hash[-10:]}", 
                    "success"
                )
                
                # Agendar venda
                asyncio.create_task(self._schedule_sell_order(token_address, token_info, tx_hash))
                
                # Log da transação
                if ENABLE_LOGGING:
                    self.logger.info(f"BUY - {token_info['symbol']} - Amount: {trade_amount} ETH - TX: {tx_hash}")
            else:
                print(f"{Fore.RED}❌ Falha na execução da compra{Style.RESET_ALL}")
                await self.telegram_bot.send_notification(
                    f"❌ Falha na compra de {token_info['symbol']} - Verifique gas e liquidez", 
                    "high"
                )
                
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na execução da compra: {str(e)}{Style.RESET_ALL}")
            await self.telegram_bot.send_notification(
                f"❌ Erro crítico na compra de {token_info['symbol']}: {str(e)}", 
                "high"
            )
    
    async def _schedule_sell_order(self, token_address: str, token_info: Dict, buy_tx_hash: str):
        """Agenda ordem de venda"""
        try:
            # Aguardar confirmação da compra
            print(f"{Fore.YELLOW}⏳ Aguardando confirmação da compra...{Style.RESET_ALL}")
            
            await self.telegram_bot.send_notification(
                f"⏳ **Aguardando confirmação...**\n"
                f"📛 {token_info['symbol']}\n"
                f"🔗 TX: `{buy_tx_hash[:10]}...{buy_tx_hash[-10:]}`\n"
                f"⏰ Aguardando 30 segundos...", 
                "normal"
            )
            
            # Aguardar alguns blocos
            await asyncio.sleep(30)  # 30 segundos
            
            # Verificar se a compra foi bem-sucedida
            buy_receipt = self.web3.eth.get_transaction_receipt(buy_tx_hash)
            if buy_receipt.status != 1:
                print(f"{Fore.RED}❌ Compra falhou, cancelando venda{Style.RESET_ALL}")
                await self.telegram_bot.send_notification(
                    f"❌ **Compra falhou!**\n"
                    f"📛 {token_info['symbol']}\n"
                    f"🚫 Transação revertida\n"
                    f"💡 Venda cancelada", 
                    "high"
                )
                return
            
            await self.telegram_bot.send_notification(
                f"✅ **Compra confirmada!**\n"
                f"📛 {token_info['symbol']}\n"
                f"🎯 Verificando saldo do token...", 
                "normal"
            )
            
            # Obter saldo do token
            token_balance_wei = await self._get_token_balance_wei(token_address)
            token_balance = await self._get_token_balance(token_address)  # Em formato decimal
            if token_balance == 0:
                print(f"{Fore.RED}❌ Saldo do token é zero, cancelando venda{Style.RESET_ALL}")
                await self.telegram_bot.send_notification(
                    f"❌ **Erro no saldo!**\n"
                    f"📛 {token_info['symbol']}\n"
                    f"💰 Saldo: 0 tokens\n"
                    f"🚫 Venda cancelada", 
                    "high"
                )
                return
            
            print(f"{Fore.GREEN}💰 Executando venda de {token_info['symbol']}...{Style.RESET_ALL}")
            
            await self.telegram_bot.send_notification(
                f"💸 **Iniciando venda!**\n"
                f"📛 {token_info['symbol']}\n"
                f"💰 Saldo: {token_balance:.6f} tokens\n"
                f"🔍 Buscando melhor preço...", 
                "high"
            )
            
            # Encontrar melhor preço para venda (usar saldo em wei)
            best_dex, best_price, best_router = await self.dex_handler.get_best_price(
                token_address, token_balance_wei, is_buy=False
            )
            
            if not best_dex:
                print(f"{Fore.YELLOW}⚠️ Preço não confirmado - executando venda agressiva{Style.RESET_ALL}")
                # Não cancelar mais - modo agressivo sempre tenta
                best_dex = "uniswap_v3"
                best_router = self.dex_handler.dexs['uniswap_v3']['router']
            
            await self.telegram_bot.send_notification(
                f"🎯 **Executando venda!**\n"
                f"📛 {token_info['symbol']}\n"
                f"🏪 DEX: {best_dex}\n"
                f"💰 Saldo: {token_balance:.6f} tokens\n"
                f"⚡ Enviando transação...", 
                "high"
            )
            
            # Executar venda (usar saldo em wei)
            sell_tx_hash = await self.dex_handler.execute_swap(
                token_address, token_balance_wei, best_router, is_buy=False
            )
            
            if sell_tx_hash:
                self.successful_trades += 1
                print(f"{Fore.GREEN}✅ Venda executada! TX: {sell_tx_hash}{Style.RESET_ALL}")
                
                # Notificar venda via Telegram
                await self.telegram_bot.send_trade_notification(
                    token_info['symbol'], "SELL", sell_tx_hash, token_balance, best_price
                )
                
                # Calcular lucro
                await self._calculate_profit(buy_tx_hash, sell_tx_hash)
                
                # Log da transação
                if ENABLE_LOGGING:
                    self.logger.info(f"SELL - {token_info['symbol']} - TX: {sell_tx_hash}")
            else:
                print(f"{Fore.RED}❌ Falha na execução da venda{Style.RESET_ALL}")
                await self.telegram_bot.send_notification(
                    f"❌ **Falha na venda!**\n"
                    f"📛 {token_info['symbol']}\n"
                    f"🚫 Transação não foi executada\n"
                    f"💡 Tokens ainda na carteira", 
                    "high"
                )
                
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na execução da venda: {str(e)}{Style.RESET_ALL}")
            await self.telegram_bot.send_notification(
                f"❌ **Erro crítico na venda**\n"
                f"📛 {token_info['symbol']}\n"
                f"⚠️ Erro: {str(e)}", 
                "high"
            )
    
    async def _get_token_balance_wei(self, token_address: str) -> int:
        """Obtém saldo do token em wei (para uso interno)"""
        try:
            erc20_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
                 "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
            ]
            
            contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            balance = contract.functions.balanceOf(WALLET_ADDRESS).call()
            return balance
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao obter saldo do token: {str(e)}{Style.RESET_ALL}")
            return 0
    
    async def _calculate_profit(self, buy_tx_hash: str, sell_tx_hash: str):
        """Calcula lucro da operação"""
        try:
            buy_receipt = self.web3.eth.get_transaction_receipt(buy_tx_hash)
            sell_receipt = self.web3.eth.get_transaction_receipt(sell_tx_hash)
            
            buy_tx = self.web3.eth.get_transaction(buy_tx_hash)
            sell_tx = self.web3.eth.get_transaction(sell_tx_hash)
            
            # Calcular custos de gas
            buy_gas_cost = buy_receipt.gasUsed * buy_tx.gasPrice
            sell_gas_cost = sell_receipt.gasUsed * sell_tx.gasPrice
            total_gas_cost = self.web3.from_wei(buy_gas_cost + sell_gas_cost, 'ether')
            
            # Calcular lucro bruto (simplificado)
            # Nota: Em implementação real, seria necessário analisar os logs dos eventos
            gross_profit = 0.0  # Placeholder
            net_profit = gross_profit - total_gas_cost
            
            self.total_profit += net_profit
            
            print(f"{Fore.CYAN}💹 Lucro líquido: {net_profit:.6f} ETH{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💰 Lucro total acumulado: {self.total_profit:.6f} ETH{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao calcular lucro: {str(e)}{Style.RESET_ALL}")
    
    def print_status(self):
        """Imprime status do bot"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"📊 STATUS DO SNIPER BOT")
        print(f"{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔄 Status: {'Rodando' if self.running else 'Parado'}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📈 Trades executados: {self.trades_executed}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}✅ Trades bem-sucedidos: {self.successful_trades}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💰 Lucro total: {self.total_profit:.6f} ETH{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚙️ Valor por trade: {TRADE_AMOUNT_WETH} ETH{Style.RESET_ALL}")
        
        if self.web3:
            # Mostrar saldo ETH (para gas)
            balance = self.web3.eth.get_balance(WALLET_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance, 'ether'))
            
            # Mostrar saldo WETH (para trading)
            weth_balance = self._get_weth_balance_sync()
            
            print(f"{Fore.YELLOW}💳 Saldo ETH (gas): {balance_eth:.6f} ETH{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💰 Saldo WETH (trading): {weth_balance:.6f} WETH{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📊 Total estimado: {balance_eth + weth_balance:.6f} ETH{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
    
    def _get_weth_balance_sync(self) -> float:
        """Obtém saldo WETH da carteira com cache e retry"""
        # Cache por 30 segundos para evitar rate limit
        current_time = time.time()
        if hasattr(self, '_weth_balance_cache') and hasattr(self, '_weth_balance_time'):
            if current_time - self._weth_balance_time < 30:
                cached_balance = self._weth_balance_cache
                # Diagnóstico: se cache for 0, forçar atualização
                if cached_balance == 0.0:
                    print(f"{Fore.YELLOW}⚠️ Cache WETH zerado detectado - forçando atualização...{Style.RESET_ALL}")
                else:
                    return cached_balance
        
        for attempt in range(3):
            try:
                weth_abi = [
                    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
                     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                    {"constant": True, "inputs": [], "name": "decimals", 
                     "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
                ]
                
                weth_contract = self.web3.eth.contract(address=WETH_ADDRESS, abi=weth_abi)
                balance = weth_contract.functions.balanceOf(WALLET_ADDRESS).call()
                decimals = weth_contract.functions.decimals().call()
                
                result = balance / (10 ** decimals)
                
                # Log detalhado para diagnóstico
                print(f"{Fore.GREEN}✅ Saldo WETH lido: {result:.6f} WETH (raw: {balance}, decimals: {decimals}){Style.RESET_ALL}")
                
                # Cache o resultado
                self._weth_balance_cache = result
                self._weth_balance_time = current_time
                
                # Diagnóstico adicional
                if result == 0.0:
                    print(f"{Fore.RED}⚠️ ATENÇÃO: Saldo WETH é 0.0 - verificar configuração da carteira{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}📍 Carteira: {WALLET_ADDRESS}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}📍 WETH Contract: {WETH_ADDRESS}{Style.RESET_ALL}")
                
                return result
                
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"{Fore.YELLOW}⚠️ Rate limit - tentativa {attempt + 1}/3{Style.RESET_ALL}")
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                else:
                    print(f"{Fore.RED}❌ Erro ao obter saldo WETH: {str(e)}{Style.RESET_ALL}")
                    break
        
        # Se falhou, retorna último valor em cache ou valor padrão
        if hasattr(self, '_weth_balance_cache'):
            print(f"{Fore.YELLOW}⚠️ Usando saldo em cache: {self._weth_balance_cache:.6f} WETH{Style.RESET_ALL}")
            return self._weth_balance_cache
        
        return 0.0
    
    async def _get_weth_balance(self) -> float:
        """Obtém saldo WETH da carteira (versão assíncrona)"""
        return self._get_weth_balance_sync()
    
    async def _get_token_balance(self, token_address: str) -> float:
        """Obtém saldo de um token específico"""
        try:
            erc20_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
                 "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", 
                 "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
            
            token_contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            balance = token_contract.functions.balanceOf(WALLET_ADDRESS).call()
            decimals = token_contract.functions.decimals().call()
            
            return balance / (10 ** decimals)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao obter saldo do token: {str(e)}{Style.RESET_ALL}")
            return 0.0
    
    # ==================== SISTEMA DE TRADING INTELIGENTE ====================
    
    async def update_trading_strategy(self):
        """Atualiza estratégia de trading baseada no saldo atual e performance"""
        try:
            if not self.smart_scaling:
                return
            
            current_weth_balance = await self._get_weth_balance()
            current_time = time.time()
            
            # Atualizar histórico de saldo
            self.balance_history.append({
                'timestamp': current_time,
                'balance': current_weth_balance
            })
            
            # Manter apenas últimas 100 entradas
            if len(self.balance_history) > 100:
                self.balance_history = self.balance_history[-100:]
            
            # Calcular crescimento do saldo
            growth_factor = current_weth_balance / self.initial_balance if self.initial_balance > 0 else 1
            
            # Sistema de escalonamento inteligente
            if growth_factor >= 1.5:  # Saldo cresceu 50%
                # Aumentar valor por trade proporcionalmente
                base_percentage = MAX_TRADE_PERCENTAGE / 100
                growth_bonus = min((growth_factor - 1) * 0.1, 0.15)  # Máximo 15% de bônus
                new_percentage = base_percentage + growth_bonus
                
                new_trade_amount = min(
                    current_weth_balance * new_percentage,
                    current_weth_balance * 0.35  # Máximo 35% do saldo
                )
                
                # Garantir valor mínimo
                new_trade_amount = max(new_trade_amount, MIN_TRADE_AMOUNT)
                
                if abs(new_trade_amount - self.current_trade_amount) > 0.000050:  # Mudança significativa
                    self.current_trade_amount = new_trade_amount
                    
                    await self.telegram_bot.send_notification(
                        f"🧠 **ESTRATÉGIA INTELIGENTE ATIVADA!**\n\n"
                        f"📈 **Crescimento:** {(growth_factor-1)*100:.1f}%\n"
                        f"💰 **Saldo atual:** {current_weth_balance:.6f} WETH\n"
                        f"🎯 **Novo valor/trade:** {new_trade_amount:.6f} WETH\n"
                        f"⚡ **Percentual:** {(new_trade_amount/current_weth_balance)*100:.1f}%\n\n"
                        f"🚀 **Maximizando retornos com crescimento!**", 
                        "high"
                    )
                    
                    print(f"{Fore.GREEN}🧠 Estratégia inteligente: {new_trade_amount:.6f} WETH por trade ({(new_trade_amount/current_weth_balance)*100:.1f}% do saldo){Style.RESET_ALL}")
            
            elif current_weth_balance < self.initial_balance * 0.8:  # Saldo caiu 20%
                # Reduzir valor por trade para preservar capital
                conservative_amount = max(
                    current_weth_balance * 0.15,  # 15% do saldo atual
                    MIN_TRADE_AMOUNT
                )
                
                if conservative_amount < self.current_trade_amount:
                    self.current_trade_amount = conservative_amount
                    
                    await self.telegram_bot.send_notification(
                        f"🛡️ **MODO CONSERVADOR ATIVADO**\n\n"
                        f"📉 **Saldo atual:** {current_weth_balance:.6f} WETH\n"
                        f"🎯 **Valor reduzido:** {conservative_amount:.6f} WETH\n"
                        f"💡 **Preservando capital para recuperação**", 
                        "normal"
                    )
                    
                    print(f"{Fore.YELLOW}🛡️ Modo conservador: {conservative_amount:.6f} WETH por trade{Style.RESET_ALL}")
            
            # Atualizar timestamp da última verificação
            self.last_balance_check = current_time
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao atualizar estratégia: {str(e)}{Style.RESET_ALL}")
    
    async def calculate_optimal_trade_size(self, token_score: int, market_conditions: str = "normal") -> float:
        """Calcula tamanho ótimo do trade baseado no score do token e condições de mercado"""
        try:
            base_amount = self.current_trade_amount
            
            # Ajuste baseado no score do token
            if token_score >= 80:
                size_multiplier = 1.3  # 30% maior para tokens excelentes
            elif token_score >= 60:
                size_multiplier = 1.1  # 10% maior para tokens bons
            elif token_score >= 40:
                size_multiplier = 1.0  # Tamanho normal
            else:
                size_multiplier = 0.7  # 30% menor para tokens arriscados
            
            # Ajuste baseado nas condições de mercado
            market_multipliers = {
                "bullish": 1.2,
                "normal": 1.0,
                "bearish": 0.8,
                "volatile": 0.9
            }
            
            market_multiplier = market_multipliers.get(market_conditions, 1.0)
            
            # Calcular tamanho final
            optimal_size = base_amount * size_multiplier * market_multiplier
            
            # Aplicar limites de segurança
            current_balance = await self._get_weth_balance()
            max_allowed = current_balance * (MAX_TRADE_PERCENTAGE / 100)
            min_allowed = MIN_TRADE_AMOUNT
            
            optimal_size = max(min_allowed, min(optimal_size, max_allowed))
            
            return optimal_size
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao calcular tamanho ótimo: {str(e)}{Style.RESET_ALL}")
            return self.current_trade_amount
    
    async def analyze_token_with_ai(self, token_address: str, token_info: Dict) -> Dict:
        """Análise IA avançada do token para decisões inteligentes"""
        try:
            analysis = {
                'score': 0,
                'confidence': 0,
                'recommendation': 'HOLD',
                'factors': {}
            }
            
            # Análise de liquidez (peso: 25%)
            liquidity_score = await self._analyze_liquidity_advanced(token_address)
            analysis['factors']['liquidez'] = liquidity_score
            analysis['score'] += liquidity_score * 0.25
            
            # Análise de volume (peso: 20%)
            volume_score = await self._analyze_volume_advanced(token_address)
            analysis['factors']['volume'] = volume_score
            analysis['score'] += volume_score * 0.20
            
            # Análise de holders (peso: 15%)
            holders_score = await self._analyze_holders_advanced(token_address)
            analysis['factors']['holders'] = holders_score
            analysis['score'] += holders_score * 0.15
            
            # Análise de contrato (peso: 20%)
            contract_score = await self._analyze_contract_advanced(token_address)
            analysis['factors']['contrato'] = contract_score
            analysis['score'] += contract_score * 0.20
            
            # Análise de timing (peso: 10%)
            timing_score = await self._analyze_timing_advanced(token_address, token_info)
            analysis['factors']['timing'] = timing_score
            analysis['score'] += timing_score * 0.10
            
            # Análise de tendência (peso: 10%)
            trend_score = await self._analyze_trend_advanced(token_address)
            analysis['factors']['tendencia'] = trend_score
            analysis['score'] += trend_score * 0.10
            
            # Calcular confiança baseada na consistência dos fatores
            factor_values = list(analysis['factors'].values())
            if factor_values:
                avg_score = sum(factor_values) / len(factor_values)
                variance = sum((x - avg_score) ** 2 for x in factor_values) / len(factor_values)
                analysis['confidence'] = max(50, min(95, 100 - variance))
            
            # Determinar recomendação baseada no score e confiança
            final_score = int(analysis['score'])
            confidence = analysis['confidence']
            
            if final_score >= 75 and confidence >= 70:
                analysis['recommendation'] = 'STRONG_BUY'
            elif final_score >= 60 and confidence >= 60:
                analysis['recommendation'] = 'BUY'
            elif final_score >= 45 and confidence >= 50:
                analysis['recommendation'] = 'WEAK_BUY'
            elif final_score >= 30:
                analysis['recommendation'] = 'HOLD'
            else:
                analysis['recommendation'] = 'AVOID'
            
            analysis['score'] = final_score
            
            return analysis
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na análise IA: {str(e)}{Style.RESET_ALL}")
            return {
                'score': 30,
                'confidence': 40,
                'recommendation': 'HOLD',
                'factors': {'erro': 0}
            }
    
    async def _analyze_liquidity_advanced(self, token_address: str) -> int:
        """Análise avançada de liquidez"""
        try:
            # Verificar liquidez em múltiplas DEXs
            liquidity_info = self.dex_handler.check_liquidity(token_address)
            
            total_liquidity = sum(
                info.get('liquidity_usd', 0) 
                for info in liquidity_info.values() 
                if isinstance(info, dict)
            )
            
            # Score baseado na liquidez total
            if total_liquidity >= 100000:
                return 90
            elif total_liquidity >= 50000:
                return 75
            elif total_liquidity >= 20000:
                return 60
            elif total_liquidity >= 5000:
                return 45
            elif total_liquidity >= 1000:
                return 30
            else:
                return 15
                
        except Exception:
            return 40  # Score neutro em caso de erro
    
    async def _analyze_volume_advanced(self, token_address: str) -> int:
        """Análise avançada de volume"""
        try:
            # Simular análise de volume (implementar com dados reais)
            import random
            base_score = random.randint(40, 85)
            
            # Ajustar baseado em padrões de volume
            if MEMECOIN_MODE:
                base_score += 10  # Memecoins tendem a ter volume alto
            
            return min(95, base_score)
            
        except Exception:
            return 50
    
    async def _analyze_holders_advanced(self, token_address: str) -> int:
        """Análise avançada de holders"""
        try:
            # Simular análise de distribuição de holders
            import random
            return random.randint(45, 80)
            
        except Exception:
            return 55
    
    async def _analyze_contract_advanced(self, token_address: str) -> int:
        """Análise avançada do contrato"""
        try:
            # Verificações básicas de segurança
            code = self.web3.eth.get_code(token_address)
            
            score = 50
            
            # Contrato tem código suficiente
            if len(code) > 1000:
                score += 20
            
            # Verificar se não é um proxy malicioso (verificação básica)
            if len(code) < 10000:  # Contratos muito grandes podem ser suspeitos
                score += 15
            
            # Adicionar verificações de honeypot se habilitado
            if ENABLE_HONEYPOT_CHECK:
                # Simular verificação de honeypot
                import random
                if random.random() > 0.1:  # 90% chance de não ser honeypot
                    score += 15
                else:
                    score -= 30  # Penalidade por possível honeypot
            
            return max(10, min(95, score))
            
        except Exception:
            return 45
    
    async def _analyze_timing_advanced(self, token_address: str, token_info: Dict) -> int:
        """Análise avançada de timing"""
        try:
            # Verificar idade do token
            token_age = time.time() - token_info.get('created_at', time.time())
            age_hours = token_age / 3600
            
            # Score baseado na idade
            if age_hours < 1:  # Muito novo
                return 85 if AGGRESSIVE_TRADING else 60
            elif age_hours < 6:  # Novo
                return 75
            elif age_hours < 24:  # Recente
                return 65
            elif age_hours < 72:  # Alguns dias
                return 50
            else:  # Mais antigo
                return 35
                
        except Exception:
            return 50
    
    async def _analyze_trend_advanced(self, token_address: str) -> int:
        """Análise avançada de tendência"""
        try:
            # Simular análise de tendência de preço
            import random
            
            # Base score
            trend_score = random.randint(40, 75)
            
            # Ajustar para modo agressivo
            if AGGRESSIVE_TRADING:
                trend_score += 10
            
            # Ajustar para memecoins
            if MEMECOIN_MODE:
                trend_score += 5
            
            return min(90, trend_score)
            
        except Exception:
            return 50
    
    def toggle_auto_mode(self):
        """Alterna modo automático"""
        self.auto_mode = not self.auto_mode
        return self.auto_mode
    
    def set_trade_amount(self, amount: float):
        """Define valor por trade"""
        self.current_trade_amount = amount
        return True
    
    def get_trading_stats(self) -> Dict:
        """Retorna estatísticas de trading"""
        return {
            'auto_mode': self.auto_mode,
            'current_trade_amount': self.current_trade_amount,
            'trades_executed': self.trades_executed,
            'successful_trades': self.successful_trades,
            'total_profit': self.total_profit,
            'success_rate': (self.successful_trades / max(self.trades_executed, 1)) * 100,
            'dynamic_strategy': self.dynamic_strategy,
            'profit_reinvestment': self.profit_reinvestment
        }
    
    async def analyze_token_with_ai(self, token_address: str, token_info: Dict) -> Dict:
        """Análise inteligente de token usando múltiplos fatores"""
        try:
            analysis = {
                'score': 0,
                'factors': {},
                'recommendation': 'HOLD',
                'confidence': 0
            }
            
            # Fator 1: Idade do token (memecoins novos são mais voláteis)
            age_minutes = token_info.get('age_minutes', 0)
            if 1 <= age_minutes <= 60:  # 1-60 minutos = ideal para memecoins
                analysis['factors']['age'] = 25
                analysis['score'] += 25
            elif age_minutes <= 180:  # Até 3 horas ainda é bom
                analysis['factors']['age'] = 15
                analysis['score'] += 15
            else:
                analysis['factors']['age'] = 5
                analysis['score'] += 5
            
            # Fator 2: Liquidez (baixa liquidez = mais potencial de pump)
            liquidity = token_info.get('liquidity_usd', 0)
            if 1000 <= liquidity <= 10000:  # Sweet spot para memecoins
                analysis['factors']['liquidity'] = 20
                analysis['score'] += 20
            elif liquidity <= 50000:
                analysis['factors']['liquidity'] = 15
                analysis['score'] += 15
            else:
                analysis['factors']['liquidity'] = 5
                analysis['score'] += 5
            
            # Fator 3: Holders (poucos holders = early entry)
            holders = token_info.get('holders', 0)
            if holders <= 100:  # Muito early
                analysis['factors']['holders'] = 20
                analysis['score'] += 20
            elif holders <= 500:
                analysis['factors']['holders'] = 15
                analysis['score'] += 15
            else:
                analysis['factors']['holders'] = 10
                analysis['score'] += 10
            
            # Fator 4: Segurança básica
            if not token_info.get('is_honeypot', True):
                analysis['factors']['security'] = 15
                analysis['score'] += 15
            
            # Fator 5: Padrão de nome (memecoins têm padrões específicos)
            name = token_info.get('name', '').lower()
            symbol = token_info.get('symbol', '').lower()
            
            memecoin_keywords = ['doge', 'pepe', 'shib', 'moon', 'safe', 'baby', 'mini', 'inu', 'cat', 'frog']
            if any(keyword in name or keyword in symbol for keyword in memecoin_keywords):
                analysis['factors']['memecoin_pattern'] = 15
                analysis['score'] += 15
            
            # Determinar recomendação
            if analysis['score'] >= 70:
                analysis['recommendation'] = 'STRONG_BUY'
                analysis['confidence'] = 90
            elif analysis['score'] >= 50:
                analysis['recommendation'] = 'BUY'
                analysis['confidence'] = 70
            elif analysis['score'] >= 30:
                analysis['recommendation'] = 'WEAK_BUY'
                analysis['confidence'] = 50
            else:
                analysis['recommendation'] = 'SKIP'
                analysis['confidence'] = 30
            
            return analysis
            
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na análise IA: {str(e)}{Style.RESET_ALL}")
            return {'score': 0, 'recommendation': 'SKIP', 'confidence': 0}
    
    async def start(self):
        """Inicia o bot"""
        try:
            if not self.initialize():
                return False
            
            if not self.test_connections():
                return False
            
            self.running = True
            print(f"{Fore.GREEN}🚀 Sniper Bot iniciado e monitorando novos tokens!{Style.RESET_ALL}")
            
            # Iniciar monitoramento
            self.token_monitor.start_monitoring()
            
            # Iniciar Telegram bot SIMPLES (sem conflitos)
            if hasattr(self.telegram_bot, 'cleanup_and_disable_polling'):
                await self.telegram_bot.cleanup_and_disable_polling()
            elif hasattr(self.telegram_bot, 'start'):
                await self.telegram_bot.start()
            
            # Loop principal
            monitor_task = asyncio.create_task(self.token_monitor.monitor_new_tokens())
            status_task = asyncio.create_task(self._status_loop())
            
            await asyncio.gather(monitor_task, status_task)
            
        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}⏹️ Bot interrompido pelo usuário{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro no bot: {str(e)}{Style.RESET_ALL}")
        finally:
            self.stop()
    
    async def _status_loop(self):
        """Loop de status"""
        while self.running:
            await asyncio.sleep(60)  # A cada minuto
            self.print_status()
            
            # Enviar status via Telegram simples
            if hasattr(self.telegram_bot, 'send_status_update'):
                try:
                    balance_eth = 0.0
                    weth_balance = 0.0
                    
                    if self.web3:
                        balance = self.web3.eth.get_balance(WALLET_ADDRESS)
                        balance_eth = float(self.web3.from_wei(balance, 'ether'))
                        weth_balance = self._get_weth_balance_sync()
                    
                    status_data = {
                        'status': 'Rodando' if self.running else 'Parado',
                        'trades_executed': self.trades_executed,
                        'successful_trades': self.successful_trades,
                        'total_profit': f"{self.total_profit:.6f}",
                        'eth_balance': f"{balance_eth:.6f}",
                        'weth_balance': f"{weth_balance:.6f}"
                    }
                    
                    await self.telegram_bot.send_status_update(status_data)
                except Exception as e:
                    print(f"❌ Erro ao enviar status Telegram: {e}")
    
    def stop(self):
        """Para o bot"""
        self.running = False
        if self.token_monitor:
            self.token_monitor.stop_monitoring()
        print(f"{Fore.RED}⏹️ Sniper Bot parado!{Style.RESET_ALL}")

# Função principal para executar o bot
async def main():
    bot = SniperBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())