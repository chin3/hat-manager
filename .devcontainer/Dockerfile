# Use official Python 3.11 image
FROM python:3.11-slim

# Install build tools and SQLite
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up user to match Codespaces
RUN useradd -m vscode
USER vscode
WORKDIR /workspaces/hat-manager

# Ensure ~/.local/bin is in PATH
ENV PATH="/home/vscode/.local/bin:$PATH"
