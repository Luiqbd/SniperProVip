#!/usr/bin/env python3
"""
🚀 SNIPER PRO VIP - TELEGRAM BOT ULTIMATE
Sistema avançado com botões inline funcionando 100%
"""

import asyncio
import requests
import json
import re
import os
import threading
import time
from typing import Dict, Optional, Callable
from config import *

class UltimateTelegramBot:
    """🤖 Bot de Telegram Ultimate com botões inline funcionando"""
    
    def __init__(self, sniper_bot_ref=None):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN') or TELEGRAM_BOT_TOKEN
        self.authorized_users = []
        self.sniper_bot = sniper_bot_ref
        
        # Processar usuários autorizados
        users_str = os.getenv('TELEGRAM_CHAT_ID') or TELEGRAM_CHAT_ID
        if users_str:
            for user_id in users_str.split(','):
                try:
                    user_id = int(user_id.strip())
                    if user_id > 0:
                        self.authorized_users.append(user_id)
                except:
                    pass
        
        self.enabled = bool(self.token and self.authorized_users)
        self.last_update_id = 0
        self.polling_thread = None
        self.running = False
        
        if not self.enabled:
            print("⚠️ Telegram bot desabilitado")
        else:
            print(f"✅🤖 Telegram Ultimate inicializado para {len(self.authorized_users)} usuário(s)")
            # Enviar mensagem inicial
            self.send_initial_message()
    
    def send_initial_message(self):
        """Envia mensagem de boas-vindas"""
        text = """
🎯 <b>SNIPER PRO VIP ULTIMATE</b>

✅ <i>Bot inicializado com sucesso!</i>

🔗 <b>Conectado à Base Network</b>
💰 <b>Saldos:</b> Verificando...

⏳ <b>Aguardando comandos...</b>

Use os botões abaixo ou comandos:
/start - Menu principal
/status - Ver status
/saldo - Ver saldos
"""
        self.send_message_sync(text)
    
    def send_message_sync(self, text: str, reply_markup: dict = None, user_id: int = None):
        """Envia mensagem síncrona"""
        if not self.enabled:
            print(f"📱 [Mock] {text[:50]}...")
            return
        
        targets = [user_id] if user_id else self.authorized_users
        
        for uid in targets:
            try:
                payload = {
                    "chat_id": uid,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                if reply_markup:
                    payload["reply_markup"] = json.dumps(reply_markup)
                
                response = requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json=payload,
                    timeout=15
                )
                
                if response.status_code != 200:
                    print(f"❌ Erro Telegram: {response.text[:100]}")
                    
            except Exception as e:
                print(f"❌ Erro ao enviar: {e}")
    
    def edit_message_sync(self, text: str, reply_markup: dict = None, user_id: int = None, message_id: int = None):
        """Edita mensagem existente"""
        if not self.enabled or not user_id or not message_id:
            return
        
        try:
            payload = {
                "chat_id": user_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            
            requests.post(
                f"https://api.telegram.org/bot{self.token}/editMessageText",
                json=payload,
                timeout=15
            )
        except:
            pass
    
    def answer_callback_sync(self, callback_id: str, text: str = None, show_alert: bool = False):
        """Responde ao callback"""
        if not self.enabled:
            return
        
        try:
            payload = {
                "callback_query_id": callback_id
            }
            if text:
                payload["text"] = text
            if show_alert:
                payload["show_alert"] = True
            
            requests.post(
                f"https://api.telegram.org/bot{self.token}/answerCallbackQuery",
                json=payload,
                timeout=10
            )
        except:
            pass
    
    # ==================== KEYBOARDS AVANÇADOS ====================
    
    def get_main_keyboard(self):
        """🎛️ Menu Principal - Inline Keyboard"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🚀 INICIAR SNIPER", "callback_data": "cmd_start"},
                    {"text": "⏹️ PARAR", "callback_data": "cmd_stop"}
                ],
                [
                    {"text": "💰 SALDOS", "callback_data": "cmd_saldo"},
                    {"text": "📊 STATUS", "callback_data": "cmd_status"}
                ],
                [
                    {"text": "📈 HISTÓRICO", "callback_data": "cmd_history"},
                    {"text": "⚙️ CONFIG", "callback_data": "cmd_config"}
                ],
                [
                    {"text": "🎯 ESTRATÉGIA", "callback_data": "cmd_strategy"},
                    {"text": "🔄 ATUALIZAR", "callback_data": "cmd_refresh"}
                ],
                [
                    {"text": "🆘 AJUDA", "callback_data": "cmd_help"}
                ]
            ]
        }
    
    def get_status_keyboard(self):
        """📊 Keyboard de Status"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Atualizar", "callback_data": "cmd_status"},
                    {"text": "💰 Saldos", "callback_data": "cmd_saldo"}
                ],
                [
                    {"text": "🚀 Iniciar", "callback_data": "cmd_start"},
                    {"text": "⏹️ Parar", "callback_data": "cmd_stop"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "cmd_menu"}
                ]
            ]
        }
    
    def get_strategy_keyboard(self):
        """🎯 Keyboard de Estratégia"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔥 AGRESSIVO", "callback_data": "str_aggressive"},
                    {"text": "📊 NORMAL", "callback_data": "str_normal"},
                    {"text": "🛡️ CONSERVADOR", "callback_data": "str_conservative"}
                ],
                [
                    {"text": "💰 +25%", "callback_data": "str_high"},
                    {"text": "💵 +10%", "callback_data": "str_medium"},
                    {"text": "💎 +5%", "callback_data": "str_low"}
                ],
                [
                    {"text": "⚡ Quick Profit: ON", "callback_data": "str_quick"},
                    {"text": "🎯 Auto Scale: ON", "callback_data": "str_scale"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "cmd_menu"}
                ]
            ]
        }
    
    def get_config_keyboard(self):
        """⚙️ Keyboard de Configurações"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Scan Interval", "callback_data": "cfg_scan"},
                    {"text": "💧 Slippage", "callback_data": "cfg_slippage"}
                ],
                [
                    {"text": "💵 Trade Amount", "callback_data": "cfg_trade"},
                    {"text": "🎯 Profit Target", "callback_data": "cfg_profit"}
                ],
                [
                    {"text": "🛡️ MEV Protection", "callback_data": "cfg_mev"},
                    {"text": "🐕 Memecoin Mode", "callback_data": "cfg_meme"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "cmd_menu"}
                ]
            ]
        }
    
    def get_balance_keyboard(self):
        """💰 Keyboard de Saldos"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Atualizar", "callback_data": "cmd_saldo"},
                    {"text": "📊 Status", "callback_data": "cmd_status"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "cmd_menu"}
                ]
            ]
        }
    
    def get_history_keyboard(self):
        """📈 Keyboard de Histórico"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Atualizar", "callback_data": "cmd_history"},
                    {"text": "📊 Trades", "callback_data": "cmd_trades"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "cmd_menu"}
                ]
            ]
        }
    
    def get_help_keyboard(self):
        """🆘 Keyboard de Ajuda"""
        return {
            "inline_keyboard": [
                [
                    {"text": "📖 Comandos", "callback_data": "help_cmds"},
                    {"text": "💡 Estratégia", "callback_data": "help_strat"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "cmd_menu"}
                ]
            ]
        }
    
    # ==================== HANDLERS ====================
    
    async def handle_callback(self, callback_data: str, callback_id: str, user_id: int, message_id: int = None):
        """📲 Processa todos os callbacks"""
        
        # Primeiro, responder ao callback para remover o "loading"
        self.answer_callback_sync(callback_id, text="✅ Processando...")
        
        if user_id not in self.authorized_users:
            self.answer_callback_sync(callback_id, text="❌ Acesso negado!", show_alert=True)
            return
        
        callback_data = callback_data.lower()
        
        # ═══════════════════════════════════════════
        # MENU PRINCIPAL
        # ═══════════════════════════════════════════
        if callback_data == "cmd_menu":
            text = self.get_main_menu_text()
            self.edit_message_sync(text, self.get_main_keyboard(), user_id, message_id)
        
        # ═══════════════════════════════════════════
        # COMANDOS PRINCIPAIS
        # ═══════════════════════════════════════════
        elif callback_data == "cmd_start":
            await self.cmd_start(user_id, message_id)
        
        elif callback_data == "cmd_stop":
            await self.cmd_stop(user_id, message_id)
        
        elif callback_data == "cmd_saldo":
            await self.cmd_saldo(user_id, message_id)
        
        elif callback_data == "cmd_status":
            await self.cmd_status(user_id, message_id)
        
        elif callback_data == "cmd_history":
            await self.cmd_history(user_id, message_id)
        
        elif callback_data == "cmd_config":
            await self.cmd_config(user_id, message_id)
        
        elif callback_data == "cmd_strategy":
            await self.cmd_strategy(user_id, message_id)
        
        elif callback_data == "cmd_refresh":
            text = self.get_main_menu_text()
            self.edit_message_sync(text, self.get_main_keyboard(), user_id, message_id)
        
        elif callback_data == "cmd_help":
            text = self.get_help_text()
            self.edit_message_sync(text, self.get_help_keyboard(), user_id, message_id)
        
        # ═══════════════════════════════════════════
        # ESTRATÉGIA
        # ═══════════════════════════════════════════
        elif callback_data.startswith("str_"):
            await self.cmd_strategy_set(callback_data, user_id, message_id)
        
        # ═══════════════════════════════════════════
        # CONFIGURAÇÕES
        # ═══════════════════════════════════════════
        elif callback_data.startswith("cfg_"):
            await self.cmd_config_set(callback_data, user_id, message_id)
        
        # ═══════════════════════════════════════════
        # AJUDA
        # ═══════════════════════════════════════════
        elif callback_data == "help_cmds":
            text = self.get_commands_text()
            self.edit_message_sync(text, self.get_help_keyboard(), user_id, message_id)
        
        elif callback_data == "help_strat":
            text = self.get_strat_help_text()
            self.edit_message_sync(text, self.get_help_keyboard(), user_id, message_id)
    
    # ==================== TEXTOS ====================
    
    def get_main_menu_text(self) -> str:
        """📋 Texto do Menu Principal"""
        status = "🟢 ATIVO" if (self.sniper_bot and getattr(self.sniper_bot, 'running', False)) else "🔴 INATIVO"
        
        return f"""
🎯 <b>SNIPER PRO VIP ULTIMATE</b>

<b>Status:</b> {status}
<b>Rede:</b> Base Network 🔵

<i>Selecione uma opção:</i>
"""
    
    def get_help_text(self) -> str:
        """📖 Texto de Ajuda"""
        return f"""
🆘 <b>AJUDA - SNIPER PRO VIP</b>

<b>Sobre o Bot:</b>
Este é um bot de sniper para a Base Network que detecta novos tokens e executa trades automaticamente.

<b>Botões:</b>
• <b>🚀 INICIAR</b> - Inicia o sniper
• <b>⏹️ PARAR</b> - Para o sniper
• <b>💰 SALDOS</b> - Verifica ETH/WETH
• <b>📊 STATUS</b> - Verifica status
• <b>📈 HISTÓRICO</b> - Ver trades
• <b>⚙️ CONFIG</b> - Configurações
• <b>🎯 ESTRATÉGIA</b> - Altera estratégia

<b>Comandos:</b>
/start - Menu
/status - Status
/saldo - Saldos
/iniciar - Iniciar
/parar - Parar
"""
    
    def get_commands_text(self) -> str:
        """📝 Lista de Comandos"""
        return f"""
📝 <b>COMANDOS DISPONÍVEIS</b>

<b>Principais:</b>
/start - Menu principal
/help - Ajuda
/status - Status do bot
/saldo - Ver saldos

<b>Controle:</b>
/iniciar - Iniciar sniper
/parar - Parar sniper

<b>Informações:</b>
/config - Configurações
/strategy - Estratégia
/history - Histórico trades
/trades - Ver trades

<b>Avançado:</b>
/test - Testar conexão
/debug - Debug info
"""
    
    def get_strat_help_text(self) -> str:
        """💡 Texto de Estratégia"""
        return f"""
💡 <b>GUIA DE ESTRATÉGIA</b>

<b>🔥 Modo AGRESSIVO:</b>
• Mais trades executados
• Score mínimo baixo
• Lucros rápidos
• Alto risco

<b>📊 Modo NORMAL:</b>
• Equilíbrio risco/retorno
• Score moderado
• Lucros constantes

<b>🛡️ Modo CONSERVADOR:</b>
• Poucos trades
• Score alto necessário
• Lucros seguros
• Baixo risco

<b>💰 Quick Profit:</b>
Vende automaticamente com 5-8% de lucro em menos de 30 segundos.

<b>🎯 Auto Scale:</b>
Aumenta automaticamente o valor do trade quando o saldo cresce.
"""
    
    # ==================== COMANDOS ====================
    
    async def cmd_start(self, user_id: int, message_id: int = None):
        """🚀 Inicia o sniper"""
        if self.sniper_bot:
            self.sniper_bot.running = True
            text = """
🚀 <b>SNIPER INICIADO!</b>

✅ <i>O bot está monitorando tokens...</i>

🔍 <i>Aguardando novos pares na Base Network...</i>
"""
            keyboard = self.get_status_keyboard()
        else:
            text = "❌ <b>Sniper não disponível!</b>"
            keyboard = self.get_main_keyboard()
        
        if message_id:
            self.edit_message_sync(text, keyboard, user_id, message_id)
        else:
            self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_stop(self, user_id: int, message_id: int = None):
        """⏹️ Para o sniper"""
        if self.sniper_bot:
            self.sniper_bot.running = False
            text = "⏹️ <b>SNIPER PARADO!</b>\n\n✅ <i>Bot停止了...</i>"
            keyboard = self.get_main_keyboard()
        else:
            text = "❌ <b>Sniper não disponível!</b>"
            keyboard = self.get_main_keyboard()
        
        if message_id:
            self.edit_message_sync(text, keyboard, user_id, message_id)
        else:
            self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_saldo(self, user_id: int, message_id: int = None):
        """💰 Mostra saldos"""
        try:
            if not self.sniper_bot or not self.sniper_bot.web3:
                text = "❌ <b>Sniper não conectado!</b>"
                keyboard = self.get_main_keyboard()
                if message_id:
                    self.edit_message_sync(text, keyboard, user_id, message_id)
                else:
                    self.send_message_sync(text, keyboard, user_id)
                return
            
            web3 = self.sniper_bot.web3
            
            # Saldo ETH
            eth_balance_wei = web3.eth.get_balance(WALLET_ADDRESS)
            eth_balance = float(web3.from_wei(eth_balance_wei, 'ether'))
            
            # Saldo WETH
            weth_contract = web3.eth.contract(
                address=WETH_ADDRESS,
                abi=[{
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }]
            )
            weth_balance_wei = weth_contract.functions.balanceOf(WALLET_ADDRESS).call()
            weth_balance = float(web3.from_wei(weth_balance_wei, 'ether'))
            
            total = eth_balance + weth_balance
            
            text = f"""
💰 <b>SALDOS - CARTEIRA</b>

<b>ETH (Gas):</b> {eth_balance:.6f} ETH
<b>WETH (Trade):</b> {weth_balance:.6f} WETH

<b>Total:</b> {total:.6f} ETH

💎 <i>Carteira:</i> <code>{WALLET_ADDRESS[:20]}...</code>
"""
            keyboard = self.get_balance_keyboard()
            
            if message_id:
                self.edit_message_sync(text, keyboard, user_id, message_id)
            else:
                self.send_message_sync(text, keyboard, user_id)
                
        except Exception as e:
            text = f"❌ Erro: {str(e)[:100]}"
            keyboard = self.get_balance_keyboard()
            if message_id:
                self.edit_message_sync(text, keyboard, user_id, message_id)
            else:
                self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_status(self, user_id: int, message_id: int = None):
        """📊 Mostra status"""
        try:
            if not self.sniper_bot:
                text = "❌ <b>Sniper não disponível!</b>"
                keyboard = self.get_main_keyboard()
                if message_id:
                    self.edit_message_sync(text, keyboard, user_id, message_id)
                else:
                    self.send_message_sync(text, keyboard, user_id)
                return
            
            running = "🟢 ATIVO" if self.sniper_bot.running else "🔴 INATIVO"
            trades = getattr(self.sniper_bot, 'trades_executed', 0)
            successes = getattr(self.sniper_bot, 'successful_trades', 0)
            profit = getattr(self.sniper_bot, 'total_profit', 0.0)
            
            # Saldos
            try:
                web3 = self.sniper_bot.web3
                eth_balance_wei = web3.eth.get_balance(WALLET_ADDRESS)
                eth_balance = float(web3.from_wei(eth_balance_wei, 'ether'))
                
                weth_contract = web3.eth.contract(
                    address=WETH_ADDRESS,
                    abi=[{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                )
                weth_balance_wei = weth_contract.functions.balanceOf(WALLET_ADDRESS).call()
                weth_balance = float(web3.from_wei(weth_balance_wei, 'ether'))
            except:
                eth_balance = 0
                weth_balance = 0
            
            text = f"""
📊 <b>STATUS DO SNIPER</b>

<b>Status:</b> {running}
<b>Rede:</b> Base Network 🔵

<b>📈 Trades:</b>
• Executados: {trades}
• Sucessos: {successes}
• Lucro: {profit:.6f} ETH

<b>💰 Saldos:</b>
• ETH: {eth_balance:.6f}
• WETH: {weth_balance:.6f}
• Total: {eth_balance + weth_balance:.6f}
"""
            keyboard = self.get_status_keyboard()
            
            if message_id:
                self.edit_message_sync(text, keyboard, user_id, message_id)
            else:
                self.send_message_sync(text, keyboard, user_id)
                
        except Exception as e:
            text = f"❌ Erro: {str(e)[:100]}"
            keyboard = self.get_status_keyboard()
            if message_id:
                self.edit_message_sync(text, keyboard, user_id, message_id)
            else:
                self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_history(self, user_id: int, message_id: int = None):
        """📈 Mostra histórico"""
        try:
            if not self.sniper_bot or not hasattr(self.sniper_bot, 'aggressive_strategy'):
                text = "📈 <b>HISTÓRICO</b>\n\n<i>Nenhum histórico disponível ainda.</i>"
                keyboard = self.get_history_keyboard()
                if message_id:
                    self.edit_message_sync(text, keyboard, user_id, message_id)
                else:
                    self.send_message_sync(text, keyboard, user_id)
                return
            
            strategy = self.sniper_bot.aggressive_strategy
            trades = len(strategy.trade_history)
            wins = strategy.successful_trades
            losses = strategy.failed_trades
            profit = sum(strategy.profit_history) if strategy.profit_history else 0
            
            text = f"""
📈 <b>HISTÓRICO DE TRADES</b>

<b>Total de Trades:</b> {trades}
<b>✅ Vitórias:</b> {wins}
<b>❌ Derrotas:</b> {losses}

<b>💰 Lucro Total:</b> {profit:.6f} ETH

<b>🏆 Taxa de Acerto:</b> {(wins/trades*100) if trades > 0 else 0:.1f}%
"""
            keyboard = self.get_history_keyboard()
            
            if message_id:
                self.edit_message_sync(text, keyboard, user_id, message_id)
            else:
                self.send_message_sync(text, keyboard, user_id)
                
        except Exception as e:
            text = f"❌ Erro: {str(e)[:100]}"
            keyboard = self.get_history_keyboard()
            if message_id:
                self.edit_message_sync(text, keyboard, user_id, message_id)
            else:
                self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_config(self, user_id: int, message_id: int = None):
        """⚙️ Mostra configurações"""
        text = f"""
⚙️ <b>CONFIGURAÇÕES</b>

<b>Rede:</b> Base Network (8453)

<b>💵 Trading:</b>
• Trade Amount: {TRADE_AMOUNT_WETH} WETH
• Slippage: {SLIPPAGE_TOLERANCE}%
• Profit Target: {TARGET_PROFIT_PERCENTAGE}%

<b>🛡️ Segurança:</b>
• Honeypot: {'✅' if ENABLE_HONEYPOT_CHECK else '❌'}
• MEV: {'✅' if ENABLE_MEV_PROTECTION else '❌'}

<b>🔥 Estratégia:</b>
• Modo: {'AGGRESSIVO' if AGGRESSIVE_TRADING else 'NORMAL'}
• Memecoin: {'✅' if MEMECOIN_MODE else '❌'}
• Quick Profit: {'✅' if QUICK_PROFIT_MODE else '❌'}
"""
        keyboard = self.get_config_keyboard()
        
        if message_id:
            self.edit_message_sync(text, keyboard, user_id, message_id)
        else:
            self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_strategy(self, user_id: int, message_id: int = None):
        """🎯 Mostra estratégia"""
        text = f"""
🎯 <b>ESTRATÉGIA ATUAL</b>

<b>Modo:</b> 🔥 AGRESSIVO

<b>Parâmetros:</b>
• Trade: {TRADE_AMOUNT_WETH} WETH
• Target: {TARGET_PROFIT_PERCENTAGE}%
• Stop Loss: 15%
• Quick Profit: 5%

<b>Escolha nova estratégia:</b>
"""
        keyboard = self.get_strategy_keyboard()
        
        if message_id:
            self.edit_message_sync(text, keyboard, user_id, message_id)
        else:
            self.send_message_sync(text, keyboard, user_id)
    
    async def cmd_strategy_set(self, callback_data: str, user_id: int, message_id: int):
        """🎯 Define estratégia"""
        strategy_map = {
            "str_aggressive": ("🔥 AGRESSIVO", "Modo agressivo ativado!"),
            "str_normal": ("📊 NORMAL", "Modo normal ativado!"),
            "str_conservative": ("🛡️ CONSERVADOR", "Modo conservador ativado!"),
            "str_high": ("💰 +25%", "Trade amount: 25%"),
            "str_medium": ("💵 +10%", "Trade amount: 10%"),
            "str_low": ("💎 +5%", "Trade amount: 5%"),
        }
        
        if callback_data in strategy_map:
            name, msg = strategy_map[callback_data]
            text = f"✅ <b>{msg}</b>"
            self.answer_callback_sync("", text=f"🎯 {name}")
        
        # Voltar para menu de estratégia
        await self.cmd_strategy(user_id, message_id)
    
    async def cmd_config_set(self, callback_data: str, user_id: int, message_id: int):
        """⚙️ Define configuração"""
        config_map = {
            "cfg_scan": ("🔄 Scan", "Intervalo de scan"),
            "cfg_slippage": ("💧 Slippage", "Slippage tolerance"),
            "cfg_trade": ("💵 Trade", "Valor por trade"),
            "cfg_profit": ("🎯 Profit", "Alvo de lucro"),
            "cfg_mev": ("🛡️ MEV", "Proteção MEV"),
            "cfg_meme": ("🐕 Meme", "Modo Memecoin"),
        }
        
        if callback_data in config_map:
            name, desc = config_map[callback_data]
            self.answer_callback_sync("", text=f"⚙️ {desc}")
        
        # Voltar para menu de config
        await self.cmd_config(user_id, message_id)
    
    # ==================== POLLING ====================
    
    async def handle_message(self, text: str, user_id: int):
        """💬 Processa mensagens/commands"""
        
        if user_id not in self.authorized_users:
            self.send_message_sync("❌ <b>Acesso negado!</b>", user_id=user_id)
            return
        
        text = text.lower().strip()
        
        # Comandos
        if text in ['/start', 'start', 'menu', '🔙']:
            await self.send_menu(user_id)
        
        elif text in ['/help', 'ajuda', 'help', '🆘']:
            text = self.get_help_text()
            self.send_message_sync(text, self.get_help_keyboard(), user_id)
        
        elif text in ['/status', 'status', '📊']:
            await self.cmd_status(user_id)
        
        elif text in ['/saldo', 'saldo', '💰', 'saldos']:
            await self.cmd_saldo(user_id)
        
        elif text in ['/iniciar', 'iniciar', 'start_sniper', '🚀', '/start_sniper']:
            await self.cmd_start(user_id)
        
        elif text in ['/parar', 'parar', 'stop_sniper', '⏹️', '/stop_sniper']:
            await self.cmd_stop(user_id)
        
        elif text in ['/history', 'historico', '📈', '/historico']:
            await self.cmd_history(user_id)
        
        elif text in ['/config', 'config', '⚙️', '/config']:
            await self.cmd_config(user_id)
        
        elif text in ['/strategy', 'strategy', '🎯', '/strategy']:
            await self.cmd_strategy(user_id)
        
        else:
            # Menu padrão
            await self.send_menu(user_id)
    
    async def send_menu(self, user_id: int):
        """📤 Envia menu principal"""
        text = self.get_main_menu_text()
        self.send_message_sync(text, self.get_main_keyboard(), user_id)
    
    def start_polling(self):
        """🔄 Inicia polling em background"""
        if not self.enabled:
            return
        
        self.running = True
        print("🔄 Starting polling loop...")
        
        def poll_loop():
            offset = None
            while self.running:
                try:
                    params = {"timeout": 25}
                    if offset:
                        params["offset"] = offset
                    
                    print("📡 Polling Telegram...")
                    response = requests.get(
                        f"https://api.telegram.org/bot{self.token}/getUpdates",
                        params=params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ok"):
                            updates = data.get("result", [])
                            if updates:
                                print(f"📬 Received {len(updates)} updates")
                            
                            for update in updates:
                                offset = update.get("update_id", 0) + 1
                                
                                # Callback Query (botões inline)
                                if "callback_query" in update:
                                    print(f"🔘 Callback received: {update}")
                                    cb = update["callback_query"]
                                    callback_id = cb.get("id")
                                    user_id = cb.get("from", {}).get("id")
                                    message_id = cb.get("message", {}).get("message_id")
                                    callback_data = cb.get("data", "")
                                    
                                    print(f"🔘 Processing callback: {callback_data} from user {user_id}")
                                    
                                    asyncio.run(self.handle_callback(callback_data, callback_id, user_id, message_id))
                                
                                # Mensagem/Comando
                                elif "message" in update:
                                    msg = update["message"]
                                    text = msg.get("text", "")
                                    user_id = msg.get("from", {}).get("id")
                                    
                                    if text:
                                        print(f"💬 Message: {text} from {user_id}")
                                        asyncio.run(self.handle_message(text, user_id))
                    
                except Exception as e:
                    print(f"⚠️ Polling error: {e}")
                    time.sleep(3)
        
        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
        print("✅🔄 Telegram polling iniciado")
    
    def stop_polling(self):
        """⏹️ Para polling"""
        self.running = False
    
    # ==================== COMPATIBILIDADE ====================
    
    async def send_notification(self, message: str, priority: str = "normal"):
        """📣 Envia notificação"""
        emoji = "🔔" if priority == "normal" else "🚨" if priority == "high" else "ℹ️"
        text = f"{emoji} <b>NOTIFICAÇÃO</b>\n\n{message}"
        self.send_message_sync(text)
    
    async def send_trade_alert(self, token_address: str, token_name: str, action: str, details: dict = None):
        """🚨 Alerta de trade"""
        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "📊"
        
        text = f"""
{emoji} <b>ALERTA DE TRADE</b>

<b>Token:</b> {token_name}
<b>Ação:</b> {action}
<b>Endereço:</b> <code>{token_address[:20]}...</code>
"""
        if details:
            if 'amount' in details:
                text += f"\n<b>Quantidade:</b> {details['amount']}"
            if 'price' in details:
                text += f"\n<b>Preço:</b> {details['price']}"
        
        keyboard = self.get_status_keyboard()
        self.send_message_sync(text, keyboard)
    
    async def send_status_update(self, status_data: dict):
        """📊 Status update"""
        status = status_data.get('status', 'Desconhecido')
        running = "🟢 ATIVO" if status == 'Rodando' else "🔴 INATIVO"
        
        text = f"""
📊 <b>STATUS ATUALIZADO</b>

<b>Status:</b> {running}
<b>Trades:</b> {status_data.get('trades_executed', 0)}
<b>Sucessos:</b> {status_data.get('successful_trades', 0)}
<b>Lucro:</b> {status_data.get('total_profit', '0')} ETH
<b>ETH:</b> {status_data.get('eth_balance', '0')}
<b>WETH:</b> {status_data.get('weth_balance', '0')}
"""
        keyboard = self.get_status_keyboard()
        self.send_message_sync(text, keyboard)
    
    async def start(self):
        """▶️ Inicia o bot"""
        # Iniciar polling em background
        self.start_polling()
        
        # Enviar mensagem inicial para todos os usuários
        import asyncio
        try:
            for user_id in self.authorized_users:
                await self.send_welcome_message(user_id)
        except Exception as e:
            print(f"Erro ao enviar mensagem inicial: {e}")
    
    async def send_welcome_message(self, user_id: int):
        """Envia mensagem de boas-vindas"""
        text = """
🎯 <b>SNIPER PRO VIP - ONLINE!</b>

✅ <i>O bot está funcionando!</i>

<b>Rede:</b> Base Network 🔵
<b>Status:</b> Monitorando...

<i>Use /start para ver o menu</i>
"""
        keyboard = self.get_main_keyboard()
        await self.send_message(text, reply_markup=keyboard, user_id=user_id)
    
    async def cleanup_and_disable_polling(self):
        """🧹 Limpa e para"""
        self.stop_polling()


# ==================== INSTÂNCIA GLOBAL ====================

_ultimate_telegram = None

def get_ultimate_telegram(sniper_bot=None):
    """🎯 Retorna instância do bot ultimate"""
    global _ultimate_telegram
    if _ultimate_telegram is None:
        _ultimate_telegram = UltimateTelegramBot(sniper_bot)
    elif sniper_bot:
        _ultimate_telegram.sniper_bot = sniper_bot
    return _ultimate_telegram
