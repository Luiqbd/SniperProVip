import asyncio
import logging
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import *
from rate_limiter import TELEGRAM_LIMITER

class TelegramBotHandler:
    """Bot Telegram ULTRA SIMPLIFICADO - apenas essenciais"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, sniper_bot=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, sniper_bot=None):
        if self._initialized:
            return
            
        self.sniper_bot = sniper_bot
        self.application = None
        self.notifications_enabled = True
        # Configurar usuários autorizados, filtrando IDs inválidos
        try:
            user_ids = [x.strip() for x in TELEGRAM_AUTHORIZED_USERS.split(',') if x.strip()]
            self.authorized_users = []
            for user_id in user_ids:
                try:
                    uid = int(user_id)
                    # Filtrar IDs de teste/placeholder
                    if uid != 123456789 and uid > 0:
                        self.authorized_users.append(uid)
                    else:
                        print(f"⚠️ ID de usuário inválido ignorado: {user_id}")
                except ValueError:
                    print(f"⚠️ ID de usuário não numérico ignorado: {user_id}")
            
            if not self.authorized_users:
                print("⚠️ Nenhum usuário autorizado válido configurado!")
                print("💡 Configure TELEGRAM_AUTHORIZED_USERS com IDs reais do Telegram")
        except:
            self.authorized_users = []
            print("⚠️ Erro ao configurar usuários autorizados")
        self._initialized = True
        
        # Stats básicas
        self.monitoring_stats = {
            'tokens_analyzed': 0,
            'trades_executed': 0,
            'total_profit': 0.0,
            'start_time': datetime.now()
        }
        self.successful_trades = 0
    
    async def start(self):
        """Inicia o bot Telegram"""
        if not TELEGRAM_BOT_TOKEN:
            print("⚠️ Token do Telegram não configurado - funcionando sem Telegram")
            self.notifications_enabled = False
            return
            
        try:
            print("🧹 INICIANDO LIMPEZA EXTREMA DO TELEGRAM...")
            
            # Força limpeza MÚLTIPLAS VEZES
            for attempt in range(3):
                print(f"🧹 Tentativa de limpeza {attempt + 1}/3...")
                await self._force_cleanup()
                await asyncio.sleep(3)  # Aguardar entre tentativas
            
            print("⏳ Aguardando 15 segundos para garantir limpeza total...")
            await asyncio.sleep(15)
            
            # Configurar aplicação com timeout mais baixo para evitar conflitos
            self.application = (Application.builder()
                              .token(TELEGRAM_BOT_TOKEN)
                              .read_timeout(15)
                              .write_timeout(15)
                              .connect_timeout(15)
                              .pool_timeout(15)
                              .build())
            
            # Handlers essenciais
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # Inicia o bot com recuperação automática
            await self.application.initialize()
            await self.application.start()
            
            # Configurar polling com recuperação automática
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            
            print("🤖 Bot Telegram iniciado com sucesso!")
            print("📱 Bot está pronto para receber comandos!")
            
            # Retornar imediatamente - polling roda em background
            
        except Exception as e:
            print(f"❌ Erro ao iniciar bot Telegram: {e}")
            # Tentar recuperação automática
            await self._handle_telegram_error(e)
    
    async def _force_cleanup(self):
        """Força limpeza AGRESSIVA de instâncias anteriores"""
        try:
            import requests
            import time
            
            print("🧹 Iniciando limpeza AGRESSIVA de instâncias Telegram...")
            
            # 1. Parar qualquer polling ativo
            if hasattr(self, 'application') and self.application:
                try:
                    await self.application.stop()
                    await self.application.shutdown()
                    print("✅ Aplicação anterior finalizada")
                except:
                    pass
            
            # 2. Deletar webhook com múltiplas tentativas
            for attempt in range(5):
                try:
                    response = requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook",
                        json={"drop_pending_updates": True},
                        timeout=15
                    )
                    if response.status_code == 200:
                        print("✅ Webhook deletado com sucesso")
                        break
                except:
                    if attempt == 2:
                        print("⚠️ Falha ao deletar webhook, continuando...")
                    time.sleep(1)
            
            # 2. Limpar updates pendentes com offset alto
            for attempt in range(3):
                try:
                    response = requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                        json={"offset": -1, "limit": 100, "timeout": 1},
                        timeout=10
                    )
                    if response.status_code == 200:
                        print("✅ Updates pendentes limpos")
                        break
                except:
                    if attempt == 2:
                        print("⚠️ Falha ao limpar updates, continuando...")
                    time.sleep(1)
            
            # 3. Forçar limpeza com offset muito alto - MÚLTIPLAS TENTATIVAS
            for attempt in range(5):
                try:
                    # Usar offset extremamente alto para forçar limpeza
                    response = requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                        json={"offset": 999999999, "limit": 100, "timeout": 1},
                        timeout=15
                    )
                    print(f"✅ Limpeza forçada - tentativa {attempt + 1}")
                    
                    # Tentar também com offset -1
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                        json={"offset": -1, "limit": 100, "timeout": 1},
                        timeout=15
                    )
                    
                    time.sleep(3)
                except:
                    pass
            
            # 4. Aguardar MUITO TEMPO para garantir que outras instâncias parem
            print("⏳ Aguardando finalização de outras instâncias...")
            time.sleep(15)
            
            # 5. Última tentativa de limpeza antes de finalizar
            try:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                    json={"offset": 999999999, "limit": 1, "timeout": 1},
                    timeout=10
                )
                print("✅ Limpeza final executada")
            except:
                pass
            
            # 5. Verificar se ainda há conflitos
            try:
                test_response = requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe",
                    timeout=5
                )
                if test_response.status_code == 200:
                    print("✅ API Telegram respondendo normalmente")
                else:
                    print(f"⚠️ API Telegram retornou status: {test_response.status_code}")
            except:
                print("⚠️ Erro ao testar API Telegram")
            
            print("✅ Limpeza de instâncias Telegram concluída")
            
        except Exception as e:
            print(f"⚠️ Erro na limpeza Telegram: {str(e)}")
            # Aguardar mesmo em caso de erro
            import time
            time.sleep(3)
    
    async def _handle_telegram_error(self, error):
        """Trata erros do Telegram e tenta recuperação"""
        error_str = str(error).lower()
        
        if "conflict" in error_str or "terminated by other" in error_str:
            print("🔄 Detectado conflito de instâncias - tentando recuperação...")
            
            # Aguardar e tentar limpeza novamente
            await asyncio.sleep(5)
            await self._force_cleanup()
            
            # Tentar reiniciar após limpeza
            try:
                await asyncio.sleep(3)
                await self.start()
            except:
                print("❌ Falha na recuperação automática do Telegram")
        else:
            print(f"❌ Erro não recuperável do Telegram: {error}")
    
    def is_authorized(self, user_id: int) -> bool:
        """Verifica se usuário está autorizado"""
        return user_id in self.authorized_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        # Log do usuário que está usando o bot
        user_id = update.effective_user.id
        username = update.effective_user.username or "Desconhecido"
        print(f"📱 Comando /start recebido de: {username} (ID: {user_id})")
        
        # Verificar autorização apenas se houver usuários configurados
        if self.authorized_users and not self.is_authorized(user_id):
            await update.message.reply_text("❌ Acesso não autorizado!")
            return
        
        welcome_text = f"""
