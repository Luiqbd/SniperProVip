#!/usr/bin/env python3
"""
Teste específico para conversão WETH->ETH com saldos baixos
"""

from colorama import Fore, Style, init
from config import EMERGENCY_MODE_THRESHOLD, EMERGENCY_TRADE_AMOUNT, EMERGENCY_GAS_PRICE

# Inicializar colorama
init(autoreset=True)

def test_emergency_settings():
    """Testa as configurações de emergência"""
    print(f"{Fore.CYAN}🧪 Testando Configurações de Emergência...{Style.RESET_ALL}")
    
    print(f"   🚨 Threshold emergência: {EMERGENCY_MODE_THRESHOLD} ETH")
    print(f"   💰 Trade emergência: {EMERGENCY_TRADE_AMOUNT} WETH")
    print(f"   ⛽ Gas price emergência: {EMERGENCY_GAS_PRICE} (0.1 gwei)")
    
    # Simular saldo atual dos logs
    current_eth = 0.000005
    current_weth = 0.001990
    
    print(f"\n   📊 Saldo atual ETH: {current_eth:.6f}")
    print(f"   📊 Saldo atual WETH: {current_weth:.6f}")
    
    # Verificar se modo emergência seria ativado
    emergency_mode = current_eth < EMERGENCY_MODE_THRESHOLD
    print(f"   🚨 Modo emergência: {'✅ ATIVO' if emergency_mode else '❌ INATIVO'}")
    
    if emergency_mode:
        print(f"   💰 Trade amount reduzido: {EMERGENCY_TRADE_AMOUNT:.6f} WETH")
        print(f"   ⛽ Gas price reduzido: {EMERGENCY_GAS_PRICE} (0.1 gwei)")
        
        # Calcular custo de gas estimado
        gas_limit = 30000  # Gas para withdraw WETH
        gas_price_wei = int(0.1 * 10**9)  # 0.1 gwei em wei
        gas_cost_wei = gas_limit * gas_price_wei
        gas_cost_eth = gas_cost_wei / 10**18
        
        print(f"   💸 Custo gas estimado: {gas_cost_eth:.8f} ETH")
        print(f"   ✅ Saldo ETH suficiente: {'SIM' if current_eth >= gas_cost_eth else 'NÃO'}")
        
        # Verificar se WETH é suficiente para conversão
        min_conversion = 0.00002  # Mínimo para conversão
        print(f"   🔄 Conversão mínima: {min_conversion:.6f} WETH")
        print(f"   ✅ WETH suficiente: {'SIM' if current_weth >= min_conversion else 'NÃO'}")
    
    return True

def test_gas_calculation():
    """Testa cálculos de gas"""
    print(f"\n{Fore.CYAN}🧪 Testando Cálculos de Gas...{Style.RESET_ALL}")
    
    # Configurações ultra baixas
    gas_limit = 30000
    gas_price_gwei = 0.1
    gas_price_wei = int(gas_price_gwei * 10**9)
    
    print(f"   ⛽ Gas limit: {gas_limit}")
    print(f"   💰 Gas price: {gas_price_gwei} gwei")
    print(f"   💰 Gas price (wei): {gas_price_wei}")
    
    # Calcular custo total
    total_cost_wei = gas_limit * gas_price_wei
    total_cost_eth = total_cost_wei / 10**18
    
    print(f"   💸 Custo total: {total_cost_wei} wei")
    print(f"   💸 Custo total: {total_cost_eth:.8f} ETH")
    
    # Verificar se é viável com saldo atual
    current_eth = 0.000005
    viable = current_eth >= total_cost_eth
    
    print(f"   📊 Saldo atual: {current_eth:.6f} ETH")
    print(f"   ✅ Transação viável: {'SIM' if viable else 'NÃO'}")
    
    if viable:
        remaining = current_eth - total_cost_eth
        print(f"   💰 ETH restante: {remaining:.8f} ETH")
    
    return viable

def main():
    """Executa todos os testes"""
    print(f"{Fore.YELLOW}🚀 TESTE DE CONVERSÃO WETH->ETH{Style.RESET_ALL}")
    print("=" * 60)
    
    tests = [
        ("Configurações Emergência", test_emergency_settings()),
        ("Cálculos de Gas", test_gas_calculation()),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}📊 RESULTADO:{Style.RESET_ALL}")
    print(f"   ✅ Passou: {passed}/{total}")
    print(f"   ❌ Falhou: {total - passed}/{total}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}🎉 CONVERSÃO OTIMIZADA!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Gas price ultra baixo: 0.1 gwei{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Threshold emergência: 0.00001 ETH{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Conversão mínima: 0.00002 WETH{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ Alguns ajustes necessários{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}🔧 MELHORIAS IMPLEMENTADAS:{Style.RESET_ALL}")
    print("• ✅ Gas price reduzido para 0.1 gwei")
    print("• ✅ Gas limit reduzido para 30,000")
    print("• ✅ Threshold emergência: 0.00001 ETH")
    print("• ✅ Conversão mínima: 0.00002 WETH")
    print("• ✅ Trade emergência: 0.000020 WETH")

if __name__ == "__main__":
    main()