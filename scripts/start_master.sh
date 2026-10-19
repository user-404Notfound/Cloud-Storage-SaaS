#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$DIR/.." && pwd)"

echo "=========================================================="
echo " Starting LAN Cloud Storage SaaS - Master Controller Node "
echo "=========================================================="

# 1. Start Hadoop HDFS Services
echo -e "\n[1/3] Starting HDFS Services..."
"$PROJECT_DIR/scripts/start_hdfs.sh"

# 2. Start Flask Backend
echo -e "\n[2/3] Starting Flask Cloud Controller on port 5000..."
source "$PROJECT_DIR/.venv/bin/activate"

# Export FLASK_HOST=0.0.0.0 so it binds to LAN IP
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"

python3 "$PROJECT_DIR/backend/run.py" &
BACKEND_PID=$!
echo "Backend running with PID $BACKEND_PID"

# 3. Start React Frontend
echo -e "\n[3/3] Starting React Web Interface on port 5173..."
cd "$PROJECT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo -e "\n=========================================================="
echo " Cloud Storage SaaS is active!"
echo " Web UI:      http://localhost:5173"
echo " Backend API: http://localhost:5000/api/health"
echo " WebHDFS:     http://localhost:9870/webhdfs/v1"
echo "=========================================================="
echo "Press Ctrl+C to stop all services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" INT TERM EXIT
wait

