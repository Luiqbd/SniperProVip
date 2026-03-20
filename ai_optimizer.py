"""
AI Optimizer - Sistema de IA para otimização automática do sniper
Aprende com o histórico de trades e ajusta estratégias automaticamente
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

class AIOptimizer:
    """
    Sistema de IA que otimiza automaticamente:
    - Valor de compra/venda
    - Timing de vendas
    - Gestão de risco
    - Crescimento do investimento
    """
    
    def __init__(self, sniper_bot):
        self.sniper_bot = sniper_bot
        self.trade_history = deque(maxlen=100)  # Últimos 100 trades
        self.win_rate = 0.5
        self.avg_profit = 0.0
        self.avg_loss = 0.0
        self.current_balance = 0.005  # Saldo inicial estimado
        self.best_profit_streak = 0
        self.current_streak = 0
        self.risk_level = "medium"  # low, medium, high
        self.last_adjustment = time.time()
        
        # Parâmetros atuais (serão ajustados pela IA)
        self.params = {
            "trade_percentage": 0.25,  # % do saldo para cada trade
            "take_profit": 0.03,  # 3% lucro
            "stop_loss": 0.30,  # 30% perda
            "quick_exit": 0.02,  # 2% saída rápida
            "hold_time_max": 120,  # segundos
            "min_liquidity": 0.05,  # ETH mínimo
            "gas_price": 0.01,  # gwei
        }
        
        # Histórico de ajustes
        self.adjustment_history = []
        
    def record_trade(self, token_symbol: str, buy_price: float, sell_price: float, 
                     sold: bool = False, reason: str = ""):
        """Registra um trade para a IA aprender"""
        if not sold:
            return
            
        profit_pct = ((sell_price - buy_price) / buy_price) * 100
        
        trade = {
            "symbol": token_symbol,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "profit_pct": profit_pct,
            "sold": sold,
            "reason": reason,
            "timestamp": time.time(),
            "balance": self.current_balance
        }
        
        self.trade_history.append(trade)
        self._update_statistics()
        
    def _update_statistics(self):
        """Atualiza estatísticas baseadas no histórico"""
        if not self.trade_history:
            return
            
        wins = [t for t in self.trade_history if t["profit_pct"] > 0]
        losses = [t for t in self.trade_history if t["profit_pct"] <= 0]
        
        self.win_rate = len(wins) / len(self.trade_history) if self.trade_history else 0.5
        
        if wins:
            self.avg_profit = sum(t["profit_pct"] for t in wins) / len(wins)
        if losses:
            self.avg_loss = sum(t["profit_pct"] for t in losses) / len(losses)
            
        # Calcular streak atual
        self.current_streak = 0
        for t in reversed(self.trade_history):
            if t["profit_pct"] > 0:
                self.current_streak += 1
            else:
                break
                
    def get_optimal_trade_amount(self) -> float:
        """
        Calcula o valor ideal para o próximo trade
        baseando-se no saldo atual e no histórico
        """
        # Saldo atual
        if self.sniper_bot and self.sniper_bot.web3:
            try:
                eth_balance = self.sniper_bot._get_eth_balance_sync()
                if eth_balance > 0:
                    self.current_balance = eth_balance
            except:
                pass
        
        # Ajustar baseado no risco
        base_percentage = self.params["trade_percentage"]
        
        # Se está em boa sequência, aumentar investimento
        if self.current_streak >= 3:
            base_percentage = min(base_percentage * 1.2, 0.5)  # Max 50%
            print(f"🤖 IA: Streak positivo ({self.current_streak}), aumentando para {base_percentage*100:.0f}%")
        
        # Se está em sequência ruim, diminuir
        if self.current_streak <= -2:
            base_percentage = max(base_percentage * 0.7, 0.1)  # Min 10%
            print(f"🤖 IA: Streak negativo, reduzindo para {base_percentage*100:.0f}%")
            
        # Se saldo baixo, ser mais conservador
        if self.current_balance < 0.003:
            base_percentage = min(base_percentage, 0.2)  # Max 20%
            
        # Se saldo alto, ser mais agressivo
        if self.current_balance > 0.01:
            base_percentage = min(base_percentage * 1.1, 0.6)  # Max 60%
            
        trade_amount = self.current_balance * base_percentage
        
        # Garantir valor mínimo
        return max(trade_amount, 0.0001)  # Mínimo 0.0001 ETH
        
    def should_sell(self, current_profit_pct: float, hold_time: int) -> tuple[bool, str]:
        """
        Decide se deve vender agora
        Retorna: (deve_vender, razão)
        """
        # Take profit
        if current_profit_pct >= self.params["take_profit"]:
            return True, f"Take profit: {current_profit_pct:.1f}%"
            
        # Stop loss
        if current_profit_pct <= -self.params["stop_loss"]:
            return True, f"Stop loss: {current_profit_pct:.1f}%"
            
        # Saída rápida com lucro
        if current_profit_pct >= self.params["quick_exit"] and hold_time >= 20:
            return True, f"Quick exit: {current_profit_pct:.1f}%"
            
        # Tempo máximo
        if hold_time >= self.params["hold_time_max"]:
            return True, f"Tempo máximo: {hold_time}s"
            
        return False, ""
        
    def optimize_parameters(self) -> Dict:
        """
        Otimiza os parâmetros baseando-se no histórico
        Chamado periodicamente para ajustar o comportamento
        """
        if time.time() - self.last_adjustment < 60:  # Só ajusta a cada minuto
            return self.params
            
        self._update_statistics()
        
        # Ajustar take profit baseado no win rate
        if self.win_rate > 0.6:
            # Bom win rate, pode ser mais agressivo
            self.params["take_profit"] = max(self.params["take_profit"] * 0.9, 0.02)
            print(f"🤖 IA: Bom win rate ({self.win_rate*100:.0f}%), reduzindo take profit para {self.params['take_profit']*100:.0f}%")
        elif self.win_rate < 0.4:
            # Win rate baixo, ser mais conservador
            self.params["take_profit"] = min(self.params["take_profit"] * 1.2, 0.10)
            print(f"🤖 IA: Win rate baixo ({self.win_rate*100:.0f}%), aumentando take profit para {self.params['take_profit']*100:.0f}%")
            
        # Ajustar stop loss baseado na perda média
        if self.avg_loss and abs(self.avg_loss) < self.params["stop_loss"]:
            # Perdas menores que stop loss, pode reduzir
            self.params["stop_loss"] = max(abs(self.avg_loss) * 1.2, 0.10)
            print(f"🤖 IA: Ajustando stop loss para {self.params['stop_loss']*100:.0f}%")
            
        # Ajustar percentage de trade baseado no saldo
        if self.current_balance > 0.01:
            self.params["trade_percentage"] = min(self.params["trade_percentage"] * 1.1, 0.6)
        elif self.current_balance < 0.003:
            self.params["trade_percentage"] = max(self.params["trade_percentage"] * 0.8, 0.1)
            
        self.last_adjustment = time.time()
        
        # Registrar ajuste
        self.adjustment_history.append({
            "timestamp": time.time(),
            "win_rate": self.win_rate,
            "params": self.params.copy(),
            "balance": self.current_balance
        })
        
        return self.params
        
    def get_recommendation(self) -> str:
        """Retorna recomendação baseada na análise"""
        if self.win_rate > 0.7:
            return "🔥🔥🔥 OTIMO! Continue assim!"
        elif self.win_rate > 0.5:
            return "👍 Bom desempenho"
        elif self.win_rate > 0.3:
            return "⚠️ Desempenho abaixo do esperado"
        else:
            return "❌ Ajuste necessario"
            
    def get_status(self) -> Dict:
        """Retorna status da IA"""
        return {
            "win_rate": f"{self.win_rate*100:.1f}%",
            "trades": len(self.trade_history),
            "current_streak": self.current_streak,
            "balance": f"{self.current_balance:.6f} ETH",
            "params": self.params,
            "recommendation": self.get_recommendation()
        }
