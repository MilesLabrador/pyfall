from flask import Flask, render_template, request
from flask_socketio import SocketIO

from locations import locations
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)
gamerooms = {} # initialize dictionary that keeps track of all gamerooms open and 
class spyfallround():
    duration = 480 # default duration is 8 minutes
    players = [] # initialize player list
    players_roles = {} # initialize player roles dictionary
    def __init__(self, gamekey, duration, host):
        self.duration = duration
        self.location = np.random.choice(list(locations.keys()))
        self.gamekey = gamekey
        self.players = [host]
    def assign_roles(self):
        """Randomly assign roles to players of the game with minimal duplicates"""
        players_list = self.players # grab all players
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

@app.route('/')
def index():
    """Serve index html"""
    print('hello!')
    return render_template('index.html')

@app.route('/<gamekey>')
def gameroom(gamekey):
    print(gamekey)
    return 'your gamekey is: '+ gamekey

@socketio.on('newgame')
def create_game(json, methods=['GET','POST']):
    """Initializes an instance of the the class spyfallround, which will serve roles and game parameters"""
    print('recieved new game request: '+str(json))
    createinfo_dict = dict(json) # convert json to dict to parse data from
    gamerooms[createinfo_dict['gamekey']] = spyfallround(createinfo_dict['gamekey'], createinfo_dict['duration'], createinfo_dict['name']) # Create instance of spyfallround() with the socketio emitted user inputs from the create game page
    print(gamerooms)
    socketio.emit('')

@socketio.on('joingame')
def join_game(json, methods=['GET','POST']):
    """check if gamekey is valid, if so add player to appropriate game"""
    
    print('recieved join game request: '+str(json))
    joininfo_dict = dict(json)
    if joininfo_dict['gamekey'] in gamerooms.keys():
      print('User has a valid gamekey, let him join!')
      gamerooms[joininfo_dict['gamekey']].players.append(joininfo_dict['name'])
      print(gamerooms[joininfo_dict['gamekey']].players)
    else:
      print("Invalid gameroom key, nothing to join")
    socket_id = request.sid
    print('socket_id', socket_id)
    socketio.emit('')


@socketio.on('newconnection')
def new_connection(json, methods=['GET','POST']):
    print('new connection: '+ str(json))
    socket_id = request.sid
    print('socketid', socket_id)
if __name__ == '__main__':
    socketio.run(app, debug=True)
