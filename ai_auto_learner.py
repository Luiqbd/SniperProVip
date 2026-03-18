#!/usr/bin/env python3
"""
IA Auto-Aprendizado - Sistema de Auto-Programação para o Sniper Bot
=========================================================================
Este módulo implementa um sistema de aprendizado que ajusta automaticamente
os parâmetros do bot baseado no desempenho histórico.

Funcionalidades:
- Ajusta valor de trade baseado em win rate
- Otimiza gas price baseado em sucesso de transações
- Ajusta score mínimo baseado em qualidade dos tokens comprados
- Modifica stop loss baseado em padrões de perda
- Aumenta agressividade quando lucrando, reduz quando perdendo
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from config import (
    # Configurações de auto-ajuste
    AI_AUTO_ADJUST,
    AI_LEARNING_RATE,
    AI_MIN_CONFIDENCE,
    AI_ADJUST_INTERVAL,
    AI_MAX_TRADE_AMOUNT,
    AI_MIN_TRADE_AMOUNT,
    AI_OPTIMIZE_GAS,
    AI_OPTIMIZE_SLIPPAGE,
    AI_OPTIMIZE_SCORE,
    AI_OPTIMIZE_STOPLOSS,
    # Configurações de trading
    TRADE_AMOUNT_WETH,
    MAX_GAS_PRICE,
    SLIPPAGE_TOLERANCE,
    MIN_SCORE_TO_BUY,
    STOP_LOSS_PERCENTAGE,
    TARGET_PROFIT_PERCENTAGE,
)


@dataclass
class TradeResult:
    """Resultado de uma trade para análise"""
    token_symbol: str
    token_address: str
    buy_price: float
    sell_price: float
    profit_loss_percent: float
    gas_spent: float
    timestamp: float
    score: int  # Score do token quando comprou
    liquidity: float  # Liquidez do par
    holders: int  # Número de holders
    success: bool  # Se a transação foi bemucedida
    failure_reason: Optional[str] = None


@dataclass
class AIData:
    """Dados persistentes para o aprendizado da IA"""
    # Histórico de trades
    trades: List[TradeResult] = field(default_factory=list)
    
    # Contadores
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    failed_trades: int = 0
    
    # Métricas
    total_profit_loss: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    
    # Parâmetros atuais (estes são ajustados)
    current_trade_amount: float = TRADE_AMOUNT_WETH
    current_gas_multiplier: float = 1.2
    current_slippage: float = SLIPPAGE_TOLERANCE
    current_min_score: int = MIN_SCORE_TO_BUY
    current_stop_loss: float = STOP_LOSS_PERCENTAGE
    current_target_profit: float = TARGET_PROFIT_PERCENTAGE
    
    # Conquistas
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Timestamps
    last_adjustment: float = 0.0
    first_trade_time: float = 0.0
    
    # Performance por horário
    hourly_performance: Dict[int, float] = field(default_factory=dict)  # hora -> profit%
    
    # Performance por DEX
    dex_performance: Dict[str, Dict] = field(default_factory=dict)  # dex -> {wins, losses, profit}


class AIAutoLearner:
    """
    Sistema de Auto-Aprendizado para o Sniper Bot
    
    Este sistema analisa o histórico de trades e ajusta automaticamente
    os parâmetros para maximizar lucros e minimizar perdas.
    """
    
    def __init__(self, data_file: str = "ai_learning_data.json"):
        self.data_file = data_file
        self.data = self._load_data()
        self.enabled = AI_AUTO_ADJUST
        
        # Configurações de ajuste
        self.learning_rate = AI_LEARNING_RATE
        self.min_confidence = AI_MIN_CONFIDENCE
        self.adjust_interval = AI_ADJUST_INTERVAL
        self.max_trade_amount = AI_MAX_TRADE_AMOUNT
        self.min_trade_amount = AI_MIN_TRADE_AMOUNT
        
        print(f"🤖 IA Auto-Aprendizado inicializada: {'ATIVADA' if self.enabled else 'DESATIVADA'}")
        if self.enabled:
            print(f"   📊 Taxa de aprendizado: {self.learning_rate}")
            print(f"   📈 Intervalo de ajuste: {self.adjust_interval} trades")
            print(f"   💰 Trade amount atual: {self.data.current_trade_amount:.6f} WETH")
    
    def _load_data(self) -> AIData:
        """Carrega dados persistentes do arquivo"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    raw_data = json.load(f)
                    
                # Converter trades
                trades = []
                for t in raw_data.get('trades', []):
                    trades.append(TradeResult(**t))
                
                return AIData(
                    trades=trades,
                    total_trades=raw_data.get('total_trades', 0),
                    winning_trades=raw_data.get('winning_trades', 0),
                    losing_trades=raw_data.get('losing_trades', 0),
                    failed_trades=raw_data.get('failed_trades', 0),
                    total_profit_loss=raw_data.get('total_profit_loss', 0.0),
                    avg_profit=raw_data.get('avg_profit', 0.0),
                    avg_loss=raw_data.get('avg_loss', 0.0),
                    current_trade_amount=raw_data.get('current_trade_amount', TRADE_AMOUNT_WETH),
                    current_gas_multiplier=raw_data.get('current_gas_multiplier', 1.2),
                    current_slippage=raw_data.get('current_slippage', SLIPPAGE_TOLERANCE),
                    current_min_score=raw_data.get('current_min_score', MIN_SCORE_TO_BUY),
                    current_stop_loss=raw_data.get('current_stop_loss', STOP_LOSS_PERCENTAGE),
                    current_target_profit=raw_data.get('current_target_profit', TARGET_PROFIT_PERCENTAGE),
                    consecutive_wins=raw_data.get('consecutive_wins', 0),
                    consecutive_losses=raw_data.get('consecutive_losses', 0),
                    max_consecutive_wins=raw_data.get('max_consecutive_wins', 0),
                    max_consecutive_losses=raw_data.get('max_consecutive_losses', 0),
                    last_adjustment=raw_data.get('last_adjustment', 0.0),
                    first_trade_time=raw_data.get('first_trade_time', 0.0),
                    hourly_performance=raw_data.get('hourly_performance', {}),
                    dex_performance=raw_data.get('dex_performance', {}),
                )
        except Exception as e:
            print(f"⚠️ Erro ao carregar dados da IA: {e}")
        
        return AIData()
    
    def _save_data(self):
        """Salva dados persistentes"""
        try:
            raw_data = {
                'trades': [
                    {
                        'token_symbol': t.token_symbol,
                        'token_address': t.token_address,
                        'buy_price': t.buy_price,
                        'sell_price': t.sell_price,
                        'profit_loss_percent': t.profit_loss_percent,
                        'gas_spent': t.gas_spent,
                        'timestamp': t.timestamp,
                        'score': t.score,
                        'liquidity': t.liquidity,
                        'holders': t.holders,
                        'success': t.success,
                        'failure_reason': t.failure_reason,
                    }
                    for t in self.data.trades
                ],
                'total_trades': self.data.total_trades,
                'winning_trades': self.data.winning_trades,
                'losing_trades': self.data.losing_trades,
                'failed_trades': self.data.failed_trades,
                'total_profit_loss': self.data.total_profit_loss,
                'avg_profit': self.data.avg_profit,
                'avg_loss': self.data.avg_loss,
                'current_trade_amount': self.data.current_trade_amount,
                'current_gas_multiplier': self.data.current_gas_multiplier,
                'current_slippage': self.data.current_slippage,
                'current_min_score': self.data.current_min_score,
                'current_stop_loss': self.data.current_stop_loss,
                'current_target_profit': self.data.current_target_profit,
                'consecutive_wins': self.data.consecutive_wins,
                'consecutive_losses': self.data.consecutive_losses,
                'max_consecutive_wins': self.data.max_consecutive_wins,
                'max_consecutive_losses': self.data.max_consecutive_losses,
                'last_adjustment': self.data.last_adjustment,
                'first_trade_time': self.data.first_trade_time,
                'hourly_performance': self.data.hourly_performance,
                'dex_performance': self.data.dex_performance,
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(raw_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar dados da IA: {e}")
    
    def add_trade_result(self, result: TradeResult):
        """Adiciona resultado de uma trade para análise"""
        if not self.enabled:
            return
        
        self.data.trades.append(result)
        self.data.total_trades += 1
        
        # Registrar timestamp inicial
        if self.data.first_trade_time == 0.0:
            self.data.first_trade_time = result.timestamp
        
        # Atualizar contadores
        if result.success:
            if result.profit_loss_percent > 0:
                self.data.winning_trades += 1
                self.data.consecutive_wins += 1
                self.data.consecutive_losses = 0
                if self.data.consecutive_wins > self.data.max_consecutive_wins:
                    self.data.max_consecutive_wins = self.data.consecutive_wins
            else:
                self.data.losing_trades += 1
                self.data.consecutive_losses += 1
                self.data.consecutive_wins = 0
                if self.data.consecutive_losses > self.data.max_consecutive_losses:
                    self.data.max_consecutive_losses = self.data.consecutive_losses
        else:
            self.data.failed_trades += 1
            self.data.consecutive_losses += 1
            self.data.consecutive_wins = 0
        
        # Atualizar profits
        self.data.total_profit_loss += result.profit_loss_percent
        
        # Atualizar médias
        if self.data.winning_trades > 0:
            self.data.avg_profit = sum(
                t.profit_loss_percent for t in self.data.trades 
                if t.success and t.profit_loss_percent > 0
            ) / self.data.winning_trades
        
        if self.data.losing_trades > 0:
            self.data.avg_loss = sum(
                t.profit_loss_percent for t in self.data.trades 
                if t.success and t.profit_loss_percent < 0
            ) / self.data.losing_trades
        
        # Registrar performance por hora
        hour = datetime.fromtimestamp(result.timestamp).hour
        if hour not in self.data.hourly_performance:
            self.data.hourly_performance[hour] = []
        self.data.hourly_performance[hour].append(result.profit_loss_percent)
        
        # Salvar e verificar se precisa ajustar
        self._save_data()
        
        # Verificar se é hora de ajustar
        if self.data.total_trades - self.data.last_adjustment >= self.adjust_interval:
            self.auto_adjust()
    
    def get_win_rate(self) -> float:
        """Calcula win rate atual"""
        if self.data.total_trades == 0:
            return 0.0
        return self.data.winning_trades / self.data.total_trades
    
    def get_recent_win_rate(self, n: int = 10) -> float:
        """Calcula win rate das últimas N trades"""
        if len(self.data.trades) == 0:
            return 0.0
        
        recent = self.data.trades[-n:]
        wins = sum(1 for t in recent if t.success and t.profit_loss_percent > 0)
        return wins / len(recent) if recent else 0.0
    
    def get_profit_factor(self) -> float:
        """Calcula profit factor (média de gain / média de loss)"""
        if self.data.avg_loss == 0:
            return 0.0
        return abs(self.data.avg_profit / self.data.avg_loss) if self.data.avg_loss != 0 else 0.0
    
    def get_best_trading_hour(self) -> Optional[int]:
        """Retorna a melhor hora para trading"""
        if not self.data.hourly_performance:
            return None
        
        best_hour = None
        best_avg = float('-inf')
        
        for hour, profits in self.data.hourly_performance.items():
            if len(profits) >= 3:  # Mínimo 3 trades
                avg = sum(profits) / len(profits)
                if avg > best_avg:
                    best_avg = avg
                    best_hour = hour
        
        return best_hour
    
    def get_current_params(self) -> Dict:
        """Retorna os parâmetros atuais ajustados"""
        return {
            'trade_amount': self.data.current_trade_amount,
            'gas_multiplier': self.data.current_gas_multiplier,
            'slippage': self.data.current_slippage,
            'min_score': self.data.current_min_score,
            'stop_loss': self.data.current_stop_loss,
            'target_profit': self.data.current_target_profit,
        }
    
    def auto_adjust(self):
        """
        Ajusta automaticamente os parâmetros baseado no desempenho
        
        Lógica:
        - Se win rate > 70%: Aumentar agressividade (mais trade, mais slippage)
        - Se win rate < 40%: Diminuir agressividade (menos trade, mais seguro)
        - Se muitas falhas: Aumentar gas e score mínimo
        - Se muito lucrando: Aumentar valor por trade
        - Se perdendo: Reduzir valor por trade e stop loss mais apertado
        """
        if not self.enabled:
            return
        
        print("\n" + "="*50)
        print("🤖 IA AUTO-AJUSTE - ANALISANDO DESEMPENHO")
        print("="*50)
        
        win_rate = self.get_win_rate()
        recent_win_rate = self.get_recent_win_rate()
        profit_factor = self.get_profit_factor()
        
        print(f"📊 Win Rate Total: {win_rate*100:.1f}%")
        print(f"📊 Win Rate Recente: {recent_win_rate*100:.1f}%")
        print(f"📊 Profit Factor: {profit_factor:.2f}")
        print(f"💰 Lucro/Perda Total: {self.data.total_profit_loss:.2f}%")
        print(f"🔥 Consecutivas: {self.data.consecutive_wins}W / {self.data.consecutive_losses}L")
        
        changes_made = []
        
        # ========== 1. AJUSTAR VALOR DE TRADE ==========
        if self.data.total_profit_loss > 10 and recent_win_rate > 0.6:
            # Lucrando bem - Aumentar valor de trade gradualmente
            increase = self.data.current_trade_amount * self.learning_rate
            new_amount = min(
                self.data.current_trade_amount + increase,
                self.max_trade_amount
            )
            if new_amount != self.data.current_trade_amount:
                self.data.current_trade_amount = new_amount
                changes_made.append(f"💰 Trade amount: {new_amount:.6f} WETH (+{increase:.6f})")
        
        elif self.data.total_profit_loss < -10 or recent_win_rate < 0.4:
            # Perdera dinheiro - Reduzir valor de trade
            decrease = self.data.current_trade_amount * self.learning_rate
            new_amount = max(
                self.data.current_trade_amount - decrease,
                self.min_trade_amount
            )
            if new_amount != self.data.current_trade_amount:
                self.data.current_trade_amount = new_amount
                changes_made.append(f"💰 Trade amount: {new_amount:.6f} WETH (-{decrease:.6f})")
        
        # ========== 2. AJUSTAR GAS ==========
        if AI_OPTIMIZE_GAS:
            failure_rate = self.data.failed_trades / max(1, self.data.total_trades)
            
            if failure_rate > 0.3:
                # Muitas falhas - Aumentar gas
                new_gas = min(self.data.current_gas_multiplier + 0.1, 2.0)
                if new_gas != self.data.current_gas_multiplier:
                    self.data.current_gas_multiplier = new_gas
                    changes_made.append(f"⛽ Gas multiplier: {new_gas:.1f}x (mais chance de sucesso)")
            
            elif failure_rate < 0.1 and self.data.current_gas_multiplier > 1.0:
                # Poucas falhas - Reduzir gas para economizar
                new_gas = max(self.data.current_gas_multiplier - 0.1, 1.0)
                if new_gas != self.data.current_gas_multiplier:
                    self.data.current_gas_multiplier = new_gas
                    changes_made.append(f"⛽ Gas multiplier: {new_gas:.1f}x (otimizando custos)")
        
        # ========== 3. AJUSTAR SLIPPAGE ==========
        if AI_OPTIMIZE_SLIPPAGE:
            if recent_win_rate > 0.7:
                # Boa taxa de sucesso - Pode aumentar slippage para mais oportunidades
                new_slippage = min(self.data.current_slippage + 2, 50)
                if new_slippage != self.data.current_slippage:
                    self.data.current_slippage = new_slippage
                    changes_made.append(f"📉 Slippage: {new_slippage}% (maior para mais oportunidades)")
            
            elif recent_win_rate < 0.4:
                # Baixa taxa de sucesso - Reduzir slippage
                new_slippage = max(self.data.current_slippage - 2, 10)
                if new_slippage != self.data.current_slippage:
                    self.data.current_slippage = new_slippage
                    changes_made.append(f"📉 Slippage: {new_slippage}% (mais seguro)")
        
        # ========== 4. AJUSTAR SCORE MÍNIMO ==========
        if AI_OPTIMIZE_SCORE:
            # Analisar trades perdidas - são de tokens com score baixo?
            recent_losing = [t for t in self.data.trades[-10:] 
                          if t.success and t.profit_loss_percent < 0]
            
            if recent_losing:
                avg_score_losing = sum(t.score for t in recent_losing) / len(recent_losing)
                
                if avg_score_losing < self.data.current_min_score + 10:
                    # Tokens comprados com score baixo dão perda
                    new_score = min(self.data.current_min_score + 5, 80)
                    if new_score != self.data.current_min_score:
                        self.data.current_min_score = new_score
                        changes_made.append(f"🎯 Score mínimo: {new_score} (mais seletivo)")
        
        # ========== 5. AJUSTAR STOP LOSS ==========
        if AI_OPTIMIZE_STOPLOSS:
            if recent_win_rate > 0.7 and self.data.consecutive_wins >= 3:
                # Em sequência de vitórias - Relaxar stop loss para capturar mais lucro
                new_stop = min(self.data.current_stop_loss + 2, 30)
                if new_stop != self.data.current_stop_loss:
                    self.data.current_stop_loss = new_stop
                    changes_made.append(f"🛑 Stop loss: {new_stop}% (relaxado para lucrar mais)")
            
            elif recent_win_rate < 0.4:
                # Em sequência de perdas - Stop loss mais apertado
                new_stop = max(self.data.current_stop_loss - 3, 10)
                if new_stop != self.data.current_stop_loss:
                    self.data.current_stop_loss = new_stop
                    changes_made.append(f"🛑 Stop loss: {new_stop}% (mais apertado para proteger)")
        
        # ========== 6. AJUSTAR TARGET PROFIT ==========
        if recent_win_rate > 0.6 and self.data.avg_profit > 10:
            # Consistentemente lucrando mais que o target - Aumentar target
            new_target = min(self.data.current_target_profit + 1, 25)
            if new_target != self.data.current_target_profit:
                self.data.current_target_profit = new_target
                changes_made.append(f"🎯 Target profit: {new_target}% (aumentado)")
        
        elif recent_win_rate < 0.4:
            # Baixa taxa de sucesso - Reduzir target para realizar lucros menores
            new_target = max(self.data.current_target_profit - 2, 5)
            if new_target != self.data.current_target_profit:
                self.data.current_target_profit = new_target
                changes_made.append(f"🎯 Target profit: {new_target}% (realizar lucros menores)")
        
        # Salvar alterações
        self.data.last_adjustment = self.data.total_trades
        self._save_data()
        
        # Resumo
        print("\n" + "-"*50)
        if changes_made:
            print("🔄 AJUSTES REALIZADOS:")
            for change in changes_made:
                print(f"   {change}")
        else:
            print("✅ Nenhum ajuste necessário - desempenho estável")
        
        print("-"*50)
        print(f"📈 Parâmetros Atuais:")
        print(f"   💰 Trade: {self.data.current_trade_amount:.6f} WETH")
        print(f"   ⛽ Gas: {self.data.current_gas_multiplier:.1f}x")
        print(f"   📉 Slippage: {self.data.current_slippage}%")
        print(f"   🎯 Score mínimo: {self.data.current_min_score}")
        print(f"   🛑 Stop loss: {self.data.current_stop_loss}%")
        print(f"   🎯 Target profit: {self.data.current_target_profit}%")
        print("="*50 + "\n")
    
    def get_status_report(self) -> str:
        """Gera relatório de status da IA"""
        win_rate = self.get_win_rate()
        
        report = f"""
🤖 IA AUTO-PROGRAMÁVEL - STATUS
================================
📊 Estatísticas:
   • Total de trades: {self.data.total_trades}
   • Vitórias: {self.data.winning_trades} ({win_rate*100:.1f}%)
   • Perdas: {self.data.losing_trades}
   • Falhas: {self.data.failed_trades}
   • Lucro/Perda total: {self.data.total_profit_loss:.2f}%

🔥 Sequências:
   • Consecutivas atuais: {self.data.consecutive_wins}W / {self.data.consecutive_losses}L
   • Máximo vitórias: {self.data.max_consecutive_wins}
   • Máximo perdas: {self.data.max_consecutive_losses}

💰 Parâmetros Atuais:
   • Trade amount: {self.data.current_trade_amount:.6f} WETH
   • Gas multiplier: {self.data.current_gas_multiplier:.1f}x
   • Slippage: {self.data.current_slippage}%
   • Score mínimo: {self.data.current_min_score}
   • Stop loss: {self.data.current_stop_loss}%
   • Target profit: {self.data.current_target_profit}%

⏰ Melhor horário: {self.get_best_trading_hour()}:00 (se disponível)
"""
        return report


# Instância global
ai_learner = AIAutoLearner()


def get_ai_learner() -> AIAutoLearner:
    """Retorna a instância global do AI Learner"""
    return ai_learner
