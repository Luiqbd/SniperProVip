"""
Estratégia Agressiva para Crescimento Rápido
Otimizada para saldos pequenos (0.001990 WETH) com foco em lucros rápidos e altos
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from config import *

class AggressiveStrategy:
    def __init__(self, sniper_bot):
        self.sniper_bot = sniper_bot
        self.initial_balance = INITIAL_WETH_BALANCE
        self.current_balance = INITIAL_WETH_BALANCE
        self.profit_history = []
        self.trade_history = []
        self.successful_trades = 0
        self.failed_trades = 0
        
        # Configurações agressivas para crescimento rápido
        self.base_trade_amount = TRADE_AMOUNT_WETH  # 0.000398 WETH (20% do saldo)
        self.max_trade_percentage = 0.35  # Até 35% do saldo por trade (muito agressivo)
        self.profit_target = 0.30  # 30% de lucro por trade (agressivo)
        self.stop_loss = 0.15  # 15% de stop loss (controlado)
        self.quick_profit_threshold = 0.10  # Vender com 10% de lucro se muito volátil
        
        # Sistema de scaling dinâmico
        self.scaling_factor = 1.0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3
        
        # Filtros agressivos para tokens
        self.min_score_aggressive = 10  # Score mínimo extremamente baixo para máximas oportunidades
        self.memecoin_bonus = 15  # Bonus para memecoins
        self.new_token_bonus = 10  # Bonus para tokens novos (< 1 hora)
        
        # Timing agressivo
        self.hold_time_min = 30  # Mínimo 30 segundos
        self.hold_time_max = 300  # Máximo 5 minutos (muito rápido)
        self.quick_exit_time = 60  # Saída rápida em 1 minuto se lucro >= 10%
        
        # Configurações de risco
        self.max_simultaneous_positions = 8  # Máximo 8 posições simultâneas para mais oportunidades
        self.current_positions = {}
        self.position_sizes = {}
        self.position_timeout = 600  # 10 minutos timeout para limpeza automática
        
        logging.info("🚀 Estratégia Agressiva inicializada para crescimento rápido")
    
    def cleanup_old_positions(self):
        """Remove posições antigas que passaram do timeout"""
        import time
        current_time = time.time()
        positions_to_remove = []
        
        for token_address, position in self.current_positions.items():
            position_age = current_time - position.get('timestamp', current_time)
            if position_age > self.position_timeout:
                positions_to_remove.append(token_address)
                print(f"🧹 Removendo posição antiga: {position.get('symbol', 'UNK')} ({position_age/60:.1f} min)")
        
        for token_address in positions_to_remove:
            del self.current_positions[token_address]
            if token_address in self.position_sizes:
                del self.position_sizes[token_address]
    
    def reset_positions(self):
        """Reset todas as posições (para debug/emergência)"""
        print(f"🔄 Resetando {len(self.current_positions)} posições")
        self.current_positions.clear()
        self.position_sizes.clear()
        
    def calculate_dynamic_trade_amount(self) -> float:
        """Calcula valor dinâmico do trade baseado no saldo atual e performance"""
        current_weth = self.sniper_bot._weth_balance_cache or self.current_balance
        
        # Base: 20% do saldo atual
        base_amount = current_weth * 0.20
        
        # Ajustar baseado na performance recente
        if self.consecutive_wins >= 2:
            # Aumentar após vitórias consecutivas
            scaling = min(1.5, 1.0 + (self.consecutive_wins * 0.15))
            base_amount *= scaling
            print(f"🚀 Scaling UP: {scaling:.2f}x após {self.consecutive_wins} vitórias")
        elif self.consecutive_losses >= 2:
            # Diminuir após perdas consecutivas
            scaling = max(0.5, 1.0 - (self.consecutive_losses * 0.15))
            base_amount *= scaling
            print(f"⚠️ Scaling DOWN: {scaling:.2f}x após {self.consecutive_losses} perdas")
        
        # Limites de segurança
        max_amount = current_weth * self.max_trade_percentage
        min_amount = MIN_TRADE_AMOUNT
        
        final_amount = max(min_amount, min(base_amount, max_amount))
        
        print(f"💰 Trade dinâmico: {final_amount:.6f} WETH ({(final_amount/current_weth)*100:.1f}% do saldo)")
        return final_amount
    
    def should_buy_token(self, token_address: str, token_info: Dict, ai_score: int, traditional_score: float) -> Tuple[bool, str]:
        """Decide se deve comprar o token com critérios agressivos"""
        
        # Score combinado com peso maior para IA
        combined_score = int(ai_score * 0.8 + traditional_score * 0.2)
        
        # Bonus para diferentes tipos de tokens
        bonus = 0
        reasons = []
        
        # Bonus para memecoins
        if MEMECOIN_MODE and any(keyword in token_info.get('name', '').lower() for keyword in ['doge', 'pepe', 'shib', 'moon', 'safe', 'baby']):
            bonus += self.memecoin_bonus
            reasons.append(f"Memecoin (+{self.memecoin_bonus})")
        
        # Bonus para tokens muito novos (oportunidade early)
        token_age = token_info.get('age_minutes', 999)
        if token_age < 60:  # Menos de 1 hora
            bonus += self.new_token_bonus
            reasons.append(f"Token novo (+{self.new_token_bonus})")
        
        # Bonus para alta liquidez
        liquidity = token_info.get('liquidity_usd', 0)
        if liquidity > 10000:
            bonus += 5
            reasons.append("Alta liquidez (+5)")
        
        # Bonus para muitos holders
        holders = token_info.get('holders', 0)
        if holders > 100:
            bonus += 5
            reasons.append("Muitos holders (+5)")
        
        final_score = combined_score + bonus
        
        # Critério agressivo: aceitar scores baixos para mais oportunidades
        min_score = self.min_score_aggressive
        
        # Limpar posições antigas primeiro
        self.cleanup_old_positions()
        
        # Verificar se já temos muitas posições
        if len(self.current_positions) >= self.max_simultaneous_positions:
            return False, f"Máximo de posições atingido ({self.max_simultaneous_positions})"
        
        # Verificar se temos saldo suficiente
        trade_amount = self.calculate_dynamic_trade_amount()
        current_weth = self.sniper_bot._weth_balance_cache or self.current_balance
        if trade_amount > current_weth * 0.9:  # Deixar 10% para gas
            return False, "Saldo insuficiente para trade"
        
        should_buy = final_score >= min_score
        
        # MODO ULTRA AGRESSIVO: Comprar tokens muito novos mesmo com score baixo
        if not should_buy and token_info.get('age_minutes', 999) <= 30:
            should_buy = True
            reason = f"ULTRA AGRESSIVO: Token muito novo ({token_info.get('age_minutes', 0)} min) - Score: {final_score}"
        else:
            reason = f"Score: {final_score}/{min_score} (base: {combined_score}, bonus: {bonus})"
            if reasons:
                reason += f" - Bonus: {', '.join(reasons)}"
        
        if should_buy:
            print(f"✅ COMPRAR: {token_info.get('symbol', 'UNK')} - {reason}")
        else:
            print(f"❌ IGNORAR: {token_info.get('symbol', 'UNK')} - {reason}")
        
        return should_buy, reason
    
    async def execute_buy_strategy(self, token_address: str, token_info: Dict) -> bool:
        """Executa estratégia de compra agressiva"""
        try:
            trade_amount = self.calculate_dynamic_trade_amount()
            
            # Registrar posição
            import time
            self.current_positions[token_address] = {
                'symbol': token_info.get('symbol', 'UNK'),
                'buy_time': datetime.now(),
                'timestamp': time.time(),  # Para limpeza automática
                'buy_amount': trade_amount,
                'target_profit': self.profit_target,
                'stop_loss': self.stop_loss,
                'quick_exit_triggered': False
            }
            
            print(f"🎯 Estratégia para {token_info.get('symbol', 'UNK')}:")
            print(f"   💰 Valor: {trade_amount:.6f} WETH")
            print(f"   🎯 Lucro alvo: {self.profit_target*100:.0f}%")
            print(f"   🛑 Stop loss: {self.stop_loss*100:.0f}%")
            print(f"   ⚡ Saída rápida: {self.quick_profit_threshold*100:.0f}% em {self.quick_exit_time}s")
            
            # Agendar monitoramento da posição
            asyncio.create_task(self.monitor_position(token_address))
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na estratégia de compra: {str(e)}")
            return False
    
    async def monitor_position(self, token_address: str):
        """Monitora posição e executa saída baseada na estratégia"""
        if token_address not in self.current_positions:
            return
        
        position = self.current_positions[token_address]
        start_time = position['buy_time']
        
        print(f"👁️ Monitorando posição: {position['symbol']}")
        
        while token_address in self.current_positions:
            try:
                await asyncio.sleep(5)  # Verificar a cada 5 segundos
                
                current_time = datetime.now()
                hold_time = (current_time - start_time).total_seconds()
                
                # Verificar se deve fazer saída rápida
                if hold_time >= self.quick_exit_time and not position['quick_exit_triggered']:
                    # Verificar preço atual e decidir saída rápida
                    if await self.check_quick_exit(token_address, position):
                        position['quick_exit_triggered'] = True
                
                # Verificar saída por tempo máximo
                if hold_time >= self.hold_time_max:
                    print(f"⏰ Tempo máximo atingido para {position['symbol']} ({hold_time:.0f}s)")
                    await self.execute_sell_strategy(token_address, "Tempo máximo")
                    break
                
                # Verificar stop loss e take profit
                if await self.check_exit_conditions(token_address, position):
                    break
                    
            except Exception as e:
                print(f"❌ Erro no monitoramento de {position['symbol']}: {str(e)}")
                await asyncio.sleep(10)
    
    async def check_quick_exit(self, token_address: str, position: Dict) -> bool:
        """Verifica se deve fazer saída rápida com lucro pequeno"""
        try:
            # Obter preço atual do token
            dex_handler = self.sniper_bot.dex_handler
            buy_amount_wei = self.sniper_bot.web3.to_wei(position['buy_amount'], 'ether')
            
            # Tentar obter preço atual
            try:
                best_dex, current_value, router = await dex_handler.get_best_price(
                    token_address, buy_amount_wei, is_buy=False
                )
                
                if current_value > 0:
                    current_value_eth = self.sniper_bot.web3.from_wei(current_value, 'ether')
                    current_profit = (current_value_eth - position['buy_amount']) / position['buy_amount']
                    
                    print(f"💹 {position['symbol']}: Lucro atual {current_profit*100:.1f}%")
                    
                    # Saída rápida se lucro >= threshold
                    if current_profit >= self.quick_profit_threshold:
                        print(f"⚡ SAÍDA RÁPIDA: {position['symbol']} com {current_profit*100:.1f}% de lucro")
                        await self.execute_sell_strategy(token_address, f"Saída rápida ({current_profit*100:.1f}%)")
                        return True
                else:
                    print(f"⚠️ Não foi possível obter preço atual para {position['symbol']}")
                    
            except Exception as price_error:
                print(f"⚠️ Erro ao verificar preço de {position['symbol']}: {str(price_error)}")
            
            return False
            
        except Exception as e:
            print(f"❌ Erro na verificação de saída rápida: {str(e)}")
            return False
    
    async def check_exit_conditions(self, token_address: str, position: Dict) -> bool:
        """Verifica condições de saída (stop loss / take profit)"""
        try:
            # Implementar verificação real de preço aqui
            # Por enquanto, simular baseado em probabilidades
            
            import random
            
            # Simular movimento de preço
            price_change = random.uniform(-0.25, 0.40)  # -25% a +40%
            
            if price_change <= -self.stop_loss:
                print(f"🛑 Stop loss ativado: {position['symbol']} ({price_change*100:.1f}%)")
                await self.execute_sell_strategy(token_address, f"Stop loss ({price_change*100:.1f}%)")
                return True
            elif price_change >= self.profit_target:
                print(f"🎯 Take profit ativado: {position['symbol']} ({price_change*100:.1f}%)")
                await self.execute_sell_strategy(token_address, f"Take profit ({price_change*100:.1f}%)")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro na verificação de condições: {str(e)}")
            return False
    
    async def execute_sell_strategy(self, token_address: str, reason: str):
        """Executa estratégia de venda"""
        if token_address not in self.current_positions:
            return
        
        position = self.current_positions[token_address]
        
        try:
            print(f"💸 Vendendo {position['symbol']} - Razão: {reason}")
            
            # Simular venda (implementar com DEX real)
            profit_loss = random.uniform(-0.15, 0.35)  # -15% a +35%
            
            # Registrar resultado
            trade_result = {
                'token': position['symbol'],
                'buy_time': position['buy_time'],
                'sell_time': datetime.now(),
                'amount': position['buy_amount'],
                'profit_loss': profit_loss,
                'reason': reason
            }
            
            self.trade_history.append(trade_result)
            
            # Atualizar estatísticas
            if profit_loss > 0:
                self.successful_trades += 1
                self.consecutive_wins += 1
                self.consecutive_losses = 0
                print(f"✅ Trade bem-sucedido: +{profit_loss*100:.1f}% ({self.consecutive_wins} vitórias consecutivas)")
            else:
                self.failed_trades += 1
                self.consecutive_losses += 1
                self.consecutive_wins = 0
                print(f"❌ Trade com perda: {profit_loss*100:.1f}% ({self.consecutive_losses} perdas consecutivas)")
            
            # Atualizar saldo
            self.current_balance += position['buy_amount'] * profit_loss
            self.profit_history.append(profit_loss)
            
            # Remover posição
            del self.current_positions[token_address]
            
            # Verificar se precisa pausar após muitas perdas
            if self.consecutive_losses >= self.max_consecutive_losses:
                print(f"⚠️ Muitas perdas consecutivas ({self.consecutive_losses}), pausando por 5 minutos")
                await asyncio.sleep(300)  # Pausar 5 minutos
                self.consecutive_losses = 0  # Reset após pausa
            
        except Exception as e:
            print(f"❌ Erro na venda: {str(e)}")
    
    def get_strategy_stats(self) -> Dict:
        """Retorna estatísticas da estratégia"""
        total_trades = self.successful_trades + self.failed_trades
        win_rate = (self.successful_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = sum(self.profit_history)
        avg_profit = (total_profit / len(self.profit_history)) if self.profit_history else 0
        
        current_balance = self.sniper_bot._weth_balance_cache or self.current_balance
        roi = ((current_balance - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        return {
            'total_trades': total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'current_balance': current_balance,
            'initial_balance': self.initial_balance,
            'roi': roi,
            'consecutive_wins': self.consecutive_wins,
            'consecutive_losses': self.consecutive_losses,
            'active_positions': len(self.current_positions)
        }
    
    def print_strategy_status(self):
        """Imprime status da estratégia"""
        stats = self.get_strategy_stats()
        
        print("\n" + "="*60)
        print("📊 STATUS DA ESTRATÉGIA AGRESSIVA")
        print("="*60)
        print(f"💰 Saldo inicial: {stats['initial_balance']:.6f} WETH")
        print(f"💰 Saldo atual: {stats['current_balance']:.6f} WETH")
        print(f"📈 ROI: {stats['roi']:+.2f}%")
        print(f"🎯 Trades: {stats['total_trades']} (✅{stats['successful_trades']} ❌{stats['failed_trades']})")
        print(f"🏆 Taxa de sucesso: {stats['win_rate']:.1f}%")
        print(f"💎 Lucro médio: {stats['avg_profit']*100:+.1f}%")
        print(f"🔥 Sequência atual: {stats['consecutive_wins']} vitórias, {stats['consecutive_losses']} perdas")
        print(f"📊 Posições ativas: {stats['active_positions']}/{self.max_simultaneous_positions}")
        print("="*60)