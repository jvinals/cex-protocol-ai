import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import eventlet
eventlet.monkey_patch()

from flask import Flask, send_from_directory
from flask_cors import CORS
import socketio
from src.models.user import db
from src.routes.user import user_bp
from src.routes.phone_calls import phone_calls_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app, origins="*")

# Initialize Socket.IO
sio = socketio.Server(cors_allowed_origins="*", async_mode='eventlet')
socket_app = socketio.WSGIApp(sio, app.wsgi_app)
app.wsgi_app = socket_app

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(phone_calls_bp, url_prefix='/api')

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Debug: Print all registered routes
print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule} [{', '.join(rule.methods)}]")

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return {"message": "CEX Protocol AI Backend API"}


if __name__ == '__main__':
    print("Starting server on http://0.0.0.0:5001")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5001)), socket_app)
