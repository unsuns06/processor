# Optimized Dockerfile for N_m3u8DL-RE with FastAPI file server.
FROM mcr.microsoft.com/dotnet/runtime:8.0-bookworm-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# Create user as required by Hugging Face Spaces  
RUN useradd -m -u 1000 user

# Install system dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    ca-certificates \
    ffmpeg \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Download and install Bento4 tools (mp4decrypt, mp4info)
RUN cd /tmp \
    && wget -q "https://www.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip" \
    && unzip -j "Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip" \
       'Bento4-SDK-1-6-0-641.x86_64-unknown-linux/bin/mp4decrypt' \
       'Bento4-SDK-1-6-0-641.x86_64-unknown-linux/bin/mp4info' \
       -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/mp4decrypt /usr/local/bin/mp4info \
    && rm -f "Bento4-SDK-1-6-0-641.x86_64-unknown-linux.zip" \
    && cd /

# Download and install N_m3u8DL-RE
RUN cd /tmp \
    && wget -q "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.3.0-beta/N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz" \
    && tar -xzf "N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz" \
    && mv N_m3u8DL-RE /usr/local/bin/N_m3u8DL-RE \
    && chmod +x /usr/local/bin/N_m3u8DL-RE \
    && rm -f "N_m3u8DL-RE_v0.3.0-beta_linux-x64_20241203.tar.gz" \
    && cd /

# Pre-create writable Logs directory for N_m3u8DL-RE
RUN mkdir -p /usr/local/bin/Logs && chown -R user:user /usr/local/bin/Logs

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies with --break-system-packages
# This is safe in Docker containers where we control the entire environment
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Create directory structure for organized downloads
RUN mkdir -p stream \
    && chown -R user:user /app

# Copy authentication files (required for Google Drive integration)
# These files must be committed to git and will be copied into the container
COPY --chown=user credentials.json .
COPY --chown=user settings.yaml .
COPY --chown=user client_secrets.json .

# Copy application files
COPY --chown=user app.py .

# Switch to non-root user
USER user

# Set user environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose port for FastAPI server
EXPOSE 7860

# Start FastAPI server.
CMD ["python3", "/app/app.py"]
