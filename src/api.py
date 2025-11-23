import logging
from flask import Flask, request

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/welcome')
def welcome():
    logger.info(f"Request received: {request.method} {request.path}")
    return {'message': 'Welcome to the GDC Attendance System API!'}

def start_api_server():
    from threading import Thread
    def run_app():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    thread = Thread(target=run_app, daemon=True)
    thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
