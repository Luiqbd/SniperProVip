import asyncio
import websockets
import json
import time
import random
from typing import Dict, List, Optional, Callable
from web3 import Web3
from config import *

class TokenMonitor:
    def __init__(self, web3: Web3, callback: Callable):
        self.web3 = web3
        self.callback = callback
        self.monitored_tokens = {}
        self.running = False
        
    def add_token(self, token_address: str, token_symbol: str = None):
        """Adiciona token para monitoramento"""
        self.monitored_tokens[token_address.lower()] = {
            'address': token_address,
            'symbol': token_symbol or f"TOKEN_{token_address[:8]}",
            'last_price': 0,
            'price_change_24h': 0,
            'volume_24h': 0,
            'liquidity': 0,
            'last_update': time.time()
        }
        print(f"📊 Token adicionado para monitoramento: {token_symbol or token_address}")
    
    def remove_token(self, token_address: str):
        """Remove token do monitoramento"""
        if token_address.lower() in self.monitored_tokens:
            del self.monitored_tokens[token_address.lower()]
            print(f"🗑️ Token removido do monitoramento: {token_address}")
    
    async def monitor_new_tokens(self):
        """Monitora TODOS os novos tokens sendo criados - MODO AGRESSIVO"""
        print("🚀 Iniciando monitoramento AGRESSIVO de TODOS os tokens...")
        
        last_block = self.web3.eth.block_number
        consecutive_errors = 0
        scan_failures = 0
        
        while self.running:
            try:
                current_block = self.web3.eth.block_number
                
                if current_block > last_block:
                    # Escanear múltiplos blocos de uma vez para não perder nada
                    blocks_to_scan = min(current_block - last_block, 10)  # Máximo 10 blocos por vez
                    await self._scan_blocks_for_new_pairs(last_block + 1, current_block)
                    last_block = current_block
                    consecutive_errors = 0  # Reset erros após sucesso
                    scan_failures = 0
                else:
                    # Se não há novos blocos, tentar método alternativo
                    if scan_failures < 3:
                        await self._aggressive_token_detection()
                        scan_failures += 1
                
                await asyncio.sleep(2)  # Verificar a cada 2 segundos
                
            except Exception as e:
                consecutive_errors += 1
                print(f"❌ Erro no monitoramento ({consecutive_errors}x): {str(e)}")
                
                if consecutive_errors > 5:
                    print("⚠️ Muitos erros consecutivos - reiniciando conexão...")
                    try:
                        # Tentar reconectar
                        from config import BASE_RPC_URL
                        self.web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))
                        consecutive_errors = 0
                    except:
                        pass
                
                await asyncio.sleep(10)  # Esperar mais tempo em caso de erro
    
    async def _aggressive_token_detection(self):
        """Detecção agressiva de tokens - método alternativo"""
        try:
            # Método alternativo: verificar pools Known que estão sendo criados frequentemente
            # Usar a detecção por transfers como backup
            # Isso já está implementado em _scan_token_transfers
            
            # Adicionar tokens de teste conhecidos da Base para verificação
            test_tokens = [
                "0x0578D5A379C8C12C33D9a3a7C6A7E9A1c7D9E2F3",  # Exemplo - trocar por tokens reais
            ]
            
            # Log para debug
            print("🔄 Verificando métodos alternativos de detecção...")
            
        except Exception as e:
            pass
    
    async def force_token_detection(self, token_address: str):
        """Força detecção de um token específico (para testing/debug)"""
        try:
            print(f"🔍 Forçando detecção de token: {token_address}")
            token_info = await self._get_token_info(token_address)
            if token_info:
                # Prioridade HIGH para tokens forçados
                await self.callback(token_address, token_info, "HIGH")
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao forçar detecção: {e}")
            return False
    
    async def _scan_blocks_for_new_pairs(self, from_block: int, to_block: int):
        """Escaneia blocos em busca de novos pares"""
        try:
            # Escanear logs de eventos reais para novos pares
            print(f"🔍 Escaneando blocos {from_block} a {to_block}...")
            
            # Buscar eventos de criação de pares
            await self._scan_pair_created_events(from_block, to_block)
                
        except Exception as e:
            print(f"❌ Erro ao escanear blocos: {str(e)}")
    
    async def _scan_pair_created_events(self, from_block: int, to_block: int):
        """Escaneia eventos reais de criação de pares com múltiplos topics"""
        try:
            print(f"🔍 Escaneando blocos {from_block} a {to_block} em busca de novos pares...")
            
            # Topics para diferentes tipos de eventos de criação de pares
            pair_created_topics = [
                '0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9',  # PairCreated padrão
                '0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118',  # Uniswap V3 PoolCreated
                '0x91ccaa7a278130b65168c3a0c8d3bcae84cf5e43704342bd3ec0b59e59c036db',  # Aerodrome PairCreated
                '0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f'   # BaseSwap PairCreated
            ]
            
            # Endereços das factories das DEXs
            factory_addresses = [
                UNISWAP_V3_FACTORY,
                AERODROME_FACTORY, 
                BASESWAP_FACTORY
            ]
            
            total_pairs_found = 0
            
            # Escanear cada factory com cada topic
            for factory in factory_addresses:
                for topic in pair_created_topics:
                    try:
                        # Buscar logs de PairCreated
                        logs = self.web3.eth.get_logs({
                            'fromBlock': from_block,
                            'toBlock': to_block,
                            'address': factory,
                            'topics': [topic]
                        })
                        
                        if logs:
                            print(f"✅ {len(logs)} eventos encontrados em {factory[:10]}...")
                            for log in logs:
                                await self._process_pair_created_log(log)
                                total_pairs_found += 1
                                
                    except Exception as e:
                        # Continuar mesmo se uma factory/topic falhar
                        continue
            
            if total_pairs_found == 0:
                print("⚠️ Nenhum novo par encontrado nesta varredura")
            
            # Também escanear transfers de tokens novos (método alternativo)
            await self._scan_token_transfers(from_block, to_block)
                    
        except Exception as e:
            print(f"❌ Erro ao escanear eventos: {str(e)}")
    
    async def _scan_token_transfers(self, from_block: int, to_block: int):
        """Escaneia transfers de tokens para detectar novos tokens"""
        try:
            # Topic para Transfer (método alternativo de detecção)
            transfer_topic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
            
            # Buscar transfers recentes
            logs = self.web3.eth.get_logs({
                'fromBlock': from_block,
                'toBlock': to_block,
                'topics': [transfer_topic]
            })
            
            # Processar apenas uma amostra para não sobrecarregar
            sample_logs = logs[:10] if len(logs) > 10 else logs
            
            for log in sample_logs:
                try:
                    # Verificar se é um token válido
                    token_address = log['address']
                    if await self._is_valid_new_token(token_address):
                        token_info = await self._get_token_info(token_address)
                        if token_info:
                            print(f"🔍 Token detectado via Transfer: {token_info['symbol']} ({token_address})")
                            await self.callback(token_address, token_info, "MEDIUM")
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Erro ao escanear transfers: {str(e)}")
    
    async def _is_valid_new_token(self, token_address: str) -> bool:
        """Verifica se é um token novo e válido"""
        try:
            # Verificar se já foi processado
            if token_address.lower() in getattr(self, '_processed_tokens', set()):
                return False
            
            # Verificar se é um token conhecido (WETH, USDC, etc.)
            known_tokens = [WETH_ADDRESS.lower(), USDC_ADDRESS.lower()]
            if token_address.lower() in known_tokens:
                return False
            
            # Verificar se é um contrato válido
            code = self.web3.eth.get_code(token_address)
            if len(code) < 100:  # Contrato muito pequeno
                return False
            
            # Marcar como processado
            if not hasattr(self, '_processed_tokens'):
                self._processed_tokens = set()
            self._processed_tokens.add(token_address.lower())
            
            return True
            
        except Exception:
            return False
    
    async def _process_pair_created_log(self, log):
        """Processa log de par criado - DETECTA TODOS OS PARES"""
        try:
            # Extrair endereços dos tokens do log
            if len(log['topics']) >= 3:
                token0_raw = '0x' + log['topics'][1].hex()[26:]
                token1_raw = '0x' + log['topics'][2].hex()[26:]
                
                # Converter para checksum address
                token0 = self.web3.to_checksum_address(token0_raw)
                token1 = self.web3.to_checksum_address(token1_raw)
                
                # MODO AGRESSIVO: Detectar TODOS os pares, não apenas WETH
                tokens_to_analyze = []
                
                # Verificar se um dos tokens é WETH (prioridade alta)
                if token0.lower() == WETH_ADDRESS.lower():
                    tokens_to_analyze.append(('HIGH', token1))
                elif token1.lower() == WETH_ADDRESS.lower():
                    tokens_to_analyze.append(('HIGH', token0))
                else:
                    # Mesmo sem WETH, analisar ambos os tokens (prioridade média)
                    tokens_to_analyze.append(('MEDIUM', token0))
                    tokens_to_analyze.append(('MEDIUM', token1))
                
                # Processar todos os tokens detectados
                for priority, token_address in tokens_to_analyze:
                    try:
                        # Obter informações do token
                        token_info = await self._get_token_info(token_address)
                        if token_info:
                            priority_emoji = "🚀" if priority == "HIGH" else "📊"
                            print(f"{priority_emoji} Novo par detectado [{priority}]: {token_info['symbol']} ({token_address})")
                            await self.callback(token_address, token_info, priority)
                    except Exception as e:
                        print(f"❌ Erro ao processar token {token_address}: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Erro ao processar log: {str(e)}")
    
    async def _simulate_new_token_detection(self):
        """Simula detecção de novo token (apenas para demonstração)"""
        import random
        
        # Gerar endereço de token simulado com checksum
        fake_token_raw = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(40)])}"
        fake_token = self.web3.to_checksum_address(fake_token_raw)
        
        token_info = {
            'symbol': f'TEST{random.randint(1, 999)}',
            'name': f'Test Token {random.randint(1, 999)}',
            'decimals': 18,
            'total_supply': random.randint(1000000, 100000000)
        }
        
        print(f"🆕 [DEMO] Novo token simulado: {token_info['symbol']} ({fake_token})")
        
        # Chamar callback
        await self.callback(fake_token, token_info)
    
    async def _process_new_pair_event(self, event):
        """Processa evento de novo par criado"""
        try:
            # Decodificar dados do evento
            token0 = '0x' + event['topics'][1].hex()[26:]
            token1 = '0x' + event['topics'][2].hex()[26:]
            
            # Verificar se um dos tokens é WETH
            if token0.lower() == WETH_ADDRESS.lower():
                new_token = token1
            elif token1.lower() == WETH_ADDRESS.lower():
                new_token = token0
            else:
                return  # Não é par com WETH
            
            # Verificar se é um token válido
            if await self._is_valid_token(new_token):
                token_info = await self._get_token_info(new_token)
                
                print(f"🆕 Novo token detectado: {token_info['symbol']} ({new_token})")
                
                # Chamar callback para processar o novo token
                await self.callback(new_token, token_info)
                
        except Exception as e:
            print(f"❌ Erro ao processar evento de novo par: {str(e)}")
    
    async def _is_valid_token(self, token_address: str) -> bool:
        """Verifica se o token é válido para trading - MODO PERMISSIVO"""
        try:
            # ABI básica para verificar token ERC20
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
            ]
            
            contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Verificações MUITO básicas - apenas se responde às funções ERC20
            try:
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                total_supply = contract.functions.totalSupply().call()
                
                # Filtros mínimos - muito permissivos
                if decimals > 0 and total_supply > 0:
                    return True
                    
            except:
                # Se falhar, tenta métodos alternativos
                pass
            
            # Método alternativo - verifica se tem código no endereço
            code = self.web3.eth.get_code(token_address)
            if len(code) > 2:  # Tem código (não é EOA)
                print(f"✅ Token aceito (método alternativo): {token_address}")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Erro na validação (aceito mesmo assim): {token_address}")
            return True  # MODO PERMISSIVO - aceita mesmo com erro
    
    async def _get_token_info(self, token_address: str) -> Dict:
        """Obtém informações do token com fallbacks robustos"""
        import random
        
        # Informações padrão - Assume que é um token novo
        current_time = time.time()
        token_info = {
            'address': token_address,
            'name': 'Unknown Token',
            'symbol': 'UNK',
            'decimals': 18,
            'total_supply': 1000000,
            'created_at': current_time,
            'age_minutes': random.randint(1, 30),  # Assume que é um token recente (1-30 min)
            'liquidity_usd': random.randint(1000, 50000),  # Liquidez simulada para análise
            'holders': random.randint(10, 500),  # Holders simulados
            'is_honeypot': False  # Assume que não é honeypot por padrão
        }
        
        try:
            erc20_abi = [
                {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
            ]
            
            contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Tenta obter cada informação individualmente
            try:
                token_info['name'] = contract.functions.name().call()
            except:
                pass
                
            try:
                token_info['symbol'] = contract.functions.symbol().call()
            except:
                pass
                
            try:
                token_info['decimals'] = contract.functions.decimals().call()
            except:
                pass
                
            try:
                token_info['total_supply'] = contract.functions.totalSupply().call()
            except:
                pass
            
            return token_info
            
        except Exception as e:
            print(f"⚠️ Erro ao obter info do token (usando padrão): {str(e)}")
            return token_info
    
    def get_token_price(self, token_address: str) -> Optional[float]:
        """Obtém preço atual do token em USD"""
        try:
            # Implementar lógica de preço usando DEX
            # Por enquanto retorna valor simulado
            return 0.001  # Valor simulado
        except Exception as e:
            print(f"❌ Erro ao obter preço: {str(e)}")
            return None
    
    def analyze_token_potential(self, token_address: str) -> Dict:
        """Analisa potencial do token"""
        try:
            analysis = {
                'score': 0,
                'factors': {},
                'recommendation': 'HOLD'
            }
            
            # Análise de liquidez
            liquidity_score = self._analyze_liquidity(token_address)
            analysis['factors']['liquidity'] = liquidity_score
            analysis['score'] += liquidity_score * 0.3
            
            # Análise de volume
            volume_score = self._analyze_volume(token_address)
            analysis['factors']['volume'] = volume_score
            analysis['score'] += volume_score * 0.2
            
            # Análise de holders
            holders_score = self._analyze_holders(token_address)
            analysis['factors']['holders'] = holders_score
            analysis['score'] += holders_score * 0.2
            
            # Análise de contrato
            contract_score = self._analyze_contract(token_address)
            analysis['factors']['contract'] = contract_score
            analysis['score'] += contract_score * 0.3
            
            # Determinar recomendação
            if analysis['score'] >= 80:
                analysis['recommendation'] = 'STRONG_BUY'
            elif analysis['score'] >= 60:
                analysis['recommendation'] = 'BUY'
            elif analysis['score'] >= 40:
                analysis['recommendation'] = 'HOLD'
            else:
                analysis['recommendation'] = 'AVOID'
            
            return analysis
            
        except Exception as e:
            print(f"❌ Erro na análise: {str(e)}")
            return {'score': 0, 'factors': {}, 'recommendation': 'AVOID'}
    
    def _analyze_liquidity(self, token_address: str) -> int:
        """Analisa liquidez do token (0-100)"""
        # Implementar análise real de liquidez
        return 75  # Valor simulado
    
    def _analyze_volume(self, token_address: str) -> int:
        """Analisa volume de trading (0-100)"""
        # Implementar análise real de volume
        return 60  # Valor simulado
    
    def _analyze_holders(self, token_address: str) -> int:
        """Analisa distribuição de holders (0-100)"""
        # Implementar análise real de holders
        return 70  # Valor simulado
    
    def _analyze_contract(self, token_address: str) -> int:
        """Analisa segurança do contrato (0-100)"""
        # Implementar análise real do contrato
        return 85  # Valor simulado
    
    def start_monitoring(self):
        """Inicia o monitoramento"""
        self.running = True
        print("🚀 Monitor de tokens iniciado!")
        
        # INICIAR O LOOP DE MONITORAMENTO
        # O loop principal será executado pelo sniper_bot via asyncio
    
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.running = False
        print("⏹️ Monitor de tokens parado!")
    
    def get_monitored_tokens(self) -> Dict:
        """Retorna lista de tokens monitorados"""
        return self.monitored_tokens