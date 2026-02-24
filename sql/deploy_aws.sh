#!/bin/bash

# SQL AI RAG Chatbot - AWS Deployment Script
# Usage: ./deploy.sh

set -e

echo "Initialising AWS Deployment..."

# 1. Update System
echo "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed. You may need to logout and login again for group changes to take effect."
else
    echo "Docker already installed."
fi

# 3. Install Ollama (Linux)
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "Ollama already installed."
fi

# 4. Start Ollama Service
echo "Starting Ollama..."
sudo systemctl start ollama

# 5. Pull Models
echo "Pulling AI Models (phi3, nomic-embed-text)..."
ollama pull phi3
ollama pull nomic-embed-text

# 6. Build and Run App
echo "Building and Starting Application..."
# We assume the script is run from the project root
docker compose up -d --build

echo "Deployment Complete! Access your dashboard at http://<your-public-ip>:8501"
