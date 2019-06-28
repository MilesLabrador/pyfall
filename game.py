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

@socketio.on('newgame')
def create_game(json, methods=['GET','POST']):
    print('recieved new game request: '+str(json))
    socketio.emit('')

@socketio.on('joingame')
def join_game(json, methods=['GET','POST']):
    print('recieved join game request: '+str(json))
    socketio.emit('')


@socketio.on('newconnection')
def new_connection(json, methods=['GET','POST']):
    print('new connection: '+ str(json))
if __name__ == '__main__':
    socketio.run(app, debug=True)
