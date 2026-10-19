#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$DIR/.." && pwd)"

export HADOOP_CONF_DIR="$PROJECT_DIR/hadoop_conf"

echo "Using HADOOP_CONF_DIR=$HADOOP_CONF_DIR"

# Stop existing if any
hdfs --daemon stop datanode 2>/dev/null || true
hdfs --daemon stop namenode 2>/dev/null || true

# Format if needed
if [ ! -d "/tmp/hadoop-sanmesh/data/namenode/current" ]; then
    echo "Formatting NameNode..."
    hdfs namenode -format -force -nonInteractive
fi

echo "Starting NameNode..."
hdfs --daemon start namenode
sleep 3

echo "Starting DataNode..."
hdfs --daemon start datanode
sleep 3

echo "=== JPS processes ==="
jps

echo "HDFS cluster started successfully."

# Keep alive to preserve daemon processes
while true; do
    sleep 10
done

