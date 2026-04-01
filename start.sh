#!/bin/bash
cd /Users/Mike/Desktop/Sandbox/rome-flip-analyzer
exec /Users/Mike/Library/Python/3.9/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
