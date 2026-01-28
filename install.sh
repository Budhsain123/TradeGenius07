#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "[*] Setting up Termux storage..."
termux-setup-storage

echo "[*] Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "[*] Installing system dependencies..."
pkg install -y \
python \
python-pip \
clang \
openssl \
libffi

echo "[*] Installing Python packages..."
pip install \
requests \
psutil \
PyJWT \
urllib3 \
pytz \
aiohttp \
cfonts \
protobuf \
protobuf-decoder \
google \
pycryptodome \
httpx \
flask \
colorama \
google-play-scraper

echo "[✓] Installation completed successfully (Termux-safe)!"