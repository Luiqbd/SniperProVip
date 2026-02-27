#!/usr/bin/env python3
"""
Versão simplificada do Telegram bot para evitar conflitos
"""

import asyncio
import requests
import json
import re
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_AUTHORIZED_USERS

class SimpleTelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.authorized_users = []
        
        # Processar usuários autorizados
        if TELEGRAM_AUTHORIZED_USERS:
            for user_id in TELEGRAM_AUTHORIZED_USERS.split(','):
                try:
                    user_id = int(user_id.strip())
                    if user_id > 0:  # IDs válidos são positivos
                        self.authorized_users.append(user_id)
                except:
                    pass
        
        self.enabled = bool(self.token and self.authorized_users)
        
        if not self.enabled:
            print("⚠️ Telegram bot desabilitado - token ou usuários não configurados")
    
    def escape_markdown(self, text: str) -> str:
        """Escapa caracteres especiais do Markdown para evitar erros de parsing"""
        # Caracteres que precisam ser escapados no Markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def markdown_to_html(self, text: str) -> str:
        """Converte Markdown básico para HTML para evitar erros de parsing"""
        # Escapar caracteres HTML primeiro
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Converter formatação Markdown para HTML
        # Bold: *texto* -> <b>texto</b>
        text = re.sub(r'\*([^*]+)\*', r'<b>\1</b>', text)
        
        # Italic: _texto_ -> <i>texto</i>
        text = re.sub(r'_([^_]+)_', r'<i>\1</i>', text)
        
        # Code: `texto` -> <code>texto</code>
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        return text
    
    async def send_message(self, message: str, priority: str = "normal", buttons: list = None):
        """Envia mensagem usando requests direto (sem python-telegram-bot)"""
        if not self.enabled:
            print(f"📱 Notificação [{priority}]: {message}")
            return
        
        for user_id in self.authorized_users:
            try:
                # Converter Markdown para HTML para evitar problemas de parsing
                html_message = self.markdown_to_html(message)
                
                payload = {
                    "chat_id": user_id,
                    "text": html_message,
                    "parse_mode": "HTML"
                }
                
                # Adicionar botões se fornecidos
                if buttons:
                    keyboard = {"inline_keyboard": []}
                    for button_row in buttons:
                        row = []
                        for button in button_row:
                            row.append({
                                "text": button["text"],
                                "callback_data": button["callback_data"]
                            })
                        keyboard["inline_keyboard"].append(row)
                    payload["reply_markup"] = keyboard
                
                response = requests.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Mensagem enviada para {user_id}")
                else:
                    print(f"❌ Erro ao enviar para {user_id}: {response.text}")
                    
            except Exception as e:
                print(f"❌ Erro ao enviar mensagem: {e}")
    
    async def send_trade_alert(self, token_address: str, token_name: str, action: str, details: dict = None):
        """Envia alerta de trade"""
        if action == "BUY":
            emoji = "🟢"
        elif action == "SELL":
            emoji = "🔴"
        else:
            emoji = "📊"
        
        message = f"{emoji} *{action}* - {token_name}\n"
        message += f"📍 `{token_address}`\n"
        
        if details:
            if 'score' in details:
                message += f"📊 Score: {details['score']}/100\n"
            if 'price' in details:
                message += f"💰 Preço: {details['price']}\n"
            if 'amount' in details:
                message += f"💎 Quantidade: {details['amount']}\n"
        
        await self.send_message(message, "high")
    
    async def send_status_update(self, status_data: dict):
        """Envia atualização de status com botões de controle"""
        message = "📊 *STATUS DO SNIPER BOT*\n\n"
        message += f"🔄 Status: {status_data.get('status', 'Desconhecido')}\n"
        message += f"📈 Trades: {status_data.get('trades_executed', 0)}\n"
        message += f"✅ Sucessos: {status_data.get('successful_trades', 0)}\n"
        message += f"💰 Lucro: {status_data.get('total_profit', '0.000000')} ETH\n"
        message += f"💳 Saldo ETH: {status_data.get('eth_balance', '0.000000')} ETH\n"
        message += f"💰 Saldo WETH: {status_data.get('weth_balance', '0.000000')} WETH\n"
        
        # Adicionar botões de controle
        buttons = [
            [
                {"text": "🔄 Atualizar Status", "callback_data": "update_status"},
                {"text": "⚙️ Configurações", "callback_data": "settings"}
            ],
            [
                {"text": "📊 Histórico", "callback_data": "history"},
                {"text": "💰 Saldos", "callback_data": "balances"}
            ]
        ]
        
        await self.send_message(message, "normal", buttons)
    
    async def send_notification(self, message: str, priority: str = "normal"):
        """Método de compatibilidade - redireciona para send_message"""
        await self.send_message(message, priority)
    
    async def cleanup_and_disable_polling(self):
        """Limpa e desabilita polling para evitar conflitos"""
        if not self.token:
            return
        
        try:
            print("🧹 Limpando Telegram para evitar conflitos...")
            
            # Deletar webhook
            requests.post(
                f"https://api.telegram.org/bot{self.token}/deleteWebhook",
                json={"drop_pending_updates": True},
                timeout=10
            )
            
            # Limpar updates pendentes
            for _ in range(3):
                requests.post(
                    f"https://api.telegram.org/bot{self.token}/getUpdates",
                    json={"offset": 999999999, "limit": 100, "timeout": 1},
                    timeout=10
                )
            
            print("✅ Telegram limpo - usando modo somente envio")
            
        except Exception as e:
            print(f"❌ Erro na limpeza Telegram: {e}")

# Instância global
simple_telegram = SimpleTelegramBot()

async def init_simple_telegram():
    """Inicializa o bot simples"""
    await simple_telegram.cleanup_and_disable_polling()
    return simple_telegram