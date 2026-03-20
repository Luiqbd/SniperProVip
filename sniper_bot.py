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
from ai_optimizer import AIOptimizer
from ai_predictor import AIPredictor
from sniper_logger import *

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
        self.current_trade_amount = TRADE_AMOUNT_ETH
        self.dynamic_strategy = True
        self.profit_reinvestment = True
        self.initial_balance = INITIAL_ETH_BALANCE
        self.balance_history = []
        self.profit_history = []
        self.smart_scaling = SMART_SCALING_ENABLED
        self.last_balance_check = 0
        
        # Cache para saldos (evitar rate limit) - agora ETH nativo
        self._eth_balance_cache = 0.0
        self._eth_balance_time = 0
        
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

        # ============================================
        # INICIALIZAR TELEGRAM BOT ULTIMATE
        # ============================================
        print("=" * 50)
        print("🔍 INICIANDO TELEGRAM BOT...")
        print("=" * 50)
        
        # Verificar variáveis de ambiente
        import os
        tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
        tg_chat = os.getenv('TELEGRAM_CHAT_ID')
        print(f"📋 TELEGRAM_BOT_TOKEN: {'CONFIGURADO' if tg_token else 'NÃO CONFIGURADO'}")
        print(f"📋 TELEGRAM_CHAT_ID: {'CONFIGURADO' if tg_chat else 'NÃO CONFIGURADO'}")
        
        self.telegram_bot = None
        telegram_enabled = False
        try:
            print("📥 Importando ultimate_telegram...")
            from ultimate_telegram import get_ultimate_telegram
            print("📥 Chamando get_ultimate_telegram...")
            self.telegram_bot = get_ultimate_telegram(self)
            
            if self.telegram_bot:
                print(f"✅ Telegram bot criado: {type(self.telegram_bot)}")
                print(f"   Token: {'*' * 10}{self.telegram_bot.token[-10:] if self.telegram_bot.token else 'NENHUM'}")
                print(f"   Users: {len(self.telegram_bot.authorized_users)}")
                print(f"   Enabled: {self.telegram_bot.enabled}")
                
                telegram_enabled = self.telegram_bot.enabled
                
                if self.telegram_bot.enabled:
                    print("🚀 Iniciando polling do Telegram...")
                    self.telegram_bot.start_polling()
                    print("✅ Polling iniciado!")
                    
                    # Testar notificação
                    try:
                        print("📱 Enviando notificação de teste...")
                        self.telegram_bot.send_message_sync("🎯 **SNIPER INICIADO!**\n\n✅ Bot está funcionando!\n💰 Pronto para operar.")
                        print("✅ Notificação de teste enviada!")
                    except Exception as test_err:
                        print(f"⚠️ Erro no teste: {test_err}")
                else:
                    print("⚠️ Telegram desabilitado (faltando token/chat_id)")
            else:
                print("❌ Telegram bot é None!")
        except Exception as e:
            print(f"❌ ERRO AO CARREGAR TELEGRAM: {e}")
            import traceback
            traceback.print_exc()
        
        # Se Telegram não está funcionando, usar mock com prints
        if not telegram_enabled or not self.telegram_bot:
            print("⚠️ Usando Telegram mock (com prints)")
            self.telegram_bot = self._create_telegram_mock()
        
        print("=" * 50)
        print("✅ TELEGRAM BOT CONFIGURADO")
        print("=" * 50)
    
    def _create_telegram_mock(self):
        """Cria um mock do telegram bot para funcionar sem Telegram"""
        class TelegramMock:
            async def send_notification(self, message, priority="normal"):
                print(f"📱 Notificação [{priority}]: {message}")
            
            async def send_trade_alert(self, token_address, token_name, action, details=None):
                print(f"🚨 Trade Alert [{action}]: {token_name} ({token_address[:10]}...)")
            
            async def send_status_update(self, status_data):
                print(f"📊 Status: {status_data}")
            
            async def start(self):
                print("📱 Telegram Mock: Funcionando sem Telegram")
            
            def set_sniper_bot(self, bot):
                pass
        
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
            self.token_monitor = TokenMonitor(self.web3, self._process_new_token, self.dex_handler)
            self.security_validator = SecurityValidator(self.web3)
            
            # Inicializar estratégia agressiva
            self.aggressive_strategy = AggressiveStrategy(self)
            # Reset posições antigas para começar limpo
            self.aggressive_strategy.reset_positions()
            print(f"{Fore.GREEN}🚀 Estratégia agressiva ativada para crescimento rápido{Style.RESET_ALL}")
            
            # Inicializar IA Otimizador
            self.ai_optimizer = AIOptimizer(self)
            print(f"{Fore.CYAN}🤖 IA Otimizador ativada - Ajustes automáticos{Style.RESET_ALL}")
            
            # Inicializar IA Preditiva (para lucros grandes)
            self.ai_predictor = AIPredictor()
            print(f"{Fore.CYAN}🎯 IA Preditiva ativada - Foco em lucros grandes!{Style.RESET_ALL}")
            
            # Verificar saldo ETH nativo (agora usado diretamente para trading)
            balance = self.web3.eth.get_balance(WALLET_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance, 'ether'))
            
            print(f"{Fore.YELLOW}💰 Saldo ETH: {balance_eth:.6f} ETH{Style.RESET_ALL}")
            
            # Agora usamos ETH nativo diretamente - não precisa mais de ETH!
            eth_balance = balance_eth
            
            # Log de saldos
            print(f"💰 Saldos verificados:")
            print(f"⛽ ETH (Gas + Trading): {eth_balance:.6f}")
            print(f"📊 Total: {eth_balance:.6f} ETH")
            
            # Calcular saldo total disponível
            total_balance = eth_balance
            print(f"{Fore.CYAN}💰 Saldo total disponível: {total_balance:.6f} ETH{Style.RESET_ALL}")
            
            # Verificar se tem ETH suficiente para trading e gas
            min_eth_for_gas = 0.000001  # Mínimo ETH para gas (mais flexível)
            
            # Calcular quantos trades são possíveis
            possible_trades = int(eth_balance / TRADE_AMOUNT_ETH) if eth_balance > 0 else 0
            
            if eth_balance >= TRADE_AMOUNT_ETH:
                print(f"{Fore.GREEN}✅ Saldo otimizado para trading!{Style.RESET_ALL}")
                print(f"{Fore.GREEN}   ETH disponível: {eth_balance:.6f}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}   Valor por trade: {TRADE_AMOUNT_ETH:.6f} ETH{Style.RESET_ALL}")
                print(f"{Fore.GREEN}   Trades possíveis: {possible_trades} operações{Style.RESET_ALL}")
                if eth_balance >= min_eth_for_gas:
                    print(f"{Fore.GREEN}   ETH para gas: {eth_balance:.6f} ✅{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}   ETH para gas baixo: {eth_balance:.6f} (pode limitar trades){Style.RESET_ALL}")
                
                # Log bot pronto para operar
                print("🚀 BOT PRONTO PARA OPERAR!")
                print(f"✅ Inicialização completa")
                print(f"💰 Trades possíveis: {possible_trades}")
                print(f"🎯 Valor por trade: {TRADE_AMOUNT_ETH:.6f} ETH")
                print(f"⛽ Gas disponível: {'✅' if eth_balance >= min_eth_for_gas else '⚠️'}")
                print("🔍 Aguardando novos tokens...")
            else:
                print(f"{Fore.YELLOW}⚠️ Saldo baixo mas continuará monitorando!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}   ETH disponível: {eth_balance:.6f}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}   Necessário para 1 trade: {TRADE_AMOUNT_ETH:.6f}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}   💡 Bot aguardará mais saldo ou tokens com menor valor{Style.RESET_ALL}")
                
                # Log saldo baixo
                print("⚠️ BOT INICIADO - SALDO BAIXO")
                print(f"💰 ETH disponível: {eth_balance:.6f}")
                print(f"🎯 Necessário: {TRADE_AMOUNT_ETH:.6f} ETH")
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
                token_address, self.web3.to_wei(TRADE_AMOUNT_ETH, 'ether'), is_buy=True
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
            
            # Análise da IA Preditiva (para lucros grandes)
            if hasattr(self, 'ai_predictor'):
                predictor_result = self.ai_predictor.analyze_token(token_info)
                print(f"{Fore.MAGENTA}🎯 IA Preditiva: Score {predictor_result['score']}/100 - {predictor_result['prediction']}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}   Razão: {predictor_result['reason']}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}   Meta de lucro: {predictor_result['target_profit']*100:.0f}%{Style.RESET_ALL}")
            
            # Análise tradicional como backup
            traditional_analysis = self.token_monitor.analyze_token_potential(token_address)
            
            # Combinar análises (IA tem peso maior)
            combined_score = int(ai_analysis['score'] * 0.7 + traditional_analysis['score'] * 0.3)
            
            # Boost para tokens com prioridade HIGH (pares com ETH)
            if priority == "HIGH":
                combined_score = min(100, combined_score + 15)  # +15 pontos para pares ETH
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
        """Executa ordem de compra - ULTRA RÁPIDO"""
        try:
            print(f"{Fore.GREEN}⚡ EXECUTANDO COMPRA ULTRA RÁPIDA - {token_info['symbol']}...{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🎯 FOCO: LUCROS GRANDES!{Style.RESET_ALL}")
            
            # Usar valor dinâmico da estratégia + IA
            if self.aggressive_strategy:
                trade_amount = self.aggressive_strategy.calculate_dynamic_trade_amount()
            else:
                trade_amount = self.current_trade_amount
            
            # IA também pode ajustar o valor
            if hasattr(self, 'ai_optimizer'):
                ai_amount = self.ai_optimizer.get_optimal_trade_amount()
                if ai_amount < trade_amount:
                    trade_amount = ai_amount
                    print(f"🤖 IA ajustou valor para: {trade_amount:.6f} ETH")
            
            # Notificar início da compra
            await self.telegram_bot.send_notification(
                f"💰 **Iniciando compra!**\n"
                f"📛 **{token_info['symbol']}**\n"
                f"💎 Valor: {trade_amount:.6f} ETH\n"
                f"🧠 Estratégia: {'Dinâmica' if self.dynamic_strategy else 'Fixa'}\n"
                f"🔍 Verificando saldos...", 
                "high"
            )
            
            # Verificar saldo antes de executar - agora usa ETH nativo diretamente
            balance = self.web3.eth.get_balance(WALLET_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance, 'ether'))
            # Agora usamos ETH nativo diretamente para trading
            eth_balance = balance_eth
            
            # Log de verificação de saldo
            log_balance_check(eth_balance)
            
            # Log detalhado dos saldos
            print(f"{Fore.CYAN}💰 Verificação de saldos:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   ETH (gas + trading): {eth_balance:.6f} ETH{Style.RESET_ALL}")
            print(f"{Fore.CYAN}   Trade amount: {trade_amount:.6f} ETH{Style.RESET_ALL}")
            
            # =====================================================
            # LÓGICA URGENTE: SEMPRE garantir ETH para gas PRIMEIRO
            # =====================================================
            
            # Verificar se tem ETH mínimo para QUALQUER transação
            MIN_ETH_FOR_ANY_TX = 0.00003  # Mínimo para fazer qualquer transação na Base
            
            if balance_eth < MIN_ETH_FOR_ANY_TX:
                print(f"{Fore.RED}⚠️ ETH CRÍTICAMENTE BAIXO!{Style.RESET_ALL}")
                print(f"{Fore.RED}   ETH atual: {balance_eth:.9f}{Style.RESET_ALL}")
                print(f"{Fore.RED}   Mínimo para transação: {MIN_ETH_FOR_ANY_TX}{Style.RESET_ALL}")
                
                # Verificar se é caso de "saldo zero" - situação irrecuperável sem ETH
                if balance_eth < 0.000001:
                    print(f"{Fore.RED}🚨 SITUAÇÃO CRÍTICA: ETH ZERO!{Style.RESET_ALL}")
                    print(f"{Fore.RED}   Não é possível fazer nenhuma transação!{Style.RESET_ALL}")
                    await self.telegram_bot.send_notification(
                        f"🚨 **CRISE DE GAS!**\n"
                        f"💰 ETH atual: {balance_eth:.9f}\n"
                        f"⚠️ Você NÃO tem ETH para pagar gas!\n"
                        f"💡 ENVIE ETH para sua carteira:\n"
                        f"   `{WALLET_ADDRESS}`\n"
                        f"⚠️ Mínimo recomendado: 0.001 ETH\n"
                        f"❌ Compra cancelada", 
                        "high"
                    )
                else:
                    await self.telegram_bot.send_notification(
                        f"🚨 **ETH INSUFICIENTE!**\n"
                        f"💰 ETH atual: {balance_eth:.9f}\n"
                        f"⚠️ Mínimo necessário: {MIN_ETH_FOR_ANY_TX}\n"
                        f"💡 Adicione ETH à sua carteira!\n"
                        f"❌ Compra cancelada", 
                        "high"
                    )
                return
            
            # Ajustar trade_amount se ETH insuficiente
            if eth_balance < trade_amount:
                available_eth = eth_balance * 0.95
                if available_eth >= 0.000050:
                    trade_amount = available_eth
                    print(f"{Fore.YELLOW}💡 Usando ETH disponível: {trade_amount:.6f}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}❌ ETH insuficiente!{Style.RESET_ALL}")
                    log_insufficient_balance(token_info.get('symbol', 'UNKNOWN'), trade_amount, eth_balance, "ETH")
                    await self.telegram_bot.send_notification(
                        f"❌ **Compra cancelada**\n"
                        f"💰 ETH: {eth_balance:.6f}\n"
                        f"⚠️ Saldo muito baixo", 
                        "high"
                    )
                    return
            
            # Verificação final ETH
            if eth_balance < 0.000001:
                log_insufficient_balance(token_info.get('symbol', 'UNKNOWN'), 0.000001, eth_balance, "ETH")
                print(f"{Fore.RED}❌ ETH insuficiente!{Style.RESET_ALL}")
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
            
            # Só cancelar se best_dex for None (erro real)
            if not best_dex:
                print(f"{Fore.RED}❌ Token sem liquidez - CANCELANDO COMPRA{Style.RESET_ALL}")
                await self.telegram_bot.send_notification(
                    f"❌ **Compra cancelada**\n"
                    f"📛 {token_info['symbol']}\n"
                    f"⚠️ Sem liquidez disponível",
                    "high"
                )
                return None  # Cancelar compra
            
            # Se best_price é 1, é modo arriscado
            if best_price == 1:
                print(f"{Fore.YELLOW}⚠️ MODO ARRISCADO: Comprando sem liquidez confirmada!{Style.RESET_ALL}")
                await self.telegram_bot.send_notification(
                    f"⚠️ **MODO ARRISCADO**\n"
                    f"📛 {token_info['symbol']}\n"
                    f"💡 Tentando comprar mesmo sem liquidez\n"
                    f"⚠️ Risco: transação pode falhar",
                    "high"
                )
            
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
                print(f"{Fore.GREEN}✅ Compra enviada! TX: {tx_hash}{Style.RESET_ALL}")
                log_buy_attempt(token_info.get('symbol', 'UNKNOWN'), trade_amount, f"TX: {tx_hash}")
                print(f"{Fore.YELLOW}⏳ Aguardando confirmação da blockchain...{Style.RESET_ALL}")
                
                # Aguardar confirmação
                await asyncio.sleep(10)
                
                # Verificar se a transação foi confirmada
                try:
                    buy_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                    if buy_receipt and buy_receipt.status == 1:
                        self.trades_executed += 1
                        print(f"{Fore.GREEN}✅ Compra CONFIRMADA! TX: {tx_hash}{Style.RESET_ALL}")
                        log_buy_success(token_info.get('symbol', 'UNKNOWN'), trade_amount, tx_hash, best_dex)
                        
                        # Notificar via sistema em tempo real
                        try:
                            await self.telegram_bot.send_trade_alert(
                                tx_hash, token_info['symbol'], "BUY", {"amount": trade_amount, "price": best_price}
                            )
                            await self.telegram_bot.send_notification(
                                f"🟢 **COMPRA CONFIRMADA!**\n\n"
                                f"📛 Token: {token_info['symbol']}\n"
                                f"💰 Valor: {trade_amount:.6f} ETH\n"
                                f"🔗 TX: `{tx_hash[:10]}...{tx_hash[-10:]}`\n"
                                f"⏰ Data: {datetime.now().strftime('%H:%M:%S')}", 
                                "high"
                            )
                            print(f"📱 Notificação de compra enviada!")
                        except Exception as e:
                            print(f"⚠️ Erro ao enviar notificação: {e}")
                            log_error("NOTIFICATION_ERROR", str(e))
                        
                        # Agendar venda
                        asyncio.create_task(self._schedule_sell_order(token_address, token_info, tx_hash))
                    else:
                        status = buy_receipt.status if buy_receipt else 'N/A'
                        print(f"{Fore.RED}❌ Compra FALHOU na blockchain (Status: {status}){Style.RESET_ALL}")
                        log_buy_failure(token_info.get('symbol', 'UNKNOWN'), trade_amount, f"Status: {status}")
                        log_tx_reverted(tx_hash, f"Status: {status}")
                        await self.telegram_bot.send_notification(
                            f"❌ **Compra FALHOU!**\n\n"
                            f"📛 Token: {token_info['symbol']}\n"
                            f"🔗 TX: `{tx_hash[:10]}...{tx_hash[-10:]}`\n"
                            f"⚠️ Transação revertida\n"
                            f"⏰ Data: {datetime.now().strftime('%H:%M:%S')}", 
                            "high"
                        )
                except Exception as e:
                    print(f"{Fore.RED}❌ Erro ao verificar transação: {e}{Style.RESET_ALL}")
                    log_error("BUY_RECEIPT_ERROR", str(e), tx_hash=tx_hash)
                
                # Log da transação
                if ENABLE_LOGGING:
                    self.logger.info(f"BUY - {token_info['symbol']} - Amount: {trade_amount} ETH - TX: {tx_hash}")
            else:
                print(f"{Fore.RED}❌ Falha na execução da compra{Style.RESET_ALL}")
                log_buy_failure(token_info.get('symbol', 'UNKNOWN'), trade_amount, "execute_swap returned None")
                await self.telegram_bot.send_notification(
                    f"❌ Falha na compra de {token_info['symbol']} - Verifique gas e liquidez", 
                    "high"
                )
                
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na execução da compra: {str(e)}{Style.RESET_ALL}")
            log_error("BUY_EXECUTION_ERROR", str(e), exception=e)
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
            
            if not best_dex or best_price == 0:
                print(f"{Fore.RED}❌ Token sem liquidez para venda - CANCELANDO{Style.RESET_ALL}")
                return None  # Cancelar venda
            
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
                print(f"{Fore.GREEN}✅ Venda enviada! TX: {sell_tx_hash}{Style.RESET_ALL}")
                log_sell_attempt(token_info.get('symbol', 'UNKNOWN'), token_balance)
                
                # Aguardar e verificar confirmação
                await asyncio.sleep(10)
                
                try:
                    sell_receipt = self.web3.eth.get_transaction_receipt(sell_tx_hash)
                    if sell_receipt and sell_receipt.status == 1:
                        self.successful_trades += 1
                        print(f"{Fore.GREEN}✅ Venda CONFIRMADA! TX: {sell_tx_hash}{Style.RESET_ALL}")
                        log_sell_success(token_info.get('symbol', 'UNKNOWN'), token_balance, sell_tx_hash)
                        
                        # Notificar venda via Telegram
                        try:
                            await self.telegram_bot.send_trade_alert(
                                sell_tx_hash, token_info['symbol'], "SELL", {"amount": token_balance, "price": best_price}
                            )
                            await self.telegram_bot.send_notification(
                                f"🔴 **VENDA CONFIRMADA!**\n\n"
                                f"📛 Token: {token_info['symbol']}\n"
                                f"💰 Saldo: {token_balance:.6f} tokens\n"
                                f"🔗 TX: `{sell_tx_hash[:10]}...{sell_tx_hash[-10:]}`\n"
                                f"⏰ Data: {datetime.now().strftime('%H:%M:%S')}", 
                                "high"
                            )
                            print(f"📱 Notificação de venda enviada!")
                        except Exception as e:
                            print(f"⚠️ Erro ao enviar notificação de venda: {e}")
                            log_error("SELL_NOTIFICATION_ERROR", str(e))
                        
                        # Calcular lucro
                        await self._calculate_profit(buy_tx_hash, sell_tx_hash, token_info.get('symbol', 'TOKEN'))
                    else:
                        status = sell_receipt.status if sell_receipt else 'N/A'
                        print(f"{Fore.RED}❌ Venda FALHOU na blockchain (Status: {status}){Style.RESET_ALL}")
                        log_sell_failure(token_info.get('symbol', 'UNKNOWN'), token_balance, f"Status: {status}")
                        log_tx_reverted(sell_tx_hash, f"Status: {status}")
                        await self.telegram_bot.send_notification(
                            f"❌ **VENDA FALHOU!**\n\n"
                            f"📛 Token: {token_info['symbol']}\n"
                            f"🔗 TX: `{sell_tx_hash[:10]}...{sell_tx_hash[-10:]}`\n"
                            f"⚠️ Transação revertida", 
                            "high"
                        )
                except Exception as e:
                    print(f"{Fore.RED}❌ Erro ao verificar venda: {e}{Style.RESET_ALL}")
                    log_error("SELL_RECEIPT_ERROR", str(e), tx_hash=sell_tx_hash)
                
                # Log da transação
                if ENABLE_LOGGING:
                    self.logger.info(f"SELL - {token_info['symbol']} - TX: {sell_tx_hash}")
            else:
                print(f"{Fore.RED}❌ Falha na execução da venda{Style.RESET_ALL}")
                log_sell_failure(token_info.get('symbol', 'UNKNOWN'), token_balance, "execute_swap returned None")
                await self.telegram_bot.send_notification(
                    f"❌ **Falha na venda!**\n"
                    f"📛 {token_info['symbol']}\n"
                    f"🚫 Transação não foi executada\n"
                    f"💡 Tokens ainda na carteira", 
                    "high"
                )
                
        except Exception as e:
            print(f"{Fore.RED}❌ Erro na execução da venda: {str(e)}{Style.RESET_ALL}")
            log_error("SELL_EXECUTION_ERROR", str(e), exception=e)
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
    
    async def _calculate_profit(self, buy_tx_hash: str, sell_tx_hash: str, token_symbol: str = "TOKEN"):
        """Calcula lucro da operação"""
        try:
            # Pequena pausa para garantir que as transações estão confirmadas
            await asyncio.sleep(2)
            
            try:
                buy_receipt = self.web3.eth.get_transaction_receipt(buy_tx_hash)
                sell_receipt = self.web3.eth.get_transaction_receipt(sell_tx_hash)
                
                buy_tx = self.web3.eth.get_transaction(buy_tx_hash)
                sell_tx = self.web3.eth.get_transaction(sell_tx_hash)
                
                # Calcular custos de gas
                buy_gas_cost = buy_receipt.gasUsed * buy_tx.gasPrice
                sell_gas_cost = sell_receipt.gasUsed * sell_tx.gasPrice
                total_gas_cost = self.web3.from_wei(buy_gas_cost + sell_gas_cost, 'ether')
                
            except Exception as e:
                print(f"⚠️ Erro ao obter receipts: {e}")
                total_gas_cost = 0.0015  # Estimativa
            
            # Obter saldos atuais
            current_eth = float(self.web3.from_wei(self.web3.eth.get_balance(WALLET_ADDRESS), 'ether'))
            current_weth = self._get_eth_balance_sync()
            
            # Calcular lucro baseado na diferença de saldo
            # (simplificado - considera saldo ETH antes e depois)
            initial_total = 0.006854  # Saldo inicial estimado
            current_total = current_eth + current_weth
            profit = current_total - initial_total
            
            self.total_profit += profit
            
            # Notificação de LUCRO
            emoji = "🟢" if profit >= 0 else "🔴"
            await self.telegram_bot.send_notification(
                f"{emoji} **LUCRO/STOP-LOSS!**\n\n"
                f"📛 Token: {token_symbol}\n"
                f"💰 Lucro: {profit:+.6f} ETH\n"
                f"💰 Lucro total: {self.total_profit:+.6f} ETH\n"
                f"⛽ Gas gasto: ~{total_gas_cost:.6f} ETH\n"
                f"💵 Saldo atual: {current_total:.6f} ETH\n"
                f"⏰ Data: {datetime.now().strftime('%H:%M:%S')}", 
                "high"
            )
            
            print(f"{Fore.CYAN}💹 Lucro: {profit:+.6f} ETH | Total: {self.total_profit:+.6f} ETH{Style.RESET_ALL}")
            
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
        print(f"{Fore.YELLOW}⚙️ Valor por trade: {TRADE_AMOUNT_ETH} ETH{Style.RESET_ALL}")
        
        # Status da IA
        if hasattr(self, 'ai_optimizer'):
            ai_status = self.ai_optimizer.get_status()
            print(f"{Fore.CYAN}{'='*50}")
            print(f"🤖 IA OTIMIZADOR")
            print(f"{'='*50}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}🎯 Win Rate: {ai_status['win_rate']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📊 Trades: {ai_status['trades']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}🔥 Sequência atual: {ai_status['current_streak']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💵 Saldo IA: {ai_status['balance']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📈 {ai_status['recommendation']}{Style.RESET_ALL}")
        
        if self.web3:
            # Mostrar saldo ETH (para gas)
            balance = self.web3.eth.get_balance(WALLET_ADDRESS)
            balance_eth = float(self.web3.from_wei(balance, 'ether'))
            
            # Mostrar saldo ETH (para trading)
            eth_balance = self._get_eth_balance_sync()
            
            print(f"{Fore.YELLOW}💳 Saldo ETH (gas): {balance_eth:.6f} ETH{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💰 Saldo ETH (trading): {eth_balance:.6f} ETH{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}📊 Total estimado: {balance_eth + eth_balance:.6f} ETH{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")
    
    def _get_eth_balance_sync(self) -> float:
        """Obtém saldo ETH nativo da carteira com cache e retry"""
        # Cache por 30 segundos para evitar rate limit
        current_time = time.time()
        if hasattr(self, '_eth_balance_cache') and hasattr(self, '_eth_balance_time'):
            if current_time - self._eth_balance_time < 30:
                cached_balance = self._eth_balance_cache
                # Diagnóstico: se cache for 0, forçar atualização
                if cached_balance == 0.0:
                    print(f"{Fore.YELLOW}⚠️ Cache ETH zerado detectado - forçando atualização...{Style.RESET_ALL}")
                else:
                    return cached_balance
        
        for attempt in range(3):
            try:
                # Obter saldo ETH nativo diretamente
                balance = self.web3.eth.get_balance(WALLET_ADDRESS)
                result = float(self.web3.from_wei(balance, 'ether'))
                
                # Log detalhado para diagnóstico
                print(f"{Fore.GREEN}✅ Saldo ETH nativo lido: {result:.6f} ETH (raw: {balance}){Style.RESET_ALL}")
                
                # Cache o resultado
                self._eth_balance_cache = result
                self._eth_balance_time = current_time
                
                # Diagnóstico adicional
                if result == 0.0:
                    print(f"{Fore.RED}⚠️ ATENÇÃO: Saldo ETH é 0.0 - verificar configuração da carteira{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}📍 Carteira: {WALLET_ADDRESS}{Style.RESET_ALL}")
                
                return result
                
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"{Fore.YELLOW}⚠️ Rate limit - tentativa {attempt + 1}/3{Style.RESET_ALL}")
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                else:
                    print(f"{Fore.RED}❌ Erro ao obter saldo ETH: {str(e)}{Style.RESET_ALL}")
                    break
        
        # Se falhou, retorna último valor em cache ou valor padrão
        if hasattr(self, '_eth_balance_cache'):
            print(f"{Fore.YELLOW}⚠️ Usando saldo em cache: {self._eth_balance_cache:.6f} ETH{Style.RESET_ALL}")
            return self._eth_balance_cache
        
        return 0.0
    
    # Mantido para compatibilidade
    def _get_eth_balance_sync(self) -> float:
        """Obtém saldo ETH nativo (agora usa ETH diretamente)"""
        return self._get_eth_balance_sync()
    
    async def _get_eth_balance(self) -> float:
        """Obtém saldo ETH nativo (versão assíncrona)"""
        return self._get_eth_balance_sync()
    
    async def _get_eth_balance(self) -> float:
        """Obtém saldo ETH nativo da carteira (versão assíncrona)"""
        return self._get_eth_balance_sync()
    
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
            
            current_eth_balance = await self._get_eth_balance()
            current_time = time.time()
            
            # Atualizar histórico de saldo
            self.balance_history.append({
                'timestamp': current_time,
                'balance': current_eth_balance
            })
            
            # Manter apenas últimas 100 entradas
            if len(self.balance_history) > 100:
                self.balance_history = self.balance_history[-100:]
            
            # Calcular crescimento do saldo
            growth_factor = current_eth_balance / self.initial_balance if self.initial_balance > 0 else 1
            
            # Sistema de escalonamento inteligente
            if growth_factor >= 1.5:  # Saldo cresceu 50%
                # Aumentar valor por trade proporcionalmente
                base_percentage = MAX_TRADE_PERCENTAGE / 100
                growth_bonus = min((growth_factor - 1) * 0.1, 0.15)  # Máximo 15% de bônus
                new_percentage = base_percentage + growth_bonus
                
                new_trade_amount = min(
                    current_eth_balance * new_percentage,
                    current_eth_balance * 0.35  # Máximo 35% do saldo
                )
                
                # Garantir valor mínimo
                new_trade_amount = max(new_trade_amount, MIN_TRADE_AMOUNT)
                
                if abs(new_trade_amount - self.current_trade_amount) > 0.000050:  # Mudança significativa
                    self.current_trade_amount = new_trade_amount
                    
                    await self.telegram_bot.send_notification(
                        f"🧠 **ESTRATÉGIA INTELIGENTE ATIVADA!**\n\n"
                        f"📈 **Crescimento:** {(growth_factor-1)*100:.1f}%\n"
                        f"💰 **Saldo atual:** {current_eth_balance:.6f} ETH\n"
                        f"🎯 **Novo valor/trade:** {new_trade_amount:.6f} ETH\n"
                        f"⚡ **Percentual:** {(new_trade_amount/current_eth_balance)*100:.1f}%\n\n"
                        f"🚀 **Maximizando retornos com crescimento!**", 
                        "high"
                    )
                    
                    print(f"{Fore.GREEN}🧠 Estratégia inteligente: {new_trade_amount:.6f} ETH por trade ({(new_trade_amount/current_eth_balance)*100:.1f}% do saldo){Style.RESET_ALL}")
            
            elif current_eth_balance < self.initial_balance * 0.8:  # Saldo caiu 20%
                # Reduzir valor por trade para preservar capital
                conservative_amount = max(
                    current_eth_balance * 0.15,  # 15% do saldo atual
                    MIN_TRADE_AMOUNT
                )
                
                if conservative_amount < self.current_trade_amount:
                    self.current_trade_amount = conservative_amount
                    
                    await self.telegram_bot.send_notification(
                        f"🛡️ **MODO CONSERVADOR ATIVADO**\n\n"
                        f"📉 **Saldo atual:** {current_eth_balance:.6f} ETH\n"
                        f"🎯 **Valor reduzido:** {conservative_amount:.6f} ETH\n"
                        f"💡 **Preservando capital para recuperação**", 
                        "normal"
                    )
                    
                    print(f"{Fore.YELLOW}🛡️ Modo conservador: {conservative_amount:.6f} ETH por trade{Style.RESET_ALL}")
            
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
            current_balance = await self._get_eth_balance()
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
                    eth_balance = 0.0
                    
                    if self.web3:
                        balance = self.web3.eth.get_balance(WALLET_ADDRESS)
                        balance_eth = float(self.web3.from_wei(balance, 'ether'))
                        eth_balance = self._get_eth_balance_sync()
                    
                    status_data = {
                        'status': 'Rodando' if self.running else 'Parado',
                        'trades_executed': self.trades_executed,
                        'successful_trades': self.successful_trades,
                        'total_profit': f"{self.total_profit:.6f}",
                        'eth_balance': f"{balance_eth:.6f}",
                        'eth_balance': f"{eth_balance:.6f}"
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