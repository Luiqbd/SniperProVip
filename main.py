#!/usr/bin/env python3
"""
Sniper Bot V5 - Base Network Edition
Bot de sniper para trading automático na rede Base Ethereum
Configurado para usar BestWallet e múltiplas DEXs
"""

import asyncio
import sys
import os
from aiohttp import web
import threading
from sniper_bot import SniperBot

async def health_check(request):
    """Endpoint de health check para o Render"""
    return web.json_response({
        'status': 'healthy',
        'service': 'Sniper Bot V5',
        'network': 'Base Ethereum'
    })

async def status_endpoint(request):
    """Endpoint de status do bot"""
    return web.json_response({
        'status': 'running',
        'message': 'Sniper Bot V5 ativo na Base Network',
        'trades_executed': 0,
        'uptime': 'Running'
    })

async def start_web_server():
    """Inicia servidor web para o Render"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status_endpoint)
    
    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Servidor web iniciado na porta {port}")

async def main_async():
    """Função principal assíncrona"""
    print("🚀 Iniciando Sniper Bot V5 - Base Network Edition")
    print("=" * 60)
    
    # Verificar se as variáveis de ambiente estão configuradas
    private_key = os.getenv('PRIVATE_KEY')
    wallet_address = os.getenv('WALLET_ADDRESS')
    
    if not private_key or not wallet_address:
        if os.path.exists('.env'):
            print("📝 Carregando configurações do arquivo .env")
        else:
            print("❌ Variáveis de ambiente não configuradas!")
            print("📝 Configure PRIVATE_KEY e WALLET_ADDRESS nas variáveis de ambiente")
            print("   ou copie .env.example para .env e configure suas credenciais")
            return
    else:
        print("✅ Variáveis de ambiente configuradas")
    
    try:
        # Iniciar servidor web para o Render
        await start_web_server()
        
        # Executar o bot
        bot = SniperBot()
        await bot.start()
        
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")
        sys.exit(1)

def main():
    """Função principal"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
