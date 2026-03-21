# 🎯 Sniper Bot Dashboard

Dashboard web para monitorar seu Sniper Bot em tempo real!

## 🚀 Quick Start

### Opção 1: GitHub Pages (Grátis)

1. Ative o GitHub Pages:
   - Vá em Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (ou `gh-pages`)
   - Folder: `/dashboard`

2. Acesse: `https://seu-usuario.github.io/SniperProVip/dashboard`

### Opção 2: Servidor Local

```bash
cd dashboard
python3 api.py
```

Acesse: `http://localhost:5000`

## 📁 Arquivos

```
dashboard/
├── index.html    # Dashboard web (HTML/CSS/JS)
├── api.py       # API server para integrar com o bot
└── README.md    # Este arquivo
```

## 🔌 Integração com o Bot

Adicione ao seu `sniper_bot.py`:

```python
# No início do arquivo
try:
    from dashboard.api import update_bot_status, record_trade, update_balance
    DASHBOARD_ENABLED = True
except ImportError:
    DASHBOARD_ENABLED = False

# Na função de compra/venda, adicione:
if DASHBOARD_ENABLED:
    record_trade(token_symbol, 'BUY', amount, price, 'SUCCESS', tx_hash)
    update_balance(current_eth_balance)

# Ao iniciar/parar o bot:
if DASHBOARD_ENABLED:
    update_bot_status('RUNNING')  # ou 'STOPPED'
```

## 🎨 Features

- 📊 Estatísticas em tempo real
- 💰 Saldo ETH
- 📈 Histórico de trades
- 💎 Posições ativas
- 🛡️ Risk Manager
- ⚙️ Controles do bot
- 🎯 Indicador LIVE

## 🌐 Variáveis de Ambiente

Para a API:
- `PORT`: Porta do servidor (padrão: 5000)

## 📱 Design Responsivo

O dashboard funciona em:
- 💻 Desktop
- 📱 Mobile
- 📟 Tablet

---

Feito com ❤️ para o Sniper Bot!