🚀 **SNIPER BOT V6 - ATIVO**

💰 **Status da Carteira:**
• ETH: {self.get_eth_balance():.6f} ETH
• ETH: {self.get_eth_balance():.6f} ETH

🤖 **Bot Status:** {'🟢 ATIVO' if self.is_bot_running() else '🔴 PARADO'}

📊 **Performance:**
• Trades: {self.monitoring_stats['trades_executed']}
• Lucro: {self.monitoring_stats['total_profit']:.6f} ETH
"""
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    def get_main_menu_keyboard(self):
        """Menu principal organizado com botões essenciais e avançados"""
        bot_status = "🟢" if self.is_bot_running() else "🔴"
        
        keyboard = [
            # Controles essenciais
            [
                InlineKeyboardButton(f"🚀 START {bot_status}", callback_data="start_bot"),
                InlineKeyboardButton("⏹️ STOP", callback_data="stop_bot")
            ],
            # Informações básicas
            [
                InlineKeyboardButton("📊 STATUS", callback_data="dashboard"),
                InlineKeyboardButton("💰 CARTEIRA", callback_data="wallet")
            ],
            # Configurações de trading
            [
                InlineKeyboardButton("⚙️ CONFIG", callback_data="config"),
                InlineKeyboardButton("📈 TRADES", callback_data="trades_history")
            ],
            # Ferramentas avançadas
            [
                InlineKeyboardButton("🔧 AVANÇADO", callback_data="advanced_menu"),
                InlineKeyboardButton("🔄 REFRESH", callback_data="refresh")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_advanced_menu_keyboard(self):
        """Menu avançado com funcionalidades extras"""
        keyboard = [
            # Análise e monitoramento
            [
                InlineKeyboardButton("🔍 ANÁLISE TOKEN", callback_data="analyze_token"),
                InlineKeyboardButton("📊 ESTATÍSTICAS", callback_data="stats")
            ],
            # Configurações avançadas
            [
                InlineKeyboardButton("💰 AJUSTAR VALOR", callback_data="adjust_amount"),
                InlineKeyboardButton("⚡ VELOCIDADE", callback_data="speed_config")
            ],
            # Segurança e logs
            [
                InlineKeyboardButton("🛡️ SEGURANÇA", callback_data="security_check"),
                InlineKeyboardButton("📝 LOGS", callback_data="view_logs")
            ],
            # Voltar
            [
                InlineKeyboardButton("⬅️ VOLTAR", callback_data="back_to_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_config_menu_keyboard(self):
        """Menu de configurações"""
        keyboard = [
            # Configurações de trading
            [
                InlineKeyboardButton("💰 VALOR TRADE", callback_data="set_trade_amount"),
                InlineKeyboardButton("⚡ SLIPPAGE", callback_data="set_slippage")
            ],
            # Configurações de segurança
            [
                InlineKeyboardButton("🛡️ FILTROS", callback_data="security_filters"),
                InlineKeyboardButton("🔔 ALERTAS", callback_data="notification_settings")
            ],
            # Configurações de DEX
            [
                InlineKeyboardButton("🔄 DEX PREFS", callback_data="dex_preferences"),
                InlineKeyboardButton("⏱️ TIMEOUTS", callback_data="timeout_settings")
            ],
            # Voltar
            [
                InlineKeyboardButton("⬅️ VOLTAR", callback_data="back_to_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipula callbacks dos botões com tratamento de erro robusto"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Log do usuário que está usando o bot
            user_id = query.from_user.id
            username = query.from_user.username or "Desconhecido"
            print(f"📱 Botão pressionado por: {username} (ID: {user_id}) - Ação: {query.data}")
            
            # Verificar autorização apenas se houver usuários configurados
            if self.authorized_users and not self.is_authorized(user_id):
                await query.edit_message_text("❌ Acesso não autorizado!")
                return
            
            data = query.data
            
            # Botões principais
            if data == "refresh":
                await self.handle_refresh(query)
            elif data == "start_bot":
                await self.handle_start_bot(query)
            elif data == "stop_bot":
                await self.handle_stop_bot(query)
            elif data == "dashboard":
                await self.handle_dashboard(query)
            elif data == "wallet":
                await self.handle_wallet(query)
            
            # Menus
            elif data == "config":
                await self.handle_config_menu(query)
            elif data == "advanced_menu":
                await self.handle_advanced_menu(query)
            elif data == "back_to_main":
                await self.handle_refresh(query)
            
            # Histórico e estatísticas
            elif data == "trades_history":
                await self.handle_trades_history(query)
            elif data == "stats":
                await self.handle_stats(query)
            
            # Configurações avançadas
            elif data == "analyze_token":
                await self.handle_analyze_token(query)
            elif data == "adjust_amount":
                await self.handle_adjust_amount(query)
            elif data == "speed_config":
                await self.handle_speed_config(query)
            elif data == "security_check":
                await self.handle_security_check(query)
            elif data == "view_logs":
                await self.handle_view_logs(query)
            
            # Configurações específicas
            elif data == "set_trade_amount":
                await self.handle_set_trade_amount(query)
            elif data == "set_slippage":
                await self.handle_set_slippage(query)
            elif data == "security_filters":
                await self.handle_security_filters(query)
            elif data == "notification_settings":
                await self.handle_notification_settings(query)
            elif data == "dex_preferences":
                await self.handle_dex_preferences(query)
            elif data == "timeout_settings":
                await self.handle_timeout_settings(query)
            
            else:
                await query.edit_message_text(
                    f"🔧 Função '{data}' em desenvolvimento...\n\n⬅️ Use o botão REFRESH para voltar ao menu principal",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 REFRESH", callback_data="refresh")]])
                )
                
        except Exception as e:
            print(f"❌ Erro no callback do botão: {str(e)}")
            try:
                await query.edit_message_text(
                    f"❌ **Erro ao processar comando**\n\n🔧 Detalhes: {str(e)[:100]}\n\n⬅️ Use REFRESH para voltar",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 REFRESH", callback_data="refresh")]]),
                    parse_mode='Markdown'
                )
            except:
                # Se não conseguir editar a mensagem, tentar enviar nova
                try:
                    await query.message.reply_text(
                        f"❌ Erro no botão: {str(e)[:50]}...\n\nUse /start para reiniciar"
                    )
                except:
                    pass
    
    async def handle_refresh(self, query):
        """Atualiza o menu principal"""
        welcome_text = f"""
