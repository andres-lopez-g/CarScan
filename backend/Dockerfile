FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

# Build the Rust vendetunave scraper binary and install it onto PATH
COPY rust-scraper /rust-scraper
RUN cargo build --release --manifest-path /rust-scraper/Cargo.toml \
    && cp /rust-scraper/target/release/vendetunave-scraper /usr/local/bin/vendetunave-scraper \
    && rm -rf /rust-scraper/target

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium (deps already included in base image)
RUN playwright install chromium

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
