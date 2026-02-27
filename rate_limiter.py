#!/usr/bin/env python3
"""
Rate Limiter inteligente para evitar 429 errors
"""

import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    max_requests: int
    time_window: int  # segundos
    backoff_multiplier: float = 2.0
    max_backoff: int = 60

class SmartRateLimiter:
    """Rate limiter inteligente com backoff exponencial"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: List[float] = []
        self.current_backoff = 0
        self.last_429_time = 0
        self.consecutive_429s = 0
        
    async def acquire(self):
        """Adquire permissão para fazer uma requisição"""
        now = time.time()
        
        # Limpar requisições antigas
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.config.time_window]
        
        # Verificar se precisa de backoff após 429
        if self.current_backoff > 0:
            if now - self.last_429_time < self.current_backoff:
                wait_time = self.current_backoff - (now - self.last_429_time)
                print(f"⏳ Rate limit backoff: aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            else:
                # Reduzir backoff gradualmente
                self.current_backoff = max(0, self.current_backoff * 0.5)
        
        # Verificar limite de requisições
        if len(self.requests) >= self.config.max_requests:
            oldest_request = min(self.requests)
            wait_time = self.config.time_window - (now - oldest_request)
            if wait_time > 0:
                print(f"⏳ Rate limit: aguardando {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Registrar nova requisição
        self.requests.append(time.time())
    
    def handle_429_error(self):
        """Lidar com erro 429"""
        now = time.time()
        self.last_429_time = now
        self.consecutive_429s += 1
        
        # Backoff exponencial
        base_backoff = min(5 * (self.config.backoff_multiplier ** self.consecutive_429s), 
                          self.config.max_backoff)
        self.current_backoff = base_backoff
        
        print(f"🚫 Rate limit 429 detectado. Backoff: {self.current_backoff}s")
    
    def handle_success(self):
        """Lidar com requisição bem-sucedida"""
        if self.consecutive_429s > 0:
            self.consecutive_429s = max(0, self.consecutive_429s - 1)
            if self.consecutive_429s == 0:
                self.current_backoff = 0
                print("✅ Rate limit recuperado")

# Configurações OTIMIZADAS para Base Network (evitar 429 errors)
BASE_RPC_LIMITER = SmartRateLimiter(RateLimitConfig(
    max_requests=15,  # 15 requisições por janela (evitar rate limit)
    time_window=60,   # 60 segundos
    backoff_multiplier=1.5,  # Backoff moderado
    max_backoff=10    # Backoff máximo 10 segundos
))

TELEGRAM_LIMITER = SmartRateLimiter(RateLimitConfig(
    max_requests=20,  # 20 mensagens por minuto
    time_window=60,
    backoff_multiplier=2.0,
    max_backoff=60
))

async def with_rate_limit(limiter: SmartRateLimiter, func, *args, **kwargs):
    """Executa função com rate limiting"""
    await limiter.acquire()
    
    try:
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        limiter.handle_success()
        return result
    except Exception as e:
        if "429" in str(e) or "Too Many Requests" in str(e):
            limiter.handle_429_error()
        raise e