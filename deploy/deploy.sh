#!/bin/bash
set -e

cd /opt/wichat
echo "=== Pulling latest code... ==="
git pull origin main

echo "=== Installing backend dependencies... ==="
cd /opt/wichat/backend
.venv/bin/pip install -r requirements.txt --quiet

echo "=== Building frontend... ==="
cd /opt/wichat/frontend
npm install --silent
npm run build

echo "=== Restarting backend... ==="
sudo systemctl restart wichat
sleep 2
sudo systemctl status wichat --no-pager | head -6

echo "=== Deploy done ==="
