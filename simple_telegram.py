#!/usr/bin/env python3
"""
Sistema Avançado de Telegram Bot para Sniper Pro VIP
Comandos e botões funcionando 100%
"""

import asyncio
import requests
import json
import re
import os
import threading
from typing import Dict, Optional, Callable
from config import *

class AdvancedTelegramBot:
    """Bot de Telegram avançado com botões e comandos funcionando"""
    
    def __init__(self, sniper_bot_ref=None):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN') or TELEGRAM_BOT_TOKEN
        self.authorized_users = []
        self.sniper_bot = sniper_bot_ref  # Referência ao bot principal
        
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
            print("⚠️ Telegram bot desabilitado - configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID")
        else:
            print(f"✅ Telegram Bot Avançado inicializado para {len(self.authorized_users)} usuário(s)")
    
    def set_sniper_bot(self, sniper_bot):
        """Define a referência do sniper bot"""
        self.sniper_bot = sniper_bot
    
    def escape_html(self, text: str) -> str:
        """Escapa caracteres HTML especiais"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def format_balance(self, balance_wei: int, decimals: int = 18) -> str:
        """Formata saldo para visualização"""
        return f"{balance_wei / (10**decimals):.6f}"
    
    async def send_message(self, text: str, parse_mode: str = "HTML", reply_markup: dict = None, user_id: int = None):
        """Envia mensagem para usuário(s) autorizado(s)"""
        if not self.enabled:
            print(f"📱 [Mock] {text}")
            return
        
        targets = [user_id] if user_id else self.authorized_users
        
        for uid in targets:
            try:
                payload = {
                    "chat_id": uid,
                    "text": text,
                    "parse_mode": parse_mode
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                
                response = requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json=payload,
                    timeout=15
                )
                
                if response.status_code != 200:
                    print(f"❌ Erro Telegram: {response.text[:100]}")
                    
            except Exception as e:
                print(f"❌ Erro ao enviar mensagem: {e}")
    
    def get_main_menu_keyboard(self):
        """Retorna teclado do menu principal"""
        return {
            "keyboard": [
                [{"text": "🔥 Iniciar Sniper", "callback_data": "start_sniper"}],
                [{"text": "⏹️ Parar Sniper", "callback_data": "stop_sniper"}],
                [{"text": "💰 Ver Saldos", "callback_data": "check_balances"}],
                [{"text": "📊 Ver Status", "callback_data": "check_status"}],
                [{"text": "📈 Histórico Trades", "callback_data": "check_history"}],
                [{"text": "⚙️ Configurações", "callback_data": "check_settings"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    
    def get_status_keyboard(self):
        """Retorna teclado de status com botões inline"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Atualizar", "callback_data": "status_refresh"},
                    {"text": "▶️ Iniciar", "callback_data": "sniper_start"},
                    {"text": "⏹️ Parar", "callback_data": "sniper_stop"}
                ],
                [
                    {"text": "💰 Saldos", "callback_data": "status_balances"},
                    {"text": "📈 Trades", "callback_data": "status_trades"}
                ],
                [
                    {"text": "🔙 Menu Principal", "callback_data": "main_menu"}
                ]
            ]
        }
    
    async def send_main_menu(self, user_id: int):
        """Envia menu principal"""
        text = """
<b>🔥 SNIPER PRO VIP - MENU PRINCIPAL</b>

<b>Bem-vindo ao seu bot de sniper!</b>

Selecione uma opção abaixo:
"""
        
        await self.send_message(text, reply_markup=self.get_main_menu_keyboard())
    
    async def handle_command(self, command: str, user_id: int) -> bool:
        """Processa comandos recebidos"""
        command = command.lower().strip()
        
        # Verificar autorização
        if user_id not in self.authorized_users:
            await self.send_message(f"❌ <b>Acesso negado!</b>\nVocê não está autorizado a usar este bot.", user_id=user_id)
            return True
        
        if command in ['/start', 'menu', 'início', 'start']:
            await self.send_main_menu(user_id)
            return True
        
        elif command in ['/help', 'ajuda', 'help']:
            text = """
<b>📖 AJUDA - SNIPER PRO VIP</b>

<b>Comandos disponíveis:</b>
/start - Menu principal
/saldo - Ver saldos da carteira
/status - Ver status do sniper
/iniciar - Iniciar o sniper
/parar - Parar o sniper
/historico - Ver histórico de trades
/config - Ver configurações

<b>Botões:</b>
Use os botões do menu para 控制o rápida.
"""
            await self.send_message(text, user_id=user_id)
            return True
        
        elif command in ['/saldo', 'saldo', '💰', 'saldos']:
            await self.show_balances(user_id)
            return True
        
        elif command in ['/status', 'status', '📊']:
            await self.show_status(user_id)
            return True
        
        elif command in ['/iniciar', 'iniciar', 'start_sniper', '🔥']:
            await self.start_sniper(user_id)
            return True
        
        elif command in ['/parar', 'parar', 'stop_sniper', '⏹️']:
            await self.stop_sniper(user_id)
            return True
        
        elif command in ['/historico', 'historico', 'history', '📈']:
            await self.show_history(user_id)
            return True
        
        elif command in ['/config', 'config', 'configurações', '⚙️']:
            await self.show_settings(user_id)
            return True
        
        return False
    
    async def show_balances(self, user_id: int):
        """Mostra saldos da carteira"""
        try:
            if not self.sniper_bot or not self.sniper_bot.web3:
                await self.send_message("❌ <b>Sniper não conectado!</b>\nInicie o sniper primeiro.", user_id=user_id)
                return
            
            web3 = self.sniper_bot.web3
            
            # Saldo ETH
            eth_balance_wei = web3.eth.get_balance(WALLET_ADDRESS)
            eth_balance = float(web3.from_wei(eth_balance_wei, 'ether'))
            
            # Saldo ETH
            weth_contract = web3.eth.contract(
                address=ETH_ADDRESS,
                abi=[{
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }]
            )
            eth_balance_wei = weth_contract.functions.balanceOf(WALLET_ADDRESS).call()
            eth_balance = float(web3.from_wei(eth_balance_wei, 'ether'))
            
            # Saldo total
            total_eth = eth_balance + eth_balance
            
            text = f"""
<b>💰 SALDOS DA CARTEIRA</b>

<b>ETH (Gas):</b> {eth_balance:.6f} ETH
<b>ETH (Trading):</b> {eth_balance:.6f} ETH

<b>Total:</b> {total_eth:.6f} ETH

<i>Carteira: <code>{WALLET_ADDRESS[:10]}...{WALLET_ADDRESS[-6:]}</code></i>
"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔄 Atualizar", "callback_data": "balances_refresh"}],
                    [{"text": "🔙 Menu", "callback_data": "main_menu"}]
                ]
            }
            
            await self.send_message(text, reply_markup=keyboard, user_id=user_id)
            
        except Exception as e:
            await self.send_message(f"❌ Erro ao buscar saldos:\n{str(e)[:200]}", user_id=user_id)
    
    async def show_status(self, user_id: int):
        """Mostra status do sniper"""
        try:
            if not self.sniper_bot:
                await self.send_message("❌ <b>Sniper não inicializado!</b>", user_id=user_id)
                return
            
            running = "🟢 <b>ATIVO</b>" if self.sniper_bot.running else "🔴 <b>INATIVO</b>"
            
            trades = self.sniper_bot.trades_executed
            successes = self.sniper_bot.successful_trades
            profit = self.sniper_bot.total_profit
            
            success_rate = (successes / trades * 100) if trades > 0 else 0
            
            # Posições ativas
            active_positions = 0
            if hasattr(self.sniper_bot, 'aggressive_strategy'):
                active_positions = len(self.sniper_bot.aggressive_strategy.current_positions)
            
            text = f"""
