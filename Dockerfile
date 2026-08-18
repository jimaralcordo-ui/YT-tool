FROM python:3.12-slim

WORKDIR /app

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# NODE.JS 20+
# ============================================================

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN node --version && npm --version

# ============================================================
# DENO
# ============================================================

RUN curl -fsSL https://deno.land/install.sh | sh

ENV DENO_INSTALL=/root/.deno
ENV PATH="/root/.deno/bin:${PATH}"

RUN deno --version

# ============================================================
# PYTHON DEPENDENCIES
# ============================================================

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# APPLICATION
# ============================================================

COPY . .

# ============================================================
# BGUTIL POT PROVIDER
# ============================================================

WORKDIR /app/bgutil-ytdlp-pot-provider/server

RUN npm ci

# IMPORTANT:
# Compile TypeScript files into server/build/
RUN npx tsc

# Make sure compilation really created main.js
RUN test -f build/main.js

# ============================================================
# RETURN TO APP
# ============================================================

WORKDIR /app

# ============================================================
# VERIFY BGUTIL
# ============================================================

RUN test -f /app/bgutil-ytdlp-pot-provider/server/build/main.js

# ============================================================
# PORT
# ============================================================

EXPOSE 10000

# ============================================================
# START
# ============================================================

CMD ["bash", "start.sh"]