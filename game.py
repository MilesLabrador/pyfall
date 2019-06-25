from flask import Flask, render_template
from flask_socketio import SocketIO

from locations import locations

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    """Serve index html"""
    print('hello!')
    return render_template('index.html')
if __name__ == '__main__':
    socketio.run(app)