<b>📊 STATUS DO SNIPER</b>

<b>Status:</b> {running}
<b>Trades Executados:</b> {trades}
<b>Trades com Sucesso:</b> {successes}
<b>Taxa de Acerto:</b> {success_rate:.1f}%
<b>Lucro Total:</b> {profit:.6f} ETH
<b>Posições Ativas:</b> {active_positions}

<b>Estratégia:</b> {'🚀 Agressiva' if AGGRESSIVE_TRADING else '📊 Normal'}
<b>Modo:</b> {'🔥 Memecoin' if MEMECOIN_MODE else '💎 Padrão'}
"""
            
            keyboard = self.get_status_keyboard()
            await self.send_message(text, reply_markup=keyboard, user_id=user_id)
            
        except Exception as e:
            await self.send_message(f"❌ Erro ao buscar status:\n{str(e)[:200]}", user_id=user_id)
    
    async def start_sniper(self, user_id: int):
        """Inicia o sniper"""
        try:
            if not self.sniper_bot:
                await self.send_message("❌ <b>Sniper não inicializado!</b>", user_id=user_id)
                return
            
            if self.sniper_bot.running:
                await self.send_message("ℹ️ <b>O sniper já está ativo!</b>", user_id=user_id)
                return
            
            self.sniper_bot.running = True
            if hasattr(self.sniper_bot, 'token_monitor'):
                self.sniper_bot.token_monitor.start_monitoring()
            
            await self.send_message("""
