from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

from locations import locations
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)
gamerooms = {} # initialize dictionary that keeps track of all gamerooms open and
sockets_gamekey = {}
class spyfallround():
    duration = 480 # default duration is 8 minutes
    players = [] # initialize player list
    players_roles = {} # initialize player roles dictionary
    def __init__(self, gamekey, duration, host, host_socket):
        self.duration = duration
        self.location = np.random.choice(list(locations.keys()))
        self.gamekey = gamekey
        self.players = {host:host_socket}
        self.started = False
    def assign_roles(self):
        """Randomly assign roles to players of the game with minimal duplicates"""
        players_list = list(self.players.keys()) # grab all players
        roles_list = locations[self.location] #list of roles from our locations dictionary
        self.spy = np.random.choice(players_list) #randomly choose spy
        if len(players_list)-1 > len(roles_list): #If there are more non-spies than there are non-spy roles, extend the roles list
            playerlen = len(players_list)-1
            rolelen = len(roles_list)
            multiplier = playerlen//rolelen # How many copies of the entire role list can we fill for sure?
            remainder = playerlen%rolelen # How many individual additional roles will we have to add to assign all players a role if we have non-whole multiplier?
            self.roles = roles_list*multiplier
            self.roles.extend(list(np.random.choice(roles_list, remainder, replace=False))) #Create list of roles that minimizes duplicates and is equal to number of players

            self.roles = np.random.choice(self.roles, len(self.roles), replace=False)# Shuffle the roles order
        else:
            self.roles = roles_list
        n=0
        for player in players_list: #Assign roles from shuffled roles list or 'Spy' to user who is spy
            if player != self.spy:
                self.players_roles[player] = self.roles[n]
                n+=1
            else:
                self.players_roles[player] = 'Spy'
        self.started = True
    def create_players_list_html(self):
        html_players_list = ''
        for player in self.players:
            html_players_list+='<li>{}</li>'.format(player)
        return html_players_list

@app.route('/')
def index():
    """Serve index html"""
    print('hello!')
    return render_template('index.html')

@app.route('/<gamekey>')
def gameroom(gamekey, methods=['GET','POST']):
    #print(gamekey)
    #print('socketid gamekeypage',request.sid)
    return render_template('index.html')
    #return 'your gamekey is: '+ gamekey

@socketio.on('newgame')
def create_game(json, methods=['GET','POST']):
    """Initializes an instance of the the class spyfallround, which will serve roles and game parameters"""
    global gamerooms
    global sockets_gamekey
    print('recieved new game request: '+str(json))
    createinfo_dict = dict(json) # convert json to dict to parse data from
    socket_id = request.sid
    sockets_gamekey[socket_id] = createinfo_dict['gamekey']
    gamerooms[createinfo_dict['gamekey']] = spyfallround(createinfo_dict['gamekey'], createinfo_dict['duration'], createinfo_dict['name'], socket_id) # Create instance of spyfallround() with the socketio emitted user inputs from the create game page
    join_room(createinfo_dict['gamekey'])
    emit('update_players', gamerooms[createinfo_dict['gamekey']].create_players_list_html(), room=createinfo_dict['gamekey'])
    print('HTML', gamerooms[createinfo_dict['gamekey']].create_players_list())
    print('players_in_game', gamerooms[createinfo_dict['gamekey']].players)
    print('TOTAL GAMEROOMS:', gamerooms)
    socketio.emit('')

@socketio.on('joingame')
def join_game(json, methods=['GET','POST']):
    """check if gamekey is valid, if so add player to appropriate game"""
    global gamerooms
    global sockets_gamekey
    print('recieved join game request: '+str(json))
    socket_id = request.sid
    joininfo_dict = dict(json)
    if joininfo_dict['gamekey'] in gamerooms.keys():
      if joininfo_dict['name'] not in gamerooms[joininfo_dict['gamekey']].players:
          sockets_gamekey[socket_id] = joininfo_dict['gamekey']
          print('Valid Gamekey, Valid Name, JOIN')
          gamerooms[joininfo_dict['gamekey']].players[joininfo_dict['name']] = socket_id
          print('total_players_in_game', gamerooms[joininfo_dict['gamekey']].players)
          emit('joingameserver', joininfo_dict['gamekey'], room=socket_id)
          join_room(joininfo_dict['gamekey'])
          emit('update_players', gamerooms[joininfo_dict['gamekey']].create_players_list_html(), room=joininfo_dict['gamekey'])
      else:
        print('Valid Gamekey, but Name taken, DONT JOIN')
    else:
      print("Invalid Gamekey, DONT JOIN")
    socketio.emit('')
@socketio.on('startgame')
def startgame():
    global gamerooms
    global sockets_gamekey
    print('startgame')
    #print('players_in_game',)
    socket_id = request.sid
    gamerooms[sockets_gamekey[socket_id]].started = True
    gamerooms[sockets_gamekey[socket_id]].assign_roles()
    for player in gamerooms[sockets_gamekey[socket_id]].players.keys():
        print(player, socket_id)
        print('STORED SOCKET', gamerooms[sockets_gamekey[socket_id]].players[player])
        print('ROLE', gamerooms[sockets_gamekey[socket_id]].players_roles[player])
        emit('startgame', gamerooms[sockets_gamekey[socket_id]].players_roles[player], room=gamerooms[sockets_gamekey[socket_id]].players[player])
    print('total_players FINAL', gamerooms[sockets_gamekey[socket_id]].players)

@socketio.on('newconnection')
def new_connection(json, methods=['GET','POST']):
    print('new connection: '+ str(json))
    socket_id = request.sid
    print('socket_id',request.sid)
if __name__ == '__main__':
    socketio.run(app, debug=True)
