"""
Risk Manager - Sistema Avançado de Gerenciamento de Risco
Protege o capital com limites diários, drawdown e circuit breaker
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import deque
from config import *

class RiskManager:
    """
    Sistema completo de gerenciamento de risco para proteção do capital
    """
    
    def __init__(self, initial_balance: float = None):
        # Saldo inicial (usar config se não especificado)
        self.initial_balance = initial_balance or INITIAL_ETH_BALANCE
        self.current_balance = self.initial_balance
        
        # Histórico de operações
        self.trade_history = deque(maxlen=100)
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Limites de risco
        self.daily_loss_limit = float(os.getenv('DAILY_LOSS_LIMIT', '0.002'))  # Max 0.002 ETH perda/dia
        self.daily_profit_target = float(os.getenv('DAILY_PROFIT_TARGET', '0.01'))  # Meta diária 0.01 ETH
        self.max_drawdown_pct = float(os.getenv('MAX_DRAWDOWN_PCT', '30'))  # 30% drawdown máx
        self.max_position_size_pct = float(os.getenv('MAX_POSITION_SIZE_PCT', '50'))  # 50% máx por trade
        
        # Circuit breaker
        self.consecutive_losses = 0
        self.max_consecutive_losses = int(os.getenv('MAX_CONSECUTIVE_LOSSES', '3'))  # Para após 3 perdas
        self.circuit_breaker_triggered = False
        self.circuit_breaker_until = None
        
        # Proteção de emergência
        self.emergency_stop = False
        self.pause_until = None
        
        # Estatísticas
        self.total_wins = 0
        self.total_losses = 0
        self.best_trade = 0.0
        self.worst_trade = 0.0
        
        print(f"🛡️ Risk Manager inicializado")
        print(f"   Limite diário de perda: {self.daily_loss_limit:.6f} ETH")
        print(f"   Meta diária de lucro: {self.daily_profit_target:.6f} ETH")
        print(f"   Posição máx: {self.max_position_size_pct}%")
    
    def check_daily_reset(self):
        """Reseta contadores diários se mudou o dia"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset_date = today
            print(f"📅 Novo dia - contadores resetados")
    
    def can_trade(self, trade_amount: float = None) -> tuple[bool, str]:
        """
        Verifica se pode operar baseando-se em múltiplos fatores de risco
        Returns: (can_trade: bool, reason: str)
        """
        self.check_daily_reset()
        
        # 1. Verificar circuit breaker
        if self.circuit_breaker_triggered:
            if self.circuit_breaker_until and datetime.now() < self.circuit_breaker_until:
                remaining = (self.circuit_breaker_until - datetime.now()).seconds
                return False, f"Circuit breaker ativo ({remaining}s restante)"
            else:
                self.circuit_breaker_triggered = False
                self.circuit_breaker_until = None
                print(f"✅ Circuit breaker resetado")
        
        # 2. Verificar emergência
        if self.emergency_stop:
            if self.pause_until and datetime.now() < self.pause_until:
                remaining = (self.pause_until - datetime.now()).seconds
                return False, f"Emergencial ativo ({remaining}s restante)"
            else:
                self.emergency_stop = False
                self.pause_until = None
        
        # 3. Verificar limite diário de perda
        if self.daily_pnl <= -self.daily_loss_limit:
            self.trigger_circuit_breaker("Limite diário de perda atingido")
            return False, "Limite diário de perda atingido"
        
        # 4. Verificar meta diária de lucro (opcional - só alerta)
        if self.daily_pnl >= self.daily_profit_target:
            print(f"🎯 Meta diária de lucro atingida! {self.daily_pnl:.6f} ETH")
        
        # 5. Verificar consecutivos losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.trigger_circuit_breaker(f"Many losses ({self.consecutive_losses})")
            return False, f"Muitas perdas consecutivas ({self.consecutive_losses})"
        
        # 6. Verificar tamanho da posição
        if trade_amount:
            max_trade = self.current_balance * (self.max_position_size_pct / 100)
            if trade_amount > max_trade:
                return False, f"Posição muito grande (máx: {max_trade:.6f} ETH)"
        
        return True, "OK"
    
    def trigger_circuit_breaker(self, reason: str):
        """Ativa circuit breaker"""
        self.circuit_breaker_triggered = True
        # Tempo de pausa baseado na causa
        pause_seconds = 300  # 5 minutos padrão
        self.circuit_breaker_until = datetime.now() + timedelta(seconds=pause_seconds)
        print(f"🛑 CIRCUIT BREAKER ATIVADO: {reason}")
        print(f"   Pausando por {pause_seconds} segundos")
    
    def trigger_emergency_stop(self, reason: str, pause_minutes: int = 15):
        """Para todas as operações emergencialmente"""
        self.emergency_stop = True
        self.pause_until = datetime.now() + timedelta(minutes=pause_minutes)
        print(f"🚨 EMERGENCY STOP: {reason}")
        print(f"   Pausando por {pause_minutes} minutos")
    
    def record_trade(self, amount: float, pnl: float, is_win: bool, token_symbol: str = "TOKEN"):
        """Registra uma operação para análise de risco"""
        trade_record = {
            'timestamp': time.time(),
            'amount': amount,
            'pnl': pnl,
            'is_win': is_win,
            'symbol': token_symbol,
            'balance_after': self.current_balance + pnl
        }
        
        self.trade_history.append(trade_record)
        self.daily_pnl += pnl
        self.daily_trades += 1
        
        # Atualizar estatísticas
        if is_win:
            self.total_wins += 1
            self.consecutive_losses = 0
            if pnl > self.best_trade:
                self.best_trade = pnl
        else:
            self.total_losses += 1
            self.consecutive_losses += 1
            if pnl < self.worst_trade:
                self.worst_trade = pnl
        
        # Atualizar saldo atual
        self.current_balance += pnl
        
        # Verificar drawdown
        if self.current_balance < self.initial_balance * (1 - self.max_drawdown_pct/100):
            self.trigger_emergency_stop(f"Drawdown {self.max_drawdown_pct}% atingido")
        
        print(f"📊 Trade registrado: {'✅ WIN' if is_win else '❌ LOSS'} | PnL: {pnl:.8f} ETH | Total hoje: {self.daily_pnl:.6f} ETH")
    
    def get_optimal_position_size(self, confidence: float = 0.5, balance: float = None) -> float:
        """
        Calcula tamanho ideal da posição baseado na confiança e saldo
        confidence: 0.0 - 1.0 (quão confiante está na operação)
        """
        balance = balance or self.current_balance
        
        # Kelly Criterion simplificado
        # Se confiança alta e taxa de acerto boa, aumenta posição
        win_rate = self.total_wins / max(1, self.total_wins + self.total_losses)
        
        # Base size: 10% do saldo
        base_size = balance * 0.10
        
        # Ajuste por confiança (0.5 = 100%, 1.0 = 200%)
        confidence_multiplier = 0.5 + (confidence * 1.5)
        
        # Ajuste por win rate
        win_rate_multiplier = 0.5 + (win_rate * 1.0)
        
        # Calcular tamanho final
        optimal_size = base_size * confidence_multiplier * win_rate_multiplier
        
        # Limitar ao máximo permitido
        max_size = balance * (self.max_position_size_pct / 100)
        optimal_size = min(optimal_size, max_size)
        
        # Mínimo razoável
        min_size = 0.0001  # 0.0001 ETH
        optimal_size = max(optimal_size, min_size)
        
        return optimal_size
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas de risco"""
        total_trades = self.total_wins + self.total_losses
        win_rate = (self.total_wins / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'wins': self.total_wins,
            'losses': self.total_losses,
            'win_rate': f"{win_rate:.1f}%",
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'current_balance': self.current_balance,
            'initial_balance': self.initial_balance,
            'best_trade': self.best_trade,
            'worst_trade': self.worst_trade,
            'consecutive_losses': self.consecutive_losses,
            'circuit_breaker': self.circuit_breaker_triggered,
            'emergency_stop': self.emergency_stop
        }
    
    def print_stats(self):
        """Imprime estatísticas atuais"""
        stats = self.get_stats()
        print(f"\n{'='*50}")
        print(f"🛡️ ESTATÍSTICAS DE RISCO")
        print(f"{'='*50}")
        print(f"Total de trades: {stats['total_trades']}")
        print(f"Wins: {stats['wins']} | Losses: {stats['losses']}")
        print(f"Win Rate: {stats['win_rate']}")
        print(f"Saldo Inicial: {stats['initial_balance']:.6f} ETH")
        print(f"Saldo Atual: {stats['current_balance']:.6f} ETH")
        print(f"P&L Diário: {stats['daily_pnl']:.6f} ETH")
        print(f"Melhor Trade: {stats['best_trade']:.6f} ETH")
        print(f"Pior Trade: {stats['worst_trade']:.6f} ETH")
        print(f"Perdas Consecutivas: {stats['consecutive_losses']}")
        print(f"Circuit Breaker: {'ATIVO' if stats['circuit_breaker'] else 'Inativo'}")
        print(f"Emergency Stop: {'ATIVO' if stats['emergency_stop'] else 'Inativo'}")
        print(f"{'='*50}\n")
    
    def calculate_dynamic_risk(self, token_score: int, liquidity_eth: float) -> float:
        """
        Calcula risco dinâmico baseado em múltiplos fatores
        Retorna: 0.0 (muito arriscado) a 1.0 (seguro)
        """
        risk_score = 0.5  # Base
        
        # Score do token (maior = menos arriscado)
        if token_score >= 80:
            risk_score += 0.3
        elif token_score >= 60:
            risk_score += 0.2
        elif token_score >= 40:
            risk_score += 0.1
        else:
            risk_score -= 0.2
        
        # Liquidez (maior = menos arriscado)
        if liquidity_eth >= 1.0:
            risk_score += 0.2
        elif liquidity_eth >= 0.5:
            risk_score += 0.1
        elif liquidity_eth < 0.1:
            risk_score -= 0.3
        
        # Histórico de losses (muitos = mais arriscado)
        if self.consecutive_losses >= 3:
            risk_score -= 0.3
        elif self.consecutive_losses >= 2:
            risk_score -= 0.2
        elif self.consecutive_losses == 0:
            risk_score += 0.1
        
        # Drawdown atual
        drawdown = (self.initial_balance - self.current_balance) / self.initial_balance
        if drawdown >= 0.2:
            risk_score -= 0.3
        elif drawdown >= 0.1:
            risk_score -= 0.1
        
        # Limitar entre 0 e 1
        return max(0.0, min(1.0, risk_score))
    
    def reset_daily(self):
        """Reseta contadores diários manualmente"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.consecutive_losses = 0
        print("📅 Contadores diários resetados")
    
    def force_circuit_break(self):
        """Força circuit breaker manualmente"""
        self.trigger_circuit_breaker("Manual trigger")


# Função para integrar com config
def get_risk_manager() -> RiskManager:
    """Factory function para criar risk manager"""
    return RiskManager(INITIAL_ETH_BALANCE)
