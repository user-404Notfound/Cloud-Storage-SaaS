#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$DIR/.." && pwd)"

export HADOOP_CONF_DIR="$PROJECT_DIR/hadoop_conf"

echo "Checking HDFS status..."
if curl -s -m 2 "http://127.0.0.1:9870/webhdfs/v1/?op=LISTSTATUS" > /dev/null 2>&1; then
    echo "[OK] HDFS is already running and WebHDFS is accessible at http://127.0.0.1:9870"
    exit 0
fi

# Ensure data directories exist
mkdir -p /tmp/hadoop-sanmesh/logs /tmp/hadoop-sanmesh/pids /tmp/hadoop-sanmesh/data/namenode /tmp/hadoop-sanmesh/data/datanode

# Format if needed
if [ ! -d "/tmp/hadoop-sanmesh/data/namenode/current" ]; then
    echo "Formatting NameNode..."
    hdfs namenode -format -force -nonInteractive
fi

echo "Starting NameNode..."
hdfs --daemon start namenode
sleep 2

echo "Starting DataNode..."
hdfs --daemon start datanode
sleep 2

echo "Verifying services..."
jps

echo "Waiting for WebHDFS to respond..."
for i in {1..10}; do
    if curl -s -m 2 "http://127.0.0.1:9870/webhdfs/v1/?op=LISTSTATUS" > /dev/null 2>&1; then
        echo "[SUCCESS] HDFS is up and running! WebHDFS: http://127.0.0.1:9870/webhdfs/v1"
        exit 0
    fi
    sleep 1
done

echo "[WARNING] WebHDFS is taking longer than expected to respond. Check logs in /tmp/hadoop-sanmesh/logs/"

