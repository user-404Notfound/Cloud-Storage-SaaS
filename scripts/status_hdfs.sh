#!/bin/bash
echo "=== Active Java Processes (jps) ==="
jps

echo -e "\n=== Checking WebHDFS HTTP API (port 9870) ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:9870/webhdfs/v1/?op=LISTSTATUS" 2>/dev/null || echo "DOWN")

if [ "$STATUS" == "200" ]; then
    echo "[ONLINE] WebHDFS is accessible (HTTP $STATUS)"
else
    echo "[OFFLINE] WebHDFS is unreachable (Status: $STATUS)"
fi

