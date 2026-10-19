#!/bin/bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$DIR/.." && pwd)"

export HADOOP_CONF_DIR="$PROJECT_DIR/hadoop_conf"

echo "Stopping DataNode..."
hdfs --daemon stop datanode 2>/dev/null || true

echo "Stopping NameNode..."
hdfs --daemon stop namenode 2>/dev/null || true

sleep 2
echo "HDFS services stopped."
jps

