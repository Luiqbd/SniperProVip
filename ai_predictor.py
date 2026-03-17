"""
AI Predictor - Sistema de IA Preditivo para identificar tokens POTENCIAIS DE ALTA
Focado em velocidade e lucros grandes
"""

import os
import time
import random
from typing import Dict, Optional, Tuple
from collections import deque

class AIPredictor:
    """
    IA Preditiva para identificar tokens com potencial de pump
    Focado em: VELOCIDADE + LUCROS GRANDES
    """
    
    def __init__(self):
        self.token_history = deque(maxlen=50)
        self.dex_performance = {
            'Uniswap V3': 0,
            'Aerodrome': 0,
            'BaseSwap': 0,
            'SushiSwap': 0
        }
        
        # Configurações agressivas para lucros grandes
        self.aggressive_mode = True
        self.min_profit_target = 0.10  # 10% mínimo (antes era 3%)
        self.max_hold_time = 180  # 3 minutos máximo
        self.quick_profit_threshold = 0.05  # 5% quick exit
        
        # Parâmetros de scoring
        self.token_scores = {}
        
    def analyze_token(self, token_info: Dict, liquidity_info: Dict = None) -> Dict:
        """
        Analisa token e retorna score de potencial de pump
        Retorna: {
            'score': 0-100,
            'prediction': 'HIGH'|'MEDIUM'|'LOW',
            'reason': str,
            'should_buy': bool
        }
        """
        symbol = token_info.get('symbol', 'UNKNOWN')
        address = token_info.get('address', '')
        
        # Score base inicial
        score = 50
        reasons = []
        
        # 1. Verificar se é token recente (alta volatilidade = potencial de pump)
        token_age_minutes = token_info.get('age_minutes', 0)
        if token_age_minutes < 5:
            score += 25
            reasons.append("Token muito novo (potencial de pump)")
        elif token_age_minutes < 30:
            score += 15
            reasons.append("Token recente")
            
        # 2. Verificar liquidez (liquidez muito baixa = risco mas também potencial)
        if liquidity_info:
            total_liquidity = sum(liquidity_info.values()) if isinstance(liquidity_info, dict) else 0
            
            # Liquidez média = bom equilíbrio
            if 0.1 <= total_liquidity <= 1.0:  # 0.1 a 1 ETH
                score += 20
                reasons.append("Liquidez moderada (bom para pump)")
            elif total_liquidity < 0.1:
                score += 15
                reasons.append("Liquidez muito baixa (alto risco mas alto retorno)")
            elif total_liquidity > 5.0:
                score += 10
                reasons.append("Alta liquidez (mais seguro)")
        
        # 3. Verificar nome do token (tokens com nomes "picantes" tendem a pump)
        pump_indicators = ['ai', 'cat', 'dog', 'pepe', 'frog', 'inu', 'moon', 'rocket', 'gas', 
                          'hack', 'elon', 'mars', 'safe', 'gold', 'bit', 'satoshi', '中', '🐕', '🚀']
        if any(ind in symbol.lower() for ind in pump_indicators):
            score += 15
            reasons.append("Nome com potencial de pump")
        
        # 4. Verificar holders (muitos holders = mais distribuição)
        holders = token_info.get('holders', 0)
        if holders and holders > 50:
            score += 10
            reasons.append(f"{holders} holders (boa distribuição)")
        
        # 5. Verificar se já pumpou antes (histórico)
        if address in self.token_history:
            prev_performance = self.token_scores.get(address, {}).get('performance', 0)
            if prev_performance > 0:
                score += 10
                reasons.append(f"Histórico positivo ({prev_performance:.0%})")
        
        # 6. Verificar DEX com melhor performance
        best_dex = self.get_best_dex()
        if best_dex:
            score += 5
            reasons.append(f"Melhor DEX: {best_dex}")
        
        # Normalizar score
        score = min(score, 100)
        
        # Decisão de compra
        should_buy = score >= 60  # Limiar mais baixo para mais oportunidades
        
        # Previsão
        if score >= 80:
            prediction = "HIGH"
            target_profit = 0.20  # 20% para tokens com alto potencial
        elif score >= 60:
            prediction = "MEDIUM"
            target_profit = 0.10  # 10%
        else:
            prediction = "LOW"
            target_profit = 0.05  # 5% só paraogar
        
        result = {
            'score': score,
            'prediction': prediction,
            'reason': ', '.join(reasons[:3]),  # Máximo 3 razões
            'should_buy': should_buy,
            'target_profit': target_profit,
            'stop_loss': 0.15 if prediction == "HIGH" else 0.20,  # Stop mais apertado para high
            'best_dex': best_dex,
            'hold_time': 30 if prediction == "HIGH" else 60  # Menos tempo para high
        }
        
        self.token_scores[address] = result
        return result
    
    def get_best_dex(self) -> str:
        """Retorna a DEX com melhor performance recente"""
        best_dex = max(self.dex_performance, key=self.dex_performance.get)
        return best_dex if self.dex_performance[best_dex] > 0 else 'BaseSwap'
    
    def record_trade_result(self, dex: str, profit_pct: float, sold: bool):
        """Registra resultado do trade para aprender"""
        if dex in self.dex_performance:
            # Se lucrou, DEX ganha pontos. Se perdeu, perde pontos
            if sold and profit_pct > 0:
                self.dex_performance[dex] += 1
            elif sold and profit_pct < 0:
                self.dex_performance[dex] -= 1
    
    def should_sell(self, current_profit_pct: float, hold_seconds: int, token_info: Dict) -> Tuple[bool, str]:
        """
        Decide se deve vender - FOCADO EM LUCROS GRANDES
        """
        symbol = token_info.get('symbol', 'TOKEN')
        
        # 1. Lucro alvo atingido - VENDER!
        if current_profit_pct >= self.min_profit_target:
            return True, f"🎯 LUCRO ALVO: {current_profit_pct*100:.0f}%"
        
        # 2. Quick profit - Se já tem 5% em menos de 30s, vender rápido
        if current_profit_pct >= self.quick_profit_threshold and hold_seconds < 30:
            return True, f"⚡ SAÍDA RÁPIDA: {current_profit_pct*100:.0f}% em {hold_seconds}s"
        
        # 3. Stop loss - Se caiu muito, vender para limitar perda
        if current_profit_pct <= -0.20:  # 20% stop loss
            return True, f"🛑 STOP LOSS: {current_profit_pct*100:.0f}%"
        
        # 4. Tempo máximo - Se passou de 3 min, vender
        if hold_seconds >= self.max_hold_time:
            return True, f"⏰ TEMPO MÁXIMO: {hold_seconds}s"
        
        # 5. Se pumpou muito rápido (mais de 50% em pouco tempo), realizar lucro parcial
        if current_profit_pct >= 0.30 and hold_seconds < 60:
            return True, f"💰 PUMP DETECTADO: {current_profit_pct*100:.0f}% - REALIZAR LUCRO!"
        
        return False, ""
    
    def get_aggressive_settings(self) -> Dict:
        """Retorna configurações agressivas para lucros grandes"""
        return {
            'min_profit_target': self.min_profit_target,
            'max_hold_time': self.max_hold_time,
            'quick_profit_threshold': self.quick_profit_threshold,
            'aggressive_mode': self.aggressive_mode
        }
    
    def optimize_for_bigger_profits(self):
        """Aumenta agressividade para buscar lucros maiores"""
        self.min_profit_target = min(self.min_profit_target + 0.02, 0.50)  # Max 50%
        self.max_hold_time = min(self.max_hold_time + 30, 300)  # Max 5 min
        print(f"🤖 IA: Ajustado para lucros maiores - Alvo: {self.min_profit_target*100:.0f}%")
    
    def optimize_for_safety(self):
        """Reduce risco se estiver perdendo muito"""
        self.min_profit_target = max(self.min_profit_target - 0.02, 0.05)  # Min 5%
        self.max_hold_time = max(self.max_hold_time - 30, 60)  # Min 1 min
        print(f"🤖 IA: Modo conservador - Alvo: {self.min_profit_target*100:.0f}%")
