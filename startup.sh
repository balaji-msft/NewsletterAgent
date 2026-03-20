#!/bin/bash
set -e
cd /home/site/wwwroot

# Install packages once (cached in /home, persists across restarts)
if [ ! -f "antenv/done.marker" ]; then
    echo "=== First run: installing dependencies ==="
    python -m venv antenv
    source antenv/bin/activate
    pip install -r requirements.txt --quiet
    touch antenv/done.marker
    echo "=== Install complete ==="
else
    source antenv/bin/activate
fi

echo "=== Starting Streamlit ==="
python -m streamlit run ui/app.py \
    --server.port 8000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