✅ <b>SNIPER INICIADO!</b>

<b>O sniper está monitorando e pronto para comprar/vender!</b>

🔍 Detectando novos tokens...
⏳ Aguardando oportunidades...
""", user_id=user_id)
            
        except Exception as e:
            await self.send_message(f"❌ Erro ao iniciar sniper:\n{str(e)[:200]}", user_id=user_id)
    
    async def stop_sniper(self, user_id: int):
        """Para o sniper"""
        try:
            if not self.sniper_bot:
                await self.send_message("❌ <b>Sniper não inicializado!</b>", user_id=user_id)
                return
            
            if not self.sniper_bot.running:
                await self.send_message("ℹ️ <b>O sniper já está parado!</b>", user_id=user_id)
                return
            
            self.sniper_bot.running = False
            if hasattr(self.sniper_bot, 'token_monitor'):
                self.sniper_bot.token_monitor.stop_monitoring()
            
            await self.send_message("""
⏹️ <b>SNIPER PARADO!</b>

<b>O sniper foi desativado com sucesso.</b>

💡 Use /iniciar para ligar novamente.
""", user_id=user_id)
            
        except Exception as e:
            await self.send_message(f"❌ Erro ao parar sniper:\n{str(e)[:200]}", user_id=user_id)
    
    async def show_history(self, user_id: int):
        """Mostra histórico de trades"""
        try:
            if not self.sniper_bot:
                await self.send_message("❌ <b>Sniper não inicializado!</b>", user_id=user_id)
                return
            
            trades = self.sniper_bot.trades_executed
            successes = self.sniper_bot.successful_trades
            profit = self.sniper_bot.total_profit
            
            text = f"""
<b>📈 HISTÓRICO DE TRADES</b>

<b>Total de Trades:</b> {trades}
<b>Trades com Sucesso:</b> {successes}
<b>Trades Falhados:</b> {trades - successes}
<b>Lucro Total:</b> {profit:.6f} ETH

<i>Para mais detalhes, verifique os logs do bot.</i>
"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔄 Atualizar", "callback_data": "history_refresh"}],
                    [{"text": "🔙 Menu", "callback_data": "main_menu"}]
                ]
            }
            
            await self.send_message(text, reply_markup=keyboard, user_id=user_id)
            
        except Exception as e:
            await self.send_message(f"❌ Erro ao buscar histórico:\n{str(e)[:200]}", user_id=user_id)
    
    async def show_settings(self, user_id: int):
        """Mostra configurações"""
        try:
            text = f"""
<b>⚙️ CONFIGURAÇÕES DO SNIPER</b>

<b>Rede:</b> Base Network (8453)

<b>Trading:</b>
• Valor por trade: {TRADE_AMOUNT_ETH} ETH
• Slippage: {SLIPPAGE_TOLERANCE}%
• Lucro alvo: {TARGET_PROFIT_PERCENTAGE}%

<b>Segurança:</b>
• Honeypot Check: {'✅ Ativado' if ENABLE_HONEYPOT_CHECK else '❌ Desativado'}
• MEV Protection: {'✅ Ativado' if ENABLE_MEV_PROTECTION else '❌ Desativado'}

<b>Estratégia:</b>
• Modo Agressivo: {'🔥 Ativado' if AGGRESSIVE_TRADING else '📊 Normal'}
• Modo Memecoin: {'🐕 Ativado' if MEMECOIN_MODE else '❌ Desativado'}
• Modo Rápido: {'⚡ Ativado' if QUICK_PROFIT_MODE else '❌ Desativado'}

<b>Tokens Mínimos:</b>
• Liquidez: ${MIN_LIQUIDITY_USD}
• Score: {MIN_SCORE_TO_BUY}
"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Menu", "callback_data": "main_menu"}]
                ]
            }
            
            await self.send_message(text, reply_markup=keyboard, user_id=user_id)
            
        except Exception as e:
            await self.send_message(f"❌ Erro ao buscar configurações:\n{str(e)[:200]}", user_id=user_id)
    
    async def handle_callback(self, callback_data: str, user_id: int):
        """Processa callback de botões inline"""
        if user_id not in self.authorized_users:
            return
        
        callback_data = callback_data.lower()
        
        if callback_data == "main_menu":
            await self.send_main_menu(user_id)
        
        elif callback_data in ["status_refresh", "check_status"]:
            await self.show_status(user_id)
        
        elif callback_data in ["balances_refresh", "check_balances", "sniper_balances"]:
            await self.show_balances(user_id)
        
        elif callback_data in ["sniper_start", "start_sniper"]:
            await self.start_sniper(user_id)
        
        elif callback_data in ["sniper_stop", "stop_sniper"]:
            await self.stop_sniper(user_id)
        
        elif callback_data in ["history_refresh", "check_history"]:
            await self.show_history(user_id)
        
        elif callback_data in ["settings", "check_settings"]:
            await self.show_settings(user_id)
    
    def start_polling(self):
        """Inicia polling de mensagens em background"""
        if not self.enabled:
            return
        
        self.running = True
        
        def poll_loop():
            offset = None
            while self.running:
                try:
                    params = {"timeout": 30}
                    if offset:
                        params["offset"] = offset
                    
                    response = requests.get(
                        f"https://api.telegram.org/bot{self.token}/getUpdates",
                        params=params,
                        timeout=35
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("ok"):
                            for update in data.get("result", []):
                                offset = update.get("update_id", 0) + 1
                                
                                # Processar mensagem
                                if "message" in update:
                                    msg = update["message"]
                                    text = msg.get("text", "")
                                    user_id = msg.get("from", {}).get("id")
                                    asyncio.run(self.handle_command(text, user_id))
                                
                                # Processar callback query
                                elif "callback_query" in update:
                                    cb = update["callback_query"]
                                    user_id = cb.get("from", {}).get("id")
                                    data = cb.get("data", "")
                                    asyncio.run(self.handle_callback(data, user_id))
                    
                except Exception as e:
                    print(f"⚠️ Erro no polling: {e}")
                    import time
                    time.sleep(5)
        
        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
        print("✅ Telegram polling iniciado em background")
    
    def stop_polling(self):
        """Para o polling"""
        self.running = False
    
    # Métodos de compatibilidade com o código antigo
    
    async def send_notification(self, message: str, priority: str = "normal"):
        """Envia notificação (para compatibilidade)"""
        text = f"<b>🔔 NOTIFICAÇÃO</b>\n\n{message}"
        await self.send_message(text)
    
    async def send_trade_alert(self, token_address: str, token_name: str, action: str, details: dict = None):
        """Envia alerta de trade"""
        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "📊"
        
        text = f"""
{emoji} <b>ALERTA DE TRADE</b>

