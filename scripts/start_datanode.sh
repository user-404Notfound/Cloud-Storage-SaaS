#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$DIR/.." && pwd)"

export HADOOP_CONF_DIR="$PROJECT_DIR/hadoop_conf"

echo "=========================================================="
echo " Starting Hadoop DataNode Worker on LAN Machine "
echo "=========================================================="

mkdir -p /tmp/hadoop-sanmesh/logs /tmp/hadoop-sanmesh/pids /tmp/hadoop-sanmesh/data/datanode

echo "Starting DataNode daemon..."
hdfs --daemon start datanode
sleep 2

echo "Active Java processes:"
jps

echo -e "\nDataNode worker started. It will report blocks to the Master NameNode."
echo "Check /tmp/hadoop-sanmesh/logs/ for worker logs."

