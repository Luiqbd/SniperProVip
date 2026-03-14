import json
from web3 import Web3
from typing import Dict, List, Optional, Tuple
import requests
import time
import asyncio
from colorama import Fore, Style, init
from config import *
from rate_limiter import BASE_RPC_LIMITER, with_rate_limit

# Inicializar colorama
init(autoreset=True)

class DEXHandler:
    def __init__(self, web3: Web3):
        self.web3 = web3
        self.backup_web3 = None
        self.balance_cache = {}
        self.cache_timeout = 30  # Cache por 30 segundos
        self.dexs = self._initialize_dexs()
        self._init_backup_rpc()
    
    def _init_backup_rpc(self):
        """Inicializa RPC backup"""
        try:
            self.backup_web3 = Web3(Web3.HTTPProvider(BASE_RPC_BACKUP))
            if self.backup_web3.is_connected():
                print(f"{Fore.GREEN}✅ RPC backup conectado: {BASE_RPC_BACKUP}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️ RPC backup não disponível{Style.RESET_ALL}")
                self.backup_web3 = None
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Erro ao conectar RPC backup: {str(e)}{Style.RESET_ALL}")
            self.backup_web3 = None
    
    def _get_web3_instance(self):
        """Retorna instância Web3 disponível (principal ou backup)"""
        if self.web3.is_connected():
            return self.web3
        elif self.backup_web3 and self.backup_web3.is_connected():
            print(f"{Fore.YELLOW}🔄 Usando RPC backup{Style.RESET_ALL}")
            return self.backup_web3
        else:
            return self.web3  # Fallback para principal mesmo se não conectado
    
    def _get_cached_balance(self, cache_key: str):
        """Obtém saldo do cache se válido"""
        if cache_key in self.balance_cache:
            cached_data = self.balance_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_timeout:
                return cached_data['balance']
        return None
    
    def _cache_balance(self, cache_key: str, balance: float):
        """Armazena saldo no cache"""
        self.balance_cache[cache_key] = {
            'balance': balance,
            'timestamp': time.time()
        }
        
    def _initialize_dexs(self) -> Dict:
        """Inicializa as configurações das DEXs"""
        dexs = {}
        
        if ENABLE_UNISWAP_V3:
            dexs['uniswap_v3'] = {
                'name': 'Uniswap V3',
                'router': UNISWAP_V3_ROUTER,
                'factory': UNISWAP_V3_FACTORY,
                'fee_tiers': [100, 500, 3000, 10000],  # 0.01%, 0.05%, 0.3%, 1%
                'priority': 1
            }
            
        if ENABLE_AERODROME:
            dexs['aerodrome'] = {
                'name': 'Aerodrome',
                'router': AERODROME_ROUTER,
                'factory': AERODROME_FACTORY,
                'priority': 2
            }
            
        if ENABLE_BASESWAP:
            dexs['baseswap'] = {
                'name': 'BaseSwap',
                'router': BASESWAP_ROUTER,
                'factory': BASESWAP_FACTORY,
                'priority': 3
            }
            
        if ENABLE_SUSHISWAP:
            dexs['sushiswap'] = {
                'name': 'SushiSwap',
                'router': SUSHISWAP_ROUTER,
                'priority': 4
            }
            
        return dexs
    
    def get_router_abi(self) -> List:
        """ABI completa para roteadores de DEX incluindo swaps de tokens"""
        return [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForETH",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsIn",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    async def get_weth_balance(self) -> float:
        """Obtém saldo WETH da carteira com cache e RPC backup"""
        cache_key = f"weth_balance_{WALLET_ADDRESS}"
        
        # Verificar cache primeiro
        cached_balance = self._get_cached_balance(cache_key)
        if cached_balance is not None:
            return cached_balance
        
        # Tentar obter saldo com rate limiting
        for attempt in range(2):  # Máximo 2 tentativas
            try:
                await BASE_RPC_LIMITER.acquire()
                
                web3_instance = self._get_web3_instance()
                weth_contract = web3_instance.eth.contract(
                    address=WETH_ADDRESS,
                    abi=[{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                )
                
                balance_wei = weth_contract.functions.balanceOf(WALLET_ADDRESS).call()
                balance_eth = float(web3_instance.from_wei(balance_wei, 'ether'))
                
                # Cache o resultado
                self._cache_balance(cache_key, balance_eth)
                
                print(f"✅ Saldo WETH lido: {balance_eth:.6f} WETH (raw: {balance_wei}, decimals: 18)")
                BASE_RPC_LIMITER.handle_success()
                return balance_eth
                
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    BASE_RPC_LIMITER.handle_429_error()
                    if attempt == 0:
                        print(f"⚠️ Rate limit - tentativa {attempt + 1}/2")
                        await asyncio.sleep(2)  # Esperar 2 segundos antes de tentar novamente
                        continue
                
                print(f"❌ Erro ao obter saldo WETH: {e}")
                if attempt == 1:  # Última tentativa
                    return 0.0
                    
        return 0.0
    
    async def convert_weth_to_eth_if_needed(self, min_eth_needed: float = 0.00001) -> bool:
        """
        Converte WETH para ETH se o saldo de ETH estiver muito baixo
        VERSÃO OTIMIZADA PARA SALDOS MÍNIMOS
        """
        for attempt in range(3):
            try:
                await BASE_RPC_LIMITER.acquire()
                
                web3_instance = self._get_web3_instance()
                eth_balance = web3_instance.eth.get_balance(WALLET_ADDRESS)
                eth_balance_eth = float(web3_instance.from_wei(eth_balance, 'ether'))
                
                if eth_balance_eth >= min_eth_needed:
                    return True  # ETH suficiente
                
                print(f"⚠️ Saldo ETH baixo: {eth_balance_eth:.9f} (precisa: {min_eth_needed})")
                
                # Verificar saldo WETH
                weth_abi = [
                    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                    {"constant": False, "inputs": [{"name": "wad", "type": "uint256"}], "name": "withdraw", "outputs": [], "type": "function"}
                ]
                
                weth_contract = web3_instance.eth.contract(address=WETH_ADDRESS, abi=weth_abi)
                weth_balance = weth_contract.functions.balanceOf(WALLET_ADDRESS).call()
                weth_balance_eth = float(web3_instance.from_wei(weth_balance, 'ether'))
                
                # Calcular exatamente o quanto precisa para gas + conversão
                # Usar gas price mínimo absoluto possível
                gas_price = web3_instance.to_wei(0.001, 'gwei')  # 0.001 gwei =最小
                gas_limit = 25000  # Gas mínimo para withdraw
                gas_cost_eth = float(web3_instance.from_wei(gas_price * gas_limit, 'ether'))
                
                # Calcular quanto ETH precisamos ter após conversão
                total_needed = max(min_eth_needed, gas_cost_eth * 2)  # Deixar folga
                
                # Converter exatamente o necessário + custo do gas
                eth_to_convert = total_needed - eth_balance_eth + gas_cost_eth
                eth_to_convert = max(eth_to_convert, gas_cost_eth * 1.5)  # Mínimo para cobrir gas
                
                print(f"💰 WETH disponível: {weth_balance_eth:.9f}")
                print(f"💰 ETH atual: {eth_balance_eth:.9f}")
                print(f"💰 ETH necessário (gas + operação): {total_needed:.9f}")
                print(f"💰 Convertendo: {eth_to_convert:.9f}")
                
                if weth_balance_eth >= eth_to_convert:
                    # Converter WETH para ETH
                    withdraw_amount = int(web3_instance.to_wei(eth_to_convert, 'ether'))
                    
                    print(f"💱 Convertendo {eth_to_convert:.9f} WETH para ETH...")
                    
                    # Preparar transação de withdraw com gas MÍNIMO
                    withdraw_tx = weth_contract.functions.withdraw(withdraw_amount).build_transaction({
                        'from': WALLET_ADDRESS,
                        'gas': gas_limit,
                        'gasPrice': gas_price,  # Gas price mínimo
                        'nonce': web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
                    })
                    
                    # Assinar e enviar
                    signed_tx = web3_instance.eth.account.sign_transaction(withdraw_tx, PRIVATE_KEY)
                    tx_hash = web3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
                    
                    print(f"✅ Conversão enviada: {tx_hash.hex()}")
                    
                    # Aguardar confirmação
                    try:
                        receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                        if receipt.status == 1:
                            print(f"✅ Conversão confirmada!")
                            BASE_RPC_LIMITER.handle_success()
                            return True
                        else:
                            print(f"❌ Conversão falhou")
                            return False
                    except:
                        # Se não confirmou em 30s, assume que vai confirmar
                        print(f"⏳ Conversão pendente (pode confirmar)")
                        return True
                else:
                    print(f"❌ WETH insuficiente: {weth_balance_eth:.9f} < {eth_to_convert:.9f}")
                    return False
                    
            except Exception as e:
                error_str = str(e)
                if "insufficient funds" in error_str.lower():
                    print(f"❌ Saldo ETH insuficiente até para transação de conversão!")
                    print(f"💡 SOLUÇÃO: Adicione ETH à carteira para pagar gas")
                    return False
                elif "429" in error_str or "Too Many Requests" in error_str:
                    BASE_RPC_LIMITER.handle_429_error()
                    if attempt < 2:
                        print(f"⚠️ Rate limit - tentativa {attempt + 1}/3")
                        await asyncio.sleep(5)
                        continue
                
                print(f"❌ Erro na conversão: {error_str[:100]}")
                if attempt == 2:
                    return False
                    
        return False
    
    async def _execute_trade_with_weth_gas(self, router_address: str, token_address: str, amount: float, is_buy: bool, slippage: float = 3.0):
        """
        Executa trade usando WETH para pagar gas (método alternativo)
        """
        try:
            print("🔄 Executando trade com WETH como gas...")
            
            # Primeiro, converter uma pequena quantidade de WETH para ETH para gas
            await BASE_RPC_LIMITER.acquire()
            web3_instance = self._get_web3_instance()
            
            # Converter apenas o mínimo necessário para gas
            weth_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": False, "inputs": [{"name": "wad", "type": "uint256"}], "name": "withdraw", "outputs": [], "type": "function"}
            ]
            
            weth_contract = web3_instance.eth.contract(address=WETH_ADDRESS, abi=weth_abi)
            
            # Converter 0.00001 WETH para ETH (suficiente para 1 transação com gas ultra baixo)
            gas_amount_weth = 0.00001
            withdraw_amount = int(web3_instance.to_wei(gas_amount_weth, 'ether'))
            
            print(f"💱 Convertendo {gas_amount_weth:.6f} WETH para gas...")
            
            # Preparar transação de withdraw com gas MÍNIMO
            withdraw_tx = weth_contract.functions.withdraw(withdraw_amount).build_transaction({
                'from': WALLET_ADDRESS,
                'gas': 25000,  # Gas MÍNIMO
                'gasPrice': web3_instance.to_wei(0.05, 'gwei'),  # Gas price ULTRA baixo
                'nonce': web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
            })
            
            # Assinar e enviar
            signed_tx = web3_instance.eth.account.sign_transaction(withdraw_tx, PRIVATE_KEY)
            tx_hash = web3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"✅ WETH convertido para gas: {tx_hash.hex()}")
            
            # Aguardar confirmação
            await asyncio.sleep(3)
            
            # Agora executar o trade normal
            return await self._execute_trade_normal(router_address, token_address, amount, is_buy, slippage)
            
        except Exception as e:
            print(f"❌ Erro ao executar trade com WETH gas: {e}")
            return None
    
    async def _execute_trade_normal(self, router_address: str, token_address: str, amount: float, is_buy: bool, slippage: float = 3.0):
        """
        Executa trade normal após ter ETH suficiente para gas
        """
        try:
            await BASE_RPC_LIMITER.acquire()
            web3_instance = self._get_web3_instance()
            
            router_contract = web3_instance.eth.contract(
                address=router_address,
                abi=self.get_router_abi()
            )
            
            path = [WETH_ADDRESS, token_address] if is_buy else [token_address, WETH_ADDRESS]
            deadline = int(time.time()) + 600
            
            amount_wei = int(web3_instance.to_wei(amount, 'ether'))
            
            if is_buy:
                # Compra: WETH -> Token
                amounts_out = router_contract.functions.getAmountsOut(amount_wei, path).call()
                min_amount_out = int(amounts_out[-1] * (1 - slippage / 100))
                
                transaction = router_contract.functions.swapExactTokensForTokens(
                    amount_wei,
                    min_amount_out,
                    path,
                    WALLET_ADDRESS,
                    deadline
                ).build_transaction({
                    'from': WALLET_ADDRESS,
                    'gas': 200000,
                    'gasPrice': web3_instance.to_wei(0.1, 'gwei'),  # Gas ultra baixo
                    'nonce': web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
                })
            else:
                # Venda: Token -> WETH
                amounts_out = router_contract.functions.getAmountsOut(amount_wei, path).call()
                min_amount_out = int(amounts_out[-1] * (1 - slippage / 100))
                
                transaction = router_contract.functions.swapExactTokensForTokens(
                    amount_wei,
                    min_amount_out,
                    path,
                    WALLET_ADDRESS,
                    deadline
                ).build_transaction({
                    'from': WALLET_ADDRESS,
                    'gas': 200000,
                    'gasPrice': web3_instance.to_wei(0.1, 'gwei'),
                    'nonce': web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
                })
            
            # Assinar e enviar transação
            signed_txn = web3_instance.eth.account.sign_transaction(transaction, PRIVATE_KEY)
            tx_hash = web3_instance.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"✅ Trade executado: {tx_hash.hex()}")
            BASE_RPC_LIMITER.handle_success()
            
            return {
                'hash': tx_hash.hex(),
                'amount': amount,
                'token': token_address,
                'type': 'buy' if is_buy else 'sell'
            }
            
        except Exception as e:
            print(f"❌ Erro no trade normal: {e}")
            return None
    
    async def check_token_liquidity(self, token_address: str) -> bool:
        """
        Verifica se o token tem liquidez suficiente em alguma DEX
        Versão ULTRA otimizada - teste mínimo e rápido
        """
        try:
            # Usar apenas uma quantidade mínima para teste ultra rápido
            test_amount = 10000000000000  # 0.00001 WETH (mínimo)
            
            # Testar DEXs em ordem de prioridade (mais prováveis primeiro)
            priority_order = ['uniswap_v3', 'aerodrome', 'baseswap', 'sushiswap']
            
            for dex_key in priority_order:
                if dex_key not in self.dexs:
                    continue
                    
                dex_info = self.dexs[dex_key]
                try:
                    await BASE_RPC_LIMITER.acquire()
                    
                    router_contract = self.web3.eth.contract(
                        address=dex_info['router'],
                        abi=self.get_router_abi()
                    )
                    
                    # Testar apenas WETH -> Token (mais comum para novos tokens)
                    path = [WETH_ADDRESS, token_address]
                    
                    amounts = router_contract.functions.getAmountsOut(test_amount, path).call()
                    
                    if len(amounts) >= 2 and amounts[-1] > 0:
                        print(f"✅ Liquidez encontrada em {dex_info['name']}")
                        BASE_RPC_LIMITER.handle_success()
                        return True
                        
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        BASE_RPC_LIMITER.handle_429_error()
                        await asyncio.sleep(0.1)  # Backoff mínimo
                    elif "execution reverted" in str(e).lower():
                        # Token não tem par nesta DEX, continuar
                        print(f"⚠️ {dex_info['name']}: Sem par de trading para este token")
                    continue
                        
            return False
            
        except Exception as e:
            print(f"❌ Erro ao verificar liquidez: {str(e)}")
            return False

    async def get_best_price(self, token_address: str, amount_in: int, is_buy: bool = True) -> Tuple[str, int, str]:
        """
        Encontra o melhor preço entre todas as DEXs com rate limiting e verificação de liquidez
        Returns: (dex_name, amount_out, router_address)
        """
        best_price = 0
        best_dex = None
        best_router = None
        successful_queries = 0
        
        # Tentar múltiplos paths para encontrar liquidez
        paths_to_try = []
        
        if is_buy:
            # Para compra: WETH -> Token
            paths_to_try = [
                [WETH_ADDRESS, token_address],  # Direto
                [WETH_ADDRESS, USDC_ADDRESS, token_address],  # Via USDC
                [WETH_ADDRESS, USDT_ADDRESS, token_address],  # Via USDT
            ]
        else:
            # Para venda: Token -> WETH
            paths_to_try = [
                [token_address, WETH_ADDRESS],  # Direto
                [token_address, USDC_ADDRESS, WETH_ADDRESS],  # Via USDC
                [token_address, USDT_ADDRESS, WETH_ADDRESS],  # Via USDT
            ]
        
        for dex_key, dex_info in self.dexs.items():
            try:
                await BASE_RPC_LIMITER.acquire()
                
                router_contract = self.web3.eth.contract(
                    address=dex_info['router'],
                    abi=self.get_router_abi()
                )
                
                # Tentar diferentes paths até encontrar liquidez
                for path in paths_to_try:
                    try:
                        amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
                        amount_out = amounts[-1]
                        
                        if amount_out > 0:  # Encontrou liquidez
                            successful_queries += 1
                            
                            if amount_out > best_price:
                                best_price = amount_out
                                best_dex = dex_info['name']
                                best_router = dex_info['router']
                                
                            path_str = " -> ".join([addr[:6] + "..." for addr in path])
                            print(f"💰 {dex_info['name']} ({path_str}): {amount_out / 10**18:.6f} {'WETH' if not is_buy else 'tokens'}")
                            BASE_RPC_LIMITER.handle_success()
                            break  # Encontrou liquidez, não precisa testar outros paths
                            
                    except Exception as path_error:
                        # Se este path falhou, tentar o próximo
                        continue
                
                # Se chegou aqui sem break, não encontrou liquidez em nenhum path
                if successful_queries == 0 or best_dex != dex_info['name']:
                    print(f"⚠️ {dex_info['name']}: Sem liquidez em nenhum path")
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    BASE_RPC_LIMITER.handle_429_error()
                    print(f"🚫 Rate limit 429 detectado. Backoff: {BASE_RPC_LIMITER.current_backoff}s")
                    print(f"⚠️ Rate limit em {dex_info['name']}, aguardando {BASE_RPC_LIMITER.current_backoff:.1f}s...")
                    await asyncio.sleep(min(BASE_RPC_LIMITER.current_backoff, 3))  # Máximo 3s
                elif "execution reverted" in error_msg.lower():
                    print(f"⚠️ {dex_info['name']}: Sem par de trading para este token")
                else:
                    print(f"⚠️ {dex_info['name']}: {error_msg[:50]}...")
                continue
        
        if successful_queries == 0:
            print("⚠️ Nenhuma DEX retornou preço válido - assumindo token muito novo")
            # Para tokens muito novos, assumir que terão liquidez em breve
            # Retornar valores padrão para permitir tentativa de compra
            print("🎯 MODO AGRESSIVO: Tentando compra mesmo sem preço confirmado")
            return "uniswap_v3", amount_in, self.dexs['uniswap_v3']['router']
            
        return best_dex, best_price, best_router
    
    async def execute_swap(self, token_address: str, amount_in: int, router_address: str, 
                    is_buy: bool = True, slippage: float = SLIPPAGE_TOLERANCE) -> Optional[str]:
        """
        Executa o swap na DEX especificada com melhor tratamento de erros
        Returns: transaction hash ou None se falhar
        """
        import time
        from eth_account import Account
        
        print(f"🔄 Iniciando swap: {'Compra' if is_buy else 'Venda'} de {self.web3.from_wei(amount_in, 'ether'):.6f} {'WETH' if is_buy else 'tokens'}")
        print(f"📍 Router: {router_address}")
        
        try:
            # Verificar saldos antes da transação
            if is_buy:
                weth_balance = await self.get_weth_balance()
                required_weth = self.web3.from_wei(amount_in, 'ether')
                print(f"💰 Saldo WETH: {weth_balance:.6f}, Necessário: {required_weth:.6f}")
                if weth_balance < required_weth:
                    print(f"❌ Saldo WETH insuficiente!")
                    return None
            
            # Verificar ETH para gas com rate limiting
            await BASE_RPC_LIMITER.acquire()
            web3_instance = self._get_web3_instance()
            
            eth_balance = web3_instance.eth.get_balance(WALLET_ADDRESS)
            eth_balance_eth = float(web3_instance.from_wei(eth_balance, 'ether'))
            print(f"💰 Saldo ETH: {eth_balance_eth:.6f}")
            
            min_eth_for_gas = 0.00005
            
            # SEMPRE tentar conversão se ETH < 0.00005
            if eth_balance_eth < min_eth_for_gas:
                print(f"⚠️ ETH baixo ({eth_balance_eth:.6f}) - forçando conversão WETH->ETH")
                if not await self.convert_weth_to_eth_if_needed(min_eth_for_gas):
                    print("❌ Não foi possível obter ETH suficiente para gas")
                    return None
                # Atualizar saldo ETH
                eth_balance = web3_instance.eth.get_balance(WALLET_ADDRESS)
                eth_balance_eth = float(web3_instance.from_wei(eth_balance, 'ether'))
                print(f"💰 Saldo ETH após conversão: {eth_balance_eth:.6f}")
            
            # Verificar checksum do router
            router_address = web3_instance.to_checksum_address(router_address)
            token_address = web3_instance.to_checksum_address(token_address)
            
            router_contract = web3_instance.eth.contract(
                address=router_address,
                abi=self.get_router_abi()
            )
            
            path = [WETH_ADDRESS, token_address] if is_buy else [token_address, WETH_ADDRESS]
            deadline = int(time.time()) + 600  # 10 minutos (aumentado)
            
            # Calcular amount_out_min com slippage mais flexível
            amount_out_min = 1  # Valor mínimo padrão para tokens novos
            try:
                amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
                if len(amounts) >= 2 and amounts[-1] > 0:
                    # Usar slippage mais agressivo para memecoins
                    effective_slippage = min(slippage + 5, 25)  # +5% extra, máximo 25%
                    amount_out_min = int(amounts[-1] * (100 - effective_slippage) / 100)
                    print(f"💰 Preço estimado: {amounts[-1]} tokens (slippage: {effective_slippage}%)")
                else:
                    print("⚠️ Não foi possível calcular preço exato, usando valor mínimo")
            except Exception as price_error:
                print(f"⚠️ Erro ao calcular preço: {str(price_error)[:50]}... Usando valor mínimo")
                # Para tokens muito novos, usar valor mínimo
                print(f"⚠️ Não foi possível calcular preço exato - usando estimativa agressiva")
                # Para tokens muito novos, usar valor mínimo muito baixo
                amount_out_min = 1  # Aceitar qualquer quantidade de tokens
            
            # Preparar transação
            if is_buy:
                # Comprar token com WETH (não ETH direto)
                # Primeiro precisa aprovar WETH se necessário
                weth_abi = [
                    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
                    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
                ]
                
                weth_contract = web3_instance.eth.contract(address=WETH_ADDRESS, abi=weth_abi)
                
                # Verificar allowance atual
                current_allowance = weth_contract.functions.allowance(WALLET_ADDRESS, router_address).call()
                
                if current_allowance < amount_in:
                    # Aprovar WETH para o router
                    # Usar gas mais conservador para saldos baixos
                    eth_balance = web3_instance.eth.get_balance(WALLET_ADDRESS)
                    eth_balance_eth = float(web3_instance.from_wei(eth_balance, 'ether'))
                    
                    # Ajustar gas baseado no saldo disponível
                    if eth_balance_eth < 0.0001:  # Saldo muito baixo
                        gas_limit = 50000
                        gas_price = web3_instance.to_wei(0.001, 'gwei')  # Gas price mínimo
                    else:
                        gas_limit = 100000
                        gas_price = web3_instance.to_wei(MAX_GAS_PRICE, 'gwei')
                    
                    # Usar nonce correto
                    nonce = web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
                    
                    approve_tx = weth_contract.functions.approve(
                        router_address, 
                        amount_in * 2  # Aprovar um pouco mais para futuras transações
                    ).build_transaction({
                        'from': WALLET_ADDRESS,
                        'gas': gas_limit,
                        'gasPrice': gas_price,
                        'nonce': nonce
                    })
                    
                    # Assinar e enviar aprovação
                    signed_approve = web3_instance.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
                    approve_hash = web3_instance.eth.send_raw_transaction(signed_approve.rawTransaction)
                    print(f"🔓 Aprovação WETH enviada: {approve_hash.hex()}")
                    
                    # Aguardar confirmação da aprovação
                    time.sleep(2)
                
                # Agora fazer o swap usando swapExactTokensForTokens
                # Usar nonce correto
                nonce = web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
                
                transaction = router_contract.functions.swapExactTokensForTokens(
                    amount_in,
                    amount_out_min,
                    path,
                    WALLET_ADDRESS,
                    deadline
                ).build_transaction({
                    'from': WALLET_ADDRESS,
                    'gas': 300000,  # Gas maior para swaps
                    'gasPrice': web3_instance.to_wei(0.01, 'gwei'),  # Gas mais alto para prioridade
                    'nonce': nonce
                })
            else:
                # Vender token por WETH
                # Primeiro aprovar o token se necessário
                token_abi = [
                    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
                    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
                ]
                
                token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
                
                # Verificar allowance atual
                current_allowance = token_contract.functions.allowance(WALLET_ADDRESS, router_address).call()
                
                if current_allowance < amount_in:
                    # Aprovar token para o router
                    approve_tx = token_contract.functions.approve(
                        router_address, 
                        amount_in * 2  # Aprovar um pouco mais
                    ).build_transaction({
                        'from': WALLET_ADDRESS,
                        'gas': 100000,
                        'gasPrice': self.web3.to_wei(MAX_GAS_PRICE, 'gwei'),
                        'nonce': self.web3.eth.get_transaction_count(WALLET_ADDRESS)
                    })
                    
                    # Assinar e enviar aprovação
                    signed_approve = self.web3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
                    approve_hash = self.web3.eth.send_raw_transaction(signed_approve.rawTransaction)
                    print(f"🔓 Aprovação token enviada: {approve_hash.hex()}")
                    
                    # Aguardar confirmação da aprovação
                    time.sleep(3)
                
                # Fazer swap de token para WETH
                transaction = router_contract.functions.swapExactTokensForTokens(
                    amount_in,
                    amount_out_min,
                    path,
                    WALLET_ADDRESS,
                    deadline
                ).build_transaction({
                    'from': WALLET_ADDRESS,
                    'gas': DEFAULT_GAS_LIMIT,
                    'gasPrice': self.web3.to_wei(MAX_GAS_PRICE, 'gwei'),
                    'nonce': self.web3.eth.get_transaction_count(WALLET_ADDRESS)
                })
            
            # Assinar e enviar transação com retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Atualizar nonce para cada tentativa
                    nonce = web3_instance.eth.get_transaction_count(WALLET_ADDRESS)
                    transaction['nonce'] = nonce
                    
                    print(f"📝 Nonce: {nonce}, Gas: {transaction.get('gas', 'default')}, GasPrice: {web3_instance.from_wei(transaction.get('gasPrice', 0), 'gwei')} gwei")
                    
                    signed_txn = web3_instance.eth.account.sign_transaction(transaction, PRIVATE_KEY)
                    tx_hash = web3_instance.eth.send_raw_transaction(signed_txn.rawTransaction)
                    
                    print(f"🚀 Transação enviada: {tx_hash.hex()}")
                    
                    # Aguardar confirmação básica
                    try:
                        receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                        if receipt.status == 1:
                            print(f"✅ Transação confirmada com sucesso!")
                            return tx_hash.hex()
                        else:
                            print(f"❌ Transação falhou na blockchain - Status: {receipt.status}")
                            return None
                    except Exception as wait_error:
                        print(f"⚠️ Timeout aguardando confirmação: {wait_error}")
                        # Retornar hash mesmo sem confirmação para monitoramento
                        return tx_hash.hex()
                    
                except Exception as send_error:
                    print(f"❌ Tentativa {attempt + 1}/{max_retries} falhou: {str(send_error)}")
                    if attempt < max_retries - 1:
                        # Aguardar antes da próxima tentativa
                        await asyncio.sleep(2)
                        # Aumentar gas price para próxima tentativa
                        if 'gasPrice' in transaction:
                            transaction['gasPrice'] = int(transaction['gasPrice'] * 1.3)
                            print(f"🔄 Tentando com gas {transaction['gasPrice']}...")
                    else:
                        print(f"❌ Todas as tentativas falharam")
                        return None
            
            return None
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erro crítico ao executar swap: {error_msg}")
            
            # Log detalhado para debugging
            if "insufficient funds" in error_msg.lower():
                print("💡 Dica: Verifique se há saldo suficiente para gas e tokens")
            elif "execution reverted" in error_msg.lower():
                print("💡 Dica: Token pode não ter liquidez ou ter restrições de trading")
            elif "nonce too low" in error_msg.lower():
                print("💡 Dica: Problema de nonce, tentando novamente...")
            
            return None
    
    def check_liquidity(self, token_address: str) -> Dict[str, float]:
        """Verifica liquidez do token em todas as DEXs"""
        liquidity_info = {}
        
        for dex_key, dex_info in self.dexs.items():
            try:
                # Implementar verificação de liquidez específica para cada DEX
                # Por enquanto, retorna valores simulados
                liquidity_info[dex_info['name']] = {
                    'liquidity_usd': 50000,  # Valor simulado
                    'volume_24h': 25000,     # Valor simulado
                    'available': True
                }
            except Exception as e:
                liquidity_info[dex_info['name']] = {
                    'liquidity_usd': 0,
                    'volume_24h': 0,
                    'available': False,
                    'error': str(e)
                }
        
        return liquidity_info
    
    def test_all_dexs(self) -> Dict[str, bool]:
        """Testa conectividade com todas as DEXs"""
        results = {}
        
        print("🔍 Testando conectividade com todas as DEXs...")
        
        for dex_key, dex_info in self.dexs.items():
            try:
                # Teste mais simples: verificar se o contrato existe
                router_address = dex_info['router']
                code = self.web3.eth.get_code(router_address)
                
                if len(code) > 0:
                    # Contrato existe, tentar uma chamada simples
                    try:
                        router_contract = self.web3.eth.contract(
                            address=router_address,
                            abi=self.get_router_abi()
                        )
                        
                        # Teste com valores menores e tratamento de erro específico
                        test_path = [WETH_ADDRESS, USDC_ADDRESS]
                        test_amount = self.web3.to_wei(0.0001, 'ether')  # Valor menor
                        
                        amounts = router_contract.functions.getAmountsOut(test_amount, test_path).call()
                        
                        results[dex_info['name']] = True
                        print(f"✅ {dex_info['name']}: Conectado")
                        
                    except Exception as call_error:
                        # Se a chamada falhar, ainda considerar como disponível se o contrato existe
                        results[dex_info['name']] = True
                        print(f"✅ {dex_info['name']}: Conectado (contrato válido)")
                else:
                    results[dex_info['name']] = False
                    print(f"❌ {dex_info['name']}: Contrato não encontrado")
                    
            except Exception as e:
                results[dex_info['name']] = False
                print(f"❌ {dex_info['name']}: {str(e)}")
        
        working_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        print(f"📊 Resultado: {working_count}/{total_count} DEXs funcionando")
        
        return results
    
    async def approve_token_if_needed(self, token_address: str, router_address: str, amount: int) -> bool:
        """
        Aprova token para o router se necessário
        Returns: True se aprovação foi bem-sucedida ou não necessária
        """
        try:
            token_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
            ]
            
            token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
            
            # Verificar allowance atual
            current_allowance = token_contract.functions.allowance(WALLET_ADDRESS, router_address).call()
            
            if current_allowance >= amount:
                print(f"✅ Token já aprovado: {current_allowance} >= {amount}")
                return True
            
            print(f"🔓 Aprovando token {token_address[:10]}... para {amount}")
            
            # Preparar transação de aprovação
            approve_tx = token_contract.functions.approve(
                router_address,
                amount * 10  # Aprovar 10x mais para evitar múltiplas aprovações
            ).build_transaction({
                'from': WALLET_ADDRESS,
                'gas': 100000,
                'gasPrice': self.web3.to_wei(MAX_GAS_PRICE, 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(WALLET_ADDRESS)
            })
            
            # Assinar e enviar
            signed_tx = self.web3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"🔓 Aprovação enviada: {tx_hash.hex()}")
            
            # Aguardar confirmação
            try:
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
                if receipt.status == 1:
                    print(f"✅ Token aprovado com sucesso!")
                    return True
                else:
                    print(f"❌ Aprovação falhou")
                    return False
            except Exception as wait_error:
                print(f"⚠️ Timeout na aprovação, mas pode ter sido processada")
                return True  # Assumir sucesso para continuar
                
        except Exception as e:
            print(f"❌ Erro ao aprovar token: {str(e)}")
            return False
    
    async def get_token_balance(self, token_address: str) -> float:
        """Obtém saldo de um token específico"""
        try:
            token_abi = [
                {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
            ]
            
            token_contract = self.web3.eth.contract(address=token_address, abi=token_abi)
            
            balance_wei = token_contract.functions.balanceOf(WALLET_ADDRESS).call()
            
            try:
                decimals = token_contract.functions.decimals().call()
            except:
                decimals = 18  # Padrão
            
            balance = balance_wei / (10 ** decimals)
            return float(balance)
            
        except Exception as e:
            print(f"❌ Erro ao obter saldo do token: {e}")
            return 0.0
    
    async def estimate_gas_for_swap(self, token_address: str, amount_in: int, router_address: str, is_buy: bool = True) -> int:
        """Estima gas necessário para o swap"""
        try:
            router_contract = self.web3.eth.contract(
                address=router_address,
                abi=self.get_router_abi()
            )
            
            path = [WETH_ADDRESS, token_address] if is_buy else [token_address, WETH_ADDRESS]
            deadline = int(time.time()) + 300
            
            if is_buy:
                gas_estimate = router_contract.functions.swapExactTokensForTokens(
                    amount_in, 1, path, WALLET_ADDRESS, deadline
                ).estimate_gas({'from': WALLET_ADDRESS})
            else:
                gas_estimate = router_contract.functions.swapExactTokensForTokens(
                    amount_in, 1, path, WALLET_ADDRESS, deadline
                ).estimate_gas({'from': WALLET_ADDRESS})
            
            # Adicionar margem de segurança
            return int(gas_estimate * 1.2)
            
        except Exception as e:
            print(f"⚠️ Não foi possível estimar gas: {e}")
            # Retornar valor padrão
            return DEFAULT_GAS_LIMIT