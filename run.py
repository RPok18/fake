
import os
import sys

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from web.app import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
