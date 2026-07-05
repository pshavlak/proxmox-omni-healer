# Run the app from the site directory
import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

uvicorn.run('app:app', host='127.0.0.1', port=8766, log_level='debug')
