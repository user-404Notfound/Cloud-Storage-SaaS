# College Laboratory LAN Deployment Guide

This guide describes how to deploy the **Shared Cloud Storage SaaS** across 4–5 Ubuntu Linux PCs connected via the college laboratory Local Area Network (LAN).

---

## 1. Network Architecture

```text
               College Laboratory LAN (Switch / Wi-Fi)
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
 ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
 │   Master PC   │       │  Worker PC 1  │       │  Worker PC 2  │
 │ 192.168.1.100 │       │ 192.168.1.101 │       │ 192.168.1.102 │
 └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
         │                       │                       │
   - NameNode (9000)         - DataNode              - DataNode
   - DataNode (9864)           (Block Storage)         (Block Storage)
   - WebHDFS (9870)
   - Flask API (5000)
   - React UI (5173)
```

- **Master PC (1 PC)**: Runs Hadoop NameNode, a local DataNode, Flask Cloud Controller, and React frontend.
- **Worker PCs (3–4 PCs)**: Run Hadoop DataNodes to store distributed, encrypted file chunks.
- **Clients**: Any browser on the LAN can open `http://<MASTER_IP>:5173` to upload, download, and manage shared files.

---

## 2. Prerequisites on All PCs

1. **Operating System**: Ubuntu 22.04 LTS or 24.04 LTS.
2. **Java**: OpenJDK 11 (`sudo apt install openjdk-11-jdk`).
3. **Hadoop**: Apache Hadoop 3.3.6 installed in `/usr/local/hadoop`.
4. **Python**: Python 3.10+ installed on the Master PC.
5. **Node.js**: Node.js v18+ and npm installed on the Master PC.

---

## 3. Network Configuration & `/etc/hosts`

Determine the IP address of each PC (`ip addr show` or `hostname -I`).
For best stability, add hostname mappings to `/etc/hosts` on **all PCs**:

```bash
sudo nano /etc/hosts
```

Add lines matching your lab IP allocation:
```text
192.168.1.100  master
192.168.1.101  node1
192.168.1.102  node2
192.168.1.103  node3
192.168.1.104  node4
```

### Firewall Configuration (Ubuntu UFW)
Ensure the required ports are open between lab machines:

**On Master PC:**
```bash
sudo ufw allow 9000/tcp   # HDFS RPC
sudo ufw allow 9870/tcp   # WebHDFS / NameNode UI
sudo ufw allow 9864/tcp   # DataNode HTTP
sudo ufw allow 9866/tcp   # DataNode Data Transfer
sudo ufw allow 5000/tcp   # Flask Cloud Controller REST API
sudo ufw allow 5173/tcp   # React Web Interface
```

**On Worker PCs:**
```bash
sudo ufw allow 9864/tcp   # DataNode HTTP
sudo ufw allow 9866/tcp   # DataNode Data Transfer
sudo ufw allow 9867/tcp   # DataNode IPC
```

---

## 4. Master PC Setup

1. **Clone the Repository**:
   ```bash
   git clone <repo-url> /home/sanmesh/Cloud-Storage-SaaS
   cd /home/sanmesh/Cloud-Storage-SaaS
   ```

2. **Configure Hadoop Master IP**:
   Edit `hadoop_conf/core-site.xml`:
   ```xml
   <property>
       <name>fs.defaultFS</name>
       <value>hdfs://192.168.1.100:9000</value>
   </property>
   ```

3. **Configure Replication Factor**:
   Edit `hadoop_conf/hdfs-site.xml` to match your cluster size (e.g. 3 or 4):
   ```xml
   <property>
       <name>dfs.replication</name>
       <value>3</value>
   </property>
   ```

4. **Register Worker Nodes**:
   Edit `hadoop_conf/workers`:
   ```text
   192.168.1.100
   192.168.1.101
   192.168.1.102
   192.168.1.103
   ```

5. **Configure Backend Environment**:
   Edit `backend/.env`:
   ```ini
   MASTER_IP=192.168.1.100
   WEBHDFS_PORT=9870
   WEBHDFS_URL=http://192.168.1.100:9870/webhdfs/v1
   HDFS_USER=sanmesh
   STORAGE_ROOT=/cloud-storage/shared
   CHUNK_SIZE=1048576
   SECRET_KEY=lan-cloud-storage-super-secret-key-2026
   AES_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
   ```

6. **Start All Services on Master**:
   ```bash
   ./scripts/start_master.sh
   ```

---

## 5. Worker PC (DataNode) Setup

On each Worker PC (e.g., `192.168.1.101`):

1. Copy the `hadoop_conf/` directory from the Master PC.
2. Run the DataNode startup script:
   ```bash
   ./scripts/start_datanode.sh
   ```
3. The DataNode will automatically connect to `hdfs://192.168.1.100:9000` and register with the NameNode.

---

## 6. Verification & Demonstration Steps

### Step 1: Verify Cluster Health
On the Master PC (or any browser on the LAN):
- Open `http://192.168.1.100:9870/dfshealth.html#tab-datanode`
- Confirm all 4–5 DataNodes appear with status **In service**!

### Step 2: Open the Cloud Storage SaaS UI
From **any** student or lab PC on the network:
- Open `http://192.168.1.100:5173` in your browser.
- Log in using one of the demo credentials:
  - `admin` / `admin123`
  - `student1` / `labpass1`
  - `student2` / `labpass2`

### Step 3: Test Upload & Distributed Encryption
1. Click **+ New -> File upload**.
2. Select a file larger than 1 MiB (e.g. a 5 MB PDF or image).
3. The UI will display progress as the controller segments the file into 1 MiB chunks and encrypts each chunk using AES-256-GCM.
4. Chunks are distributed across the DataNodes in HDFS.

### Step 4: Test Shared Access from Multiple PCs
1. Log in as `student1` on PC 1 and create a folder named `Team_Project`.
2. Upload a file into `Team_Project`.
3. Log in as `student2` on PC 2:
   - Notice `Team_Project` and the uploaded file appear immediately!
   - Click **Download** on PC 2.
   - The file is reconstructed byte-for-byte and verified.

---

## 7. Troubleshooting & Diagnostics

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **DataNode not appearing in NameNode UI** | Firewall blocking port 9000 or mismatch in `core-site.xml` | Run `sudo ufw allow 9000` on Master and verify `fs.defaultFS` points to Master IP. |
| **Download fails with HTTP 500** | DataNode HTTP port 9864 blocked | Allow port 9864 on all DataNodes (`sudo ufw allow 9864`). |
| **NameNode in Safe Mode** | Cluster newly started | Run `hdfs dfsadmin -safemode leave` on Master. |
| **Permission Denied in WebHDFS** | User mismatch | Check `HDFS_USER` in `backend/.env` matches the local user running HDFS. |

