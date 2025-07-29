FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Make scripts executable
RUN chmod +x run.py scripts/*.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_APP=scripts/api_server.py

# Create a non-root user for security with configurable UID/GID
ARG PUID=1000
ARG PGID=1000

RUN groupadd -g $PGID audiobook && \
    useradd --create-home --shell /bin/bash --uid $PUID --gid $PGID audiobook && \
    chown -R audiobook:audiobook /app && \
    # Create directories as the audiobook user to ensure proper ownership
    su audiobook -c "mkdir -p /app/incoming /app/library /app/covers /app/logs" && \
    chmod -R 755 /app/logs && \
    chmod -R 755 /app/covers && \
    # Ensure database directory is writable
    touch /app/audiobooks.db && \
    chown audiobook:audiobook /app/audiobooks.db

# Switch to non-root user
USER audiobook

# Expose port for API server
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -sf http://localhost:5000/health || exit 1

# Default command (can be overridden)
CMD ["python", "scripts/api_server.py", "/app/incoming", "/app/library", "--host", "0.0.0.0", "--port", "5000"] 