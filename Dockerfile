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

RUN cd /app/bgutil-ytdlp-pot-provider/server && \
    npm install && \
    npm run build

# ============================================================
# PORT
# ============================================================

EXPOSE 10000

# ============================================================
# START
# ============================================================

CMD ["bash", "start.sh"]