<b>Token:</b> {token_name}
<b>Ação:</b> {action}
<b>Endereço:</b> <code>{token_address[:15]}...</code>
"""
        
        if details:
            if 'amount' in details:
                text += f"\n<b>Quantidade:</b> {details['amount']}"
            if 'price' in details:
                text += f"\n<b>Preço:</b> {details['price']}"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📊 Ver Status", "callback_data": "check_status"}]
            ]
        }
        
        await self.send_message(text, reply_markup=keyboard)
    
    async def send_status_update(self, status_data: dict):
        """Envia atualização de status"""
        status = status_data.get('status', 'Desconhecido')
        running = "🟢 ATIVO" if status == 'Rodando' else "🔴 INATIVO"
        
        text = f"""
<b>📊 STATUS ATUALIZADO</b>

<b>Status:</b> {running}
<b>Trades:</b> {status_data.get('trades_executed', 0)}
<b>Sucessos:</b> {status_data.get('successful_trades', 0)}
<b>Lucro:</b> {status_data.get('total_profit', '0')} ETH
<b>ETH:</b> {status_data.get('eth_balance', '0')} ETH
<b>ETH:</b> {status_data.get('eth_balance', '0')} ETH
"""
        
        keyboard = self.get_status_keyboard()
        await self.send_message(text, reply_markup=keyboard)
    
    async def start(self):
        """Inicia o bot (para compatibilidade)"""
        self.start_polling()
        for user_id in self.authorized_users:
            await self.send_main_menu(user_id)
    
    async def cleanup_and_disable_polling(self):
        """Limpa e para polling"""
        self.stop_polling()


# Instância global
advanced_telegram = None

def get_advanced_telegram(sniper_bot=None):
    """Retorna instância do bot de telegram"""
    global advanced_telegram
    if advanced_telegram is None:
        advanced_telegram = AdvancedTelegramBot(sniper_bot)
    elif sniper_bot:
        advanced_telegram.set_sniper_bot(sniper_bot)
    return advanced_telegram


# Alias para compatibilidade
simple_telegram = None

def get_simple_telegram():
    """Alias para get_advanced_telegram"""
    return get_advanced_telegram()