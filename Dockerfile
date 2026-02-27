# Sniper Bot V5 - Base Network Edition
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do bot
COPY . .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Definir variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Expor porta (se necessário para monitoramento)
EXPOSE 8000

# Comando padrão
CMD ["python", "main.py"]