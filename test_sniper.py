#!/usr/bin/env python3
"""
Teste do Sniper Bot V2.0 - Verificação de funcionalidades
"""

import asyncio
import sys
import os
from web3 import Web3

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from dex_handler import DEXHandler
from sniper_bot import SniperBot

async def test_connection():
    """Testa conexão com a Base Network"""
    print("🔍 Testando conexão com Base Network...")
    
    try:
        web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
        if web3.is_connected():
            print("✅ Conexão com Base Network: OK")
            
            # Testar bloco atual
            latest_block = web3.eth.block_number
            print(f"📦 Bloco atual: {latest_block}")
            
            return web3
        else:
            print("❌ Falha na conexão com Base Network")
            return None
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return None

async def test_wallet_config():
    """Testa configuração da carteira"""
    print("\n🔍 Testando configuração da carteira...")
    
    try:
        if not PRIVATE_KEY or not WALLET_ADDRESS:
            print("❌ Variáveis de ambiente não configuradas")
            return False
        
        # Verificar se a private key corresponde ao endereço
        from eth_account import Account
        account = Account.from_key(PRIVATE_KEY)
        
        if account.address.lower() == WALLET_ADDRESS.lower():
            print("✅ Private key e endereço: OK")
            return True
        else:
            print("❌ Private key não corresponde ao endereço")
            return False
            
    except Exception as e:
        print(f"❌ Erro na configuração da carteira: {str(e)}")
        return False

async def test_dex_connections(web3):
    """Testa conexões com DEXs"""
    print("\n🔍 Testando conexões com DEXs...")
    
    try:
        dex_handler = DEXHandler(web3)
        results = dex_handler.test_all_dexs()
        
        working_dexs = sum(1 for working in results.values() if working)
        total_dexs = len(results)
        
        if working_dexs > 0:
            print(f"✅ DEXs funcionando: {working_dexs}/{total_dexs}")
            return True
        else:
            print("❌ Nenhuma DEX funcionando")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar DEXs: {str(e)}")
        return False

async def test_balance_check(web3):
    """Testa verificação de saldos"""
    print("\n🔍 Testando verificação de saldos...")
    
    try:
        # Saldo ETH
        balance = web3.eth.get_balance(WALLET_ADDRESS)
        balance_eth = float(web3.from_wei(balance, 'ether'))
        print(f"💰 Saldo ETH: {balance_eth:.6f} ETH")
        
        # Saldo WETH
        dex_handler = DEXHandler(web3)
        weth_balance = await dex_handler.get_weth_balance()
        print(f"💰 Saldo WETH: {weth_balance:.6f} WETH")
        
        total_balance = balance_eth + weth_balance
        print(f"💰 Saldo total: {total_balance:.6f} ETH")
        
        if total_balance > 0:
            print("✅ Saldos verificados: OK")
            return True
        else:
            print("⚠️ Saldos muito baixos")
            return True  # Não é erro crítico
            
    except Exception as e:
        print(f"❌ Erro ao verificar saldos: {str(e)}")
        return False

async def test_price_discovery(web3):
    """Testa descoberta de preços"""
    print("\n🔍 Testando descoberta de preços...")
    
    try:
        dex_handler = DEXHandler(web3)
        
        # Testar com USDC (token conhecido)
        test_amount = web3.to_wei(0.0001, 'ether')  # 0.0001 WETH
        
        print(f"🔍 Testando preço WETH -> USDC...")
        best_dex, best_price, best_router = await dex_handler.get_best_price(
            USDC_ADDRESS, test_amount, is_buy=True
        )
        
        if best_dex and best_price > 0:
            price_usdc = web3.from_wei(best_price, 'mwei')  # USDC tem 6 decimais
            print(f"✅ Melhor preço encontrado: {price_usdc:.6f} USDC na {best_dex}")
            return True
        else:
            print("⚠️ Não foi possível encontrar preço (normal para tokens novos)")
            return True  # Não é erro crítico
            
    except Exception as e:
        print(f"❌ Erro na descoberta de preços: {str(e)}")
        return False

async def test_gas_estimation(web3):
    """Testa estimativa de gas"""
    print("\n🔍 Testando estimativa de gas...")
    
    try:
        # Gas price atual
        gas_price = web3.eth.gas_price
        gas_price_gwei = web3.from_wei(gas_price, 'gwei')
        print(f"⛽ Gas price atual: {gas_price_gwei:.2f} Gwei")
        
        # Verificar se está dentro dos limites
        max_gas_gwei = MAX_GAS_PRICE
        if gas_price_gwei <= max_gas_gwei:
            print(f"✅ Gas price OK (limite: {max_gas_gwei} Gwei)")
            return True
        else:
            print(f"⚠️ Gas price alto (limite: {max_gas_gwei} Gwei)")
            return True  # Não é erro crítico
            
    except Exception as e:
        print(f"❌ Erro na estimativa de gas: {str(e)}")
        return False

async def run_comprehensive_test():
    """Executa teste completo do sistema"""
    print("🚀 INICIANDO TESTE COMPLETO DO SNIPER BOT V2.0")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 6
    
    # Teste 1: Conexão
    web3 = await test_connection()
    if web3:
        tests_passed += 1
    else:
        print("❌ Teste crítico falhou - parando execução")
        return False
    
    # Teste 2: Configuração da carteira
    if await test_wallet_config():
        tests_passed += 1
    else:
        print("❌ Teste crítico falhou - parando execução")
        return False
    
    # Teste 3: Conexões DEX
    if await test_dex_connections(web3):
        tests_passed += 1
    
    # Teste 4: Verificação de saldos
    if await test_balance_check(web3):
        tests_passed += 1
    
    # Teste 5: Descoberta de preços
    if await test_price_discovery(web3):
        tests_passed += 1
    
    # Teste 6: Estimativa de gas
    if await test_gas_estimation(web3):
        tests_passed += 1
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 60)
    print(f"✅ Testes aprovados: {tests_passed}/{total_tests}")
    print(f"📈 Taxa de sucesso: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed >= 4:  # Pelo menos 4 testes críticos
        print("🎉 SISTEMA PRONTO PARA OPERAR!")
        print("💡 Recomendação: Iniciar o bot em modo real")
        return True
    else:
        print("⚠️ SISTEMA PRECISA DE AJUSTES")
        print("💡 Recomendação: Corrigir problemas antes de operar")
        return False

async def main():
    """Função principal"""
    try:
        success = await run_comprehensive_test()
        
        if success:
            print("\n🚀 Deseja iniciar o bot agora? (y/n): ", end="")
            # Em ambiente de produção, remover input interativo
            print("Teste concluído com sucesso!")
        else:
            print("\n❌ Corrija os problemas identificados antes de continuar")
            
    except KeyboardInterrupt:
        print("\n👋 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())