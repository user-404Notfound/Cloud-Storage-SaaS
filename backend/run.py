#!/usr/bin/env python3
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = Config.DEBUG
    print(f"Starting Flask Cloud Controller on http://{host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