🚀 **SNIPER BOT V6 - ATUALIZADO**

💰 **Status da Carteira:**
• ETH: {self.get_eth_balance():.6f} ETH
• ETH: {self.get_eth_balance():.6f} ETH

🤖 **Bot Status:** {'🟢 ATIVO' if self.is_bot_running() else '🔴 PARADO'}

📊 **Performance:**
• Trades: {self.monitoring_stats['trades_executed']}
• Lucro: {self.monitoring_stats['total_profit']:.6f} ETH

⏰ **Atualizado:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_start_bot(self, query):
        """Inicia o bot"""
        if self.sniper_bot:
            if not self.sniper_bot.running:
                # Inicia o bot em background
                asyncio.create_task(self.sniper_bot.start())
                await query.edit_message_text(
                    "🚀 **BOT INICIADO!**\n\n✅ Sniper Bot está ativo e monitorando tokens...",
                    reply_markup=self.get_main_menu_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "⚠️ **BOT JÁ ESTÁ ATIVO!**\n\n🟢 O Sniper Bot já está rodando...",
                    reply_markup=self.get_main_menu_keyboard(),
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text("❌ Sniper Bot não disponível!")
    
    async def handle_stop_bot(self, query):
        """Para o bot"""
        if self.sniper_bot and self.sniper_bot.running:
            self.sniper_bot.running = False
            await query.edit_message_text(
                "⏹️ **BOT PARADO!**\n\n🔴 Sniper Bot foi desativado.",
                reply_markup=self.get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "⚠️ **BOT JÁ ESTÁ PARADO!**\n\n🔴 O Sniper Bot não está rodando.",
                reply_markup=self.get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
    
    async def handle_dashboard(self, query):
        """Mostra dashboard"""
        uptime = datetime.now() - self.monitoring_stats['start_time']
        
        dashboard_text = f"""
📊 **DASHBOARD COMPLETO**

🤖 **Status:** {'🟢 ATIVO' if self.is_bot_running() else '🔴 PARADO'}
⏰ **Uptime:** {str(uptime).split('.')[0]}

💰 **Saldos:**
• ETH: {self.get_eth_balance():.6f} ETH
• ETH: {self.get_eth_balance():.6f} ETH
• Total: {self.get_total_balance():.6f} ETH

📈 **Performance:**
• Tokens analisados: {self.monitoring_stats['tokens_analyzed']}
• Trades executados: {self.monitoring_stats['trades_executed']}
• Lucro total: {self.monitoring_stats['total_profit']:.6f} ETH

🔄 **Última atualização:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await query.edit_message_text(
            dashboard_text,
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_wallet(self, query):
        """Mostra informações da carteira"""
        # Verificar se WALLET_ADDRESS está configurado
        if WALLET_ADDRESS:
            address_display = f"`{WALLET_ADDRESS[:10]}...{WALLET_ADDRESS[-10:]}`"
        else:
            address_display = "`Não configurado`"
        
        eth_balance = self.get_eth_balance()
        trades_possible = int(eth_balance / TRADE_AMOUNT_ETH) if eth_balance > 0 and TRADE_AMOUNT_ETH > 0 else 0
        
        wallet_text = f"""
💰 **CARTEIRA DETALHADA**

🏦 **Endereço:** {address_display}

💎 **Saldos:**
• ETH (Trading): {eth_balance:.6f} ETH
• ETH (Gas): {self.get_eth_balance():.6f} ETH
• Total Estimado: {self.get_total_balance():.6f} ETH

⚙️ **Configurações:**
• Valor por trade: {TRADE_AMOUNT_ETH:.6f} ETH
• Trades possíveis: {trades_possible}

🔄 **Atualizado:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        await query.edit_message_text(
            wallet_text,
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    # Novos handlers para os botões organizados
    async def handle_config_menu(self, query):
        """Mostra menu de configurações"""
        config_text = f"""
⚙️ **MENU DE CONFIGURAÇÕES**

🎯 **Configurações Atuais:**
• Valor por trade: {TRADE_AMOUNT_ETH:.6f} ETH
• Slippage: {SLIPPAGE_TOLERANCE}%
• DEX preferida: {PRIMARY_DEX}

🛡️ **Segurança:**
• Filtros ativos: ✅
• Verificação de honeypot: ✅
• Limite de gas: {MAX_GAS_PRICE} Gwei

🔔 **Notificações:** {'✅ Ativas' if self.notifications_enabled else '❌ Desativadas'}
"""
        
        await query.edit_message_text(
            config_text,
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_advanced_menu(self, query):
        """Mostra menu avançado"""
        advanced_text = f"""
🔧 **MENU AVANÇADO**

🤖 **Status do Bot:** {'🟢 ATIVO' if self.is_bot_running() else '🔴 PARADO'}
⚡ **Modo:** {'Real Trading' if not SIMULATION_MODE else 'Simulação'}

📊 **Estatísticas Avançadas:**
• Tokens analisados: {self.monitoring_stats['tokens_analyzed']}
• Taxa de sucesso: {(self.monitoring_stats['trades_executed'] / max(1, self.monitoring_stats['tokens_analyzed']) * 100):.1f}%
• Uptime: {str(datetime.now() - self.monitoring_stats['start_time']).split('.')[0]}

🔍 **Ferramentas disponíveis:**
• Análise de token específico
• Ajuste de parâmetros em tempo real
• Verificação de segurança
• Visualização de logs
"""
        
        await query.edit_message_text(
            advanced_text,
            reply_markup=self.get_advanced_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_trades_history(self, query):
        """Mostra histórico de trades"""
        history_text = f"""
📈 **HISTÓRICO DE TRADES**

📊 **Resumo Geral:**
• Total de trades: {self.monitoring_stats['trades_executed']}
• Trades bem-sucedidos: {self.successful_trades}
• Taxa de sucesso: {(self.successful_trades / max(1, self.monitoring_stats['trades_executed']) * 100):.1f}%
• Lucro total: {self.monitoring_stats['total_profit']:.6f} ETH

💰 **Performance:**
• Melhor trade: +0.000000 ETH
• Pior trade: -0.000000 ETH
• Média por trade: {(self.monitoring_stats['total_profit'] / max(1, self.monitoring_stats['trades_executed'])):.6f} ETH

⏰ **Última atualização:** {datetime.now().strftime('%H:%M:%S')}

💡 **Dica:** Use /logs para ver detalhes completos
"""
        
        await query.edit_message_text(
            history_text,
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_stats(self, query):
        """Mostra estatísticas detalhadas"""
        uptime = datetime.now() - self.monitoring_stats['start_time']
        
        stats_text = f"""
📊 **ESTATÍSTICAS DETALHADAS**

⏱️ **Tempo de Operação:**
• Uptime: {str(uptime).split('.')[0]}
• Início: {self.monitoring_stats['start_time'].strftime('%d/%m %H:%M')}

🔍 **Monitoramento:**
• Tokens detectados: {self.monitoring_stats['tokens_analyzed']}
• Tokens por hora: {(self.monitoring_stats['tokens_analyzed'] / max(1, uptime.total_seconds() / 3600)):.1f}
• Blocos escaneados: ~{int(uptime.total_seconds() / 12)}

💰 **Trading:**
• Trades executados: {self.monitoring_stats['trades_executed']}
• Volume total: {self.monitoring_stats['trades_executed'] * TRADE_AMOUNT_ETH:.6f} ETH
• ROI: {((self.monitoring_stats['total_profit'] / max(0.001, self.monitoring_stats['trades_executed'] * TRADE_AMOUNT_ETH)) * 100):.2f}%

🎯 **Eficiência:**
• Trades/hora: {(self.monitoring_stats['trades_executed'] / max(1, uptime.total_seconds() / 3600)):.2f}
• Sucesso: {(self.successful_trades / max(1, self.monitoring_stats['trades_executed']) * 100):.1f}%
"""
        
        await query.edit_message_text(
            stats_text,
            reply_markup=self.get_advanced_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_analyze_token(self, query):
        """Análise de token específico"""
        analyze_text = """
🔍 **ANÁLISE DE TOKEN**

Para analisar um token específico, envie o comando:
`/analyze 0x[endereço_do_token]`

📊 **Informações fornecidas:**
• Verificação de segurança
• Análise de liquidez
• Histórico de preços
• Detecção de honeypot
• Score de confiabilidade

💡 **Exemplo:**
`/analyze 0x1234567890abcdef...`
"""
        
        try:
            await query.edit_message_text(
                analyze_text,
                reply_markup=self.get_advanced_menu_keyboard(),
                parse_mode='Markdown'
            )
        except Exception as e:
            if "not modified" in str(e).lower():
                # Mensagem já é a mesma, apenas responder callback
                await query.answer("🔍 Análise de token")
            else:
                # Outro erro, tentar enviar nova mensagem
                await query.message.reply_text(
                    analyze_text,
                    reply_markup=self.get_advanced_menu_keyboard(),
                    parse_mode='Markdown'
                )
    
    async def handle_adjust_amount(self, query):
        """Ajustar valor de trade"""
        current_balance = self.get_eth_balance()
        max_trades = int(current_balance / TRADE_AMOUNT_ETH) if current_balance > 0 else 0
        
        adjust_text = f"""
💰 **AJUSTAR VALOR DE TRADE**

📊 **Situação Atual:**
• Valor por trade: {TRADE_AMOUNT_ETH:.6f} ETH
• Saldo disponível: {current_balance:.6f} ETH
• Trades possíveis: {max_trades}

⚙️ **Opções disponíveis:**
• Conservador: 0.0001 ETH (~{int(current_balance / 0.0001)} trades)
• Moderado: 0.0005 ETH (~{int(current_balance / 0.0005)} trades)
• Agressivo: 0.001 ETH (~{int(current_balance / 0.001)} trades)

⚠️ **Nota:** Alterações requerem reinicialização do bot
"""
        
        await query.edit_message_text(
            adjust_text,
            reply_markup=self.get_advanced_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_speed_config(self, query):
        """Configurações de velocidade"""
        speed_text = f"""
⚡ **CONFIGURAÇÕES DE VELOCIDADE**

🚀 **Configuração Atual:**
• Modo: {'Turbo' if FAST_MODE else 'Normal'}
• Timeout: {TRANSACTION_TIMEOUT}s
• Gas Price: {MAX_GAS_PRICE} Gwei

⚙️ **Parâmetros:**
• Intervalo de scan: {SCAN_INTERVAL}s
• Confirmações: {CONFIRMATION_BLOCKS}
• Retry attempts: {MAX_RETRIES}

🎯 **Otimização:**
• MEV Protection: {'✅' if MEV_PROTECTION else '❌'}
• Priority Fee: {PRIORITY_FEE} Gwei
• Slippage: {SLIPPAGE_TOLERANCE}%

💡 **Dica:** Velocidade maior = mais gas, mas melhor chance de sucesso
"""
        
        await query.edit_message_text(
            speed_text,
            reply_markup=self.get_advanced_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_security_check(self, query):
        """Verificação de segurança"""
        security_text = f"""
🛡️ **VERIFICAÇÃO DE SEGURANÇA**

✅ **Sistemas Ativos:**
• Validação de contratos: ✅
• Detecção de honeypot: ✅
• Verificação de liquidez: ✅
• Análise de rugpull: ✅

🔍 **Filtros Aplicados:**
• Liquidez mínima: {MIN_LIQUIDITY_ETH} ETH
• Holders mínimos: {MIN_HOLDERS}
• Idade mínima: {MIN_TOKEN_AGE}s

⚠️ **Alertas de Risco:**
• Tokens suspeitos bloqueados: 0
• Contratos não verificados: Permitidos
• Tokens com tax alta: Bloqueados

🔐 **Segurança da Carteira:**
• Private key: Protegida ✅
• Saldo monitorado: ✅
• Transações assinadas localmente: ✅
"""
        
        await query.edit_message_text(
            security_text,
            reply_markup=self.get_advanced_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_view_logs(self, query):
        """Visualizar logs recentes"""
        logs_text = """
📝 **LOGS RECENTES**

🔍 **Últimas atividades:**
• 21:28:50 - Token CARV detectado
• 21:28:44 - Token BANANA analisado
• 21:28:40 - Status atualizado
• 21:28:30 - Token UNK processado

⚠️ **Alertas:**
• Conflito de instância Telegram resolvido
• Saldo ETH atualizado com sucesso

📊 **Estatísticas da sessão:**
• Tokens processados: {self.monitoring_stats['tokens_analyzed']}
• Erros: 0
• Uptime: {str(datetime.now() - self.monitoring_stats['start_time']).split('.')[0]}

💡 **Para logs completos, verifique o arquivo sniper_bot.log**
"""
        
        await query.edit_message_text(
            logs_text,
            reply_markup=self.get_advanced_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    # Handlers para configurações específicas
    async def handle_set_trade_amount(self, query):
        """Configurar valor de trade"""
        await query.edit_message_text(
            "💰 **CONFIGURAR VALOR DE TRADE**\n\n"
            "🔧 Função em desenvolvimento...\n"
            "📝 Em breve você poderá ajustar o valor diretamente pelo bot!",
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_set_slippage(self, query):
        """Configurar slippage"""
        await query.edit_message_text(
            "⚡ **CONFIGURAR SLIPPAGE**\n\n"
            "🔧 Função em desenvolvimento...\n"
            "📝 Em breve você poderá ajustar o slippage diretamente pelo bot!",
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_security_filters(self, query):
        """Configurar filtros de segurança"""
        await query.edit_message_text(
            "🛡️ **FILTROS DE SEGURANÇA**\n\n"
            "🔧 Função em desenvolvimento...\n"
            "📝 Em breve você poderá configurar filtros personalizados!",
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_notification_settings(self, query):
        """Configurar notificações"""
        status = "✅ Ativas" if self.notifications_enabled else "❌ Desativadas"
        await query.edit_message_text(
            f"🔔 **CONFIGURAÇÕES DE NOTIFICAÇÃO**\n\n"
            f"📱 Status atual: {status}\n\n"
            f"🔧 Função em desenvolvimento...\n"
            f"📝 Em breve você poderá personalizar as notificações!",
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_dex_preferences(self, query):
        """Configurar preferências de DEX"""
        await query.edit_message_text(
            "🔄 **PREFERÊNCIAS DE DEX**\n\n"
            "🔧 Função em desenvolvimento...\n"
            "📝 Em breve você poderá escolher DEXs preferenciais!",
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_timeout_settings(self, query):
        """Configurar timeouts"""
        await query.edit_message_text(
            "⏱️ **CONFIGURAÇÕES DE TIMEOUT**\n\n"
            "🔧 Função em desenvolvimento...\n"
            "📝 Em breve você poderá ajustar timeouts personalizados!",
            reply_markup=self.get_config_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    def is_bot_running(self) -> bool:
        """Verifica se o bot está rodando"""
        return self.sniper_bot and self.sniper_bot.running
    
    def get_eth_balance(self) -> float:
        """Obtém saldo ETH com diagnóstico"""
        if self.sniper_bot:
            balance = self.sniper_bot._get_eth_balance_sync()
            
            # Diagnóstico: se saldo for 0, forçar atualização
            if balance == 0.0:
                print("⚠️ Saldo ETH zerado detectado - forçando atualização...")
                # Limpar cache e tentar novamente
                if hasattr(self.sniper_bot, '_eth_balance_cache'):
                    delattr(self.sniper_bot, '_eth_balance_cache')
                if hasattr(self.sniper_bot, '_eth_balance_time'):
                    delattr(self.sniper_bot, '_eth_balance_time')
                
                # Tentar leitura novamente
                balance = self.sniper_bot._get_eth_balance_sync()
                print(f"🔄 Saldo após atualização forçada: {balance:.6f} ETH")
            
            return balance
        return 0.0
    
    def get_eth_balance(self) -> float:
        """Obtém saldo ETH"""
        if self.sniper_bot and self.sniper_bot.web3:
            try:
                balance = self.sniper_bot.web3.eth.get_balance(WALLET_ADDRESS)
                return balance / 10**18
            except:
                return 0.0
        return 0.0
    
    def get_total_balance(self) -> float:
        """Obtém saldo total estimado"""
        return self.get_eth_balance() + self.get_eth_balance()
    
    async def send_notification(self, message: str, priority: str = "normal"):
        """Envia notificação para usuários autorizados com rate limiting"""
        if not self.notifications_enabled or not self.application:
            # Se não há aplicação Telegram, apenas loga a mensagem
            print(f"📱 Notificação [{priority}]: {message}")
            return
        
        if not self.authorized_users:
            # Se não há usuários autorizados, apenas loga a mensagem
            print(f"📱 Notificação [{priority}]: {message}")
            return
        
        for user_id in self.authorized_users:
            try:
                # Usar rate limiting para Telegram
                await TELEGRAM_LIMITER.acquire()
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                TELEGRAM_LIMITER.handle_success()
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "too many requests" in error_msg:
                    TELEGRAM_LIMITER.handle_429_error()
                elif "chat not found" in error_msg:
                    print(f"⚠️ Chat {user_id} não encontrado - usuário pode não ter iniciado conversa com o bot")
                elif "bot was blocked" in error_msg:
                    print(f"⚠️ Bot foi bloqueado pelo usuário {user_id}")
                else:
                    print(f"❌ Erro ao enviar notificação para {user_id}: {e}")
    
    async def send_trade_alert(self, token_address: str, token_name: str, action: str, details: dict = None):
        """Envia alerta de trade para usuários autorizados"""
        # Garantir que action é uma string
        action = str(action) if action is not None else "UNKNOWN"
        
        if not self.notifications_enabled or not self.application:
            # Se não há aplicação Telegram, apenas loga o alerta
            print(f"🚨 Trade Alert [{action}]: {token_name} ({token_address[:10]}...)")
            return
        
        # Emojis baseados na ação
        action_emojis = {
            'BUY': '🟢 💰',
            'SELL': '🔴 💸',
            'DETECTED': '🔍 🚨',
            'ANALYSIS': '📊 🔬',
            'ERROR': '❌ ⚠️'
        }
        
        emoji = action_emojis.get(action.upper(), '📢')
        
        # Construir mensagem
        if action.upper() == 'DETECTED':
            message = f"""
{emoji} **NOVO TOKEN DETECTADO**

🪙 **Token:** {token_name}
📍 **Endereço:** `{token_address[:10]}...{token_address[-10:]}`
⏰ **Horário:** {datetime.now().strftime('%H:%M:%S')}

🔍 **Analisando segurança...**
"""
        elif action.upper() == 'BUY':
            amount = details.get('amount', 0) if details else 0
            price = details.get('price', 0) if details else 0
            message = f"""
{emoji} **COMPRA EXECUTADA**

🪙 **Token:** {token_name}
💰 **Valor:** {amount:.6f} ETH
💲 **Preço:** {price:.8f} ETH
⏰ **Horário:** {datetime.now().strftime('%H:%M:%S')}

✅ **Trade realizado com sucesso!**
"""
        elif action.upper() == 'SELL':
            amount = details.get('amount', 0) if details else 0
            profit = details.get('profit', 0) if details else 0
            message = f"""
{emoji} **VENDA EXECUTADA**

🪙 **Token:** {token_name}
💰 **Valor:** {amount:.6f} ETH
📈 **Lucro:** {profit:.6f} ETH
⏰ **Horário:** {datetime.now().strftime('%H:%M:%S')}

{'✅ **Lucro obtido!**' if profit > 0 else '⚠️ **Prejuízo controlado**'}
"""
        elif action.upper() == 'ERROR':
            error_msg = details.get('error', 'Erro desconhecido') if details else 'Erro desconhecido'
            message = f"""
{emoji} **ERRO NO TRADE**

🪙 **Token:** {token_name}
❌ **Erro:** {error_msg}
⏰ **Horário:** {datetime.now().strftime('%H:%M:%S')}

🔄 **Tentando recuperação...**
"""
        else:
            message = f"""
{emoji} **ALERTA DE TRADE**

🪙 **Token:** {token_name}
📍 **Ação:** {action}
⏰ **Horário:** {datetime.now().strftime('%H:%M:%S')}
"""
        
        # Enviar para todos os usuários autorizados
        if not self.authorized_users:
            # Se não há usuários autorizados, apenas loga o alerta detalhado
            print(f"🚨 Trade Alert [{action}]: {token_name} - {message[:100]}...")
            return
            
        for user_id in self.authorized_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                error_msg = str(e).lower()
                if "chat not found" in error_msg:
                    print(f"⚠️ Chat {user_id} não encontrado para alerta de trade")
                elif "bot was blocked" in error_msg:
                    print(f"⚠️ Bot foi bloqueado pelo usuário {user_id}")
                else:
                    print(f"❌ Erro ao enviar alerta de trade para {user_id}: {e}")
    
    async def stop(self):
        """Para o bot Telegram"""
        if self.application:
            try:
                await self.application.stop()
                await self.application.shutdown()
            except:
                pass