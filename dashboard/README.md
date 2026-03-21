# 🎯 Sniper Bot Pro - Dashboard

Dashboard web avançado para monitorar seu Sniper Bot em tempo real!

## 🚀 Quick Start

### Opção 1: GitHub Pages (Grátis)

1. Ative o GitHub Pages:
   - Vá em **Settings → Pages**
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/dashboard`

2. Acesse: `https://seu-usuario.github.io/SniperProVip/dashboard/`

### Opção 2: Render/VPS

```bash
cd dashboard
pip install flask
python3 api.py
```

Acesse: `http://localhost:5000`

## 🔌 Conectando ao Bot no Render

### Passo 1: Configure a API URL

Abra o arquivo `dashboard/index.html` e altere a linha:

```javascript
// NO TOPO DO ARQUIVO:
const API_URL = 'https://seu-sniper-bot.onrender.com';
```

Substitua `https://seu-sniper-bot.onrender.com` pela URL real do seu bot no Render!

### Passo 2: O Bot precisa rodar a API

O servidor API já está integrado! Quando o bot inicia, a API também starta automaticamente na porta 5000.

### Passo 3: Deploy

1. Faça deploy normal no Render
2. O Render expõe automaticamente a porta 5000
3. Atualize o `API_URL` no dashboard com a URL do Render

### Exemplo de URL:
```
https://sniper-pro-vip.onrender.com
```

## 📁 Arquivos

```
dashboard/
├── index.html    # Dashboard web completo
├── api.py       # API server para integrar com o bot
└── README.md    # Este arquivo
```

## 🎨 Features Avançadas

### 📊 Monitoramento em Tempo Real
- 💰 Saldo ETH
- 📈 Histórico de trades
- 💎 Posições ativas
- 🎯 Win Rate
- 📈 Lucro diário

### 🛡️ Gerenciador de Risco
- Limite diário de perda
- Perdas consecutivas
- Circuit Breaker
- Saúde do portfólio

### ⚙️ Controles
- Iniciar/Parar bot
- Resetar posições
- Forçar compra
- Modos de risco rápido

### 📋 Logs em Tempo Real
- Todos os logs do bot
- Cores por nível (INFO, WARNING, ERROR)
- Auto-scroll
- Limpar logs

## 🔌 Integração com o Bot

Adicione ao seu `sniper_bot.py`:

```python
# No início do arquivo
try:
    from dashboard.api import (
        update_bot_status, 
        record_trade, 
        update_balance,
        log_info,
        log_error,
        update_risk
    )
    DASHBOARD_ENABLED = True
except ImportError:
    DASHBOARD_ENABLED = False
    # Funções vazias se não disponível
    def update_bot_status(s): pass
    def record_trade(*args): pass
    def update_balance(b): pass
    def log_info(m): print(m)
    def log_error(m): print(f"ERROR: {m}")
    def update_risk(*args): pass

# Ao iniciar o bot:
if DASHBOARD_ENABLED:
    update_bot_status('RUNNING')
    log_info('🎯 Bot iniciado!')

# Após cada trade:
if DASHBOARD_ENABLED:
    record_trade(token_symbol, 'BUY', amount, price, 'SUCCESS', tx_hash)
    update_balance(current_eth_balance)

# Em caso de erro:
if DASHBOARD_ENABLED:
    log_error(f'Transação falhou: {error}')

# Ao parar o bot:
if DASHBOARD_ENABLED:
    update_bot_status('STOPPED')
```

## 📱 Design Responsivo

O dashboard funciona em:
- 💻 Desktop
- 📱 Mobile
- 📟 Tablet

## 🌐 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/status` | GET | Status completo do bot |
| `/api/trades` | GET | Lista de trades |
| `/api/positions` | GET | Posições ativas |
| `/api/stats` | GET | Estatísticas |
| `/api/logs` | GET | Logs em tempo real |
| `/api/logs` | POST | Adicionar log |

## 📦 Instalação

```bash
# Instalar dependências
pip install flask

# Rodar servidor
python3 api.py

# Acessar
# http://localhost:5000
```

---

Feito com ❤️ para o Sniper Bot Pro!
