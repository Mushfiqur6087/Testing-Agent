# ── Stage 1: Install Python dependencies ──────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools
RUN pip install --upgrade pip

# Copy dependency files first for layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies into a prefix we can copy later
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Install Playwright + let it install ALL system dependencies it needs for
# Chromium automatically — this is the official recommended approach and
# avoids manually hunting down missing .so files like libxkbcommon.so.0
RUN pip install --no-cache-dir playwright && \
    playwright install-deps chromium && \
    playwright install chromium

# Copy project source
COPY src/       ./src/
COPY html/      ./html/
COPY pyproject.toml ./

# Mount points — these are overridden at runtime via docker-compose volumes
# test_cases/ : where the agent reads test_cases.json from
# logs/        : where results are written to
RUN mkdir -p test_cases logs

# Default model/provider — override via docker-compose environment or CLI
ENV MODEL="gemini-2.0-flash"
ENV PROVIDER="gemini"

# Default command: run the agent with the configured model/provider
CMD python -m src.test_agent_main --model "$MODEL" --provider "$PROVIDER"
