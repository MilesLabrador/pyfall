from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

from locations import locations
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

def create_possible_locations_html():
    """From a given python dictionary, create a set of html list elemnts to display all possible locations for a game"""
    html_locations_list = ''
    for location in locations.keys():
        html_locations_list+='<li>{}</li>'.format(location)
    return html_locations_list
possible_locations_html = create_possible_locations_html()


gamerooms = {} # initialize dictionary that keeps track of all open gamerooms and their spyfallround class using format {gamekey : spyfallround class object}
sockets_gamekey = {} #initialize dictionary that keeps track of which game each individual user (socket) is in by recording their gamekey and socket_id format {socket_id : gamekey}

class spyfallround():
    duration = 480 # default duration is 8 minutes
    players = {} # initialize player dictionary, which will use format {player_name : player_socket_id}
    players_roles = {} # initialize player roles dictionary
    def __init__(self, gamekey, duration, host, host_socket_id):
        self.duration = duration
        self.location = np.random.choice(list(locations.keys())) # Randomly choose location from set dictionary of locations and roles
        self.gamekey = gamekey
        self.players = {host:host_socket_id}
        self.started = False
    def assign_roles(self):
        """Randomly assign roles to players of the game with minimal duplicates"""
        
        players_list = list(self.players.keys()) # grab all players
        roles_list = locations[self.location] # list of roles from our locations dictionary
        
        self.spy = np.random.choice(players_list) #randomly choose spy
        
        if len(players_list)-1 > len(roles_list): #If there are more non-spies than there are non-spy roles, extend the roles list
            playerlen = len(players_list)-1
            rolelen = len(roles_list)
            multiplier = playerlen//rolelen # How many copies of the entire role list can we fill for sure?
            remainder = playerlen%rolelen # How many individual additional roles will we have to add to assign all players a role if we have non-whole multiplier?
            self.roles = roles_list*multiplier
            self.roles.extend(list(np.random.choice(roles_list, remainder, replace=False))) #Create list of roles that minimizes duplicates and is equal to number of players

            self.roles = np.random.choice(self.roles, len(self.roles), replace=False) # Shuffle the roles order
        else: # If there are less players than roles, just use the non-extended roles list
            self.roles = roles_list
        n=0
        for player in players_list: # Assign roles from shuffled roles list or 'Spy' to user who is spy
            if player != self.spy:
                self.players_roles[player] = self.roles[n]
                n+=1
            else:
                self.players_roles[player] = 'Spy'
    
    def create_players_list_html(self):
        """Create a set of html list elements to display players in a spyfallround class"""
        html_players_list = ''
        for player in self.players:
            html_players_list+='<li>{}</li>'.format(player)
        return html_players_list

@app.route('/')
def index():
    """Serve index html"""
    print('index_html served')
    return render_template('index.html')

@socketio.on('newgame')
def create_game(json, methods=['GET','POST']):
    """Initializes an instance of the the class spyfallround, which will serve roles and game parameters"""
    global gamerooms
    global sockets_gamekey
    print('recieved new game request: '+str(json))
    createinfo_dict = dict(json) # convert json to dict to parse data from
    socket_id = request.sid # Record the socket ids that are also the default unique rooms for each socket
    sockets_gamekey[socket_id] = createinfo_dict['gamekey'] # Pair socket_id and its respective gamekey for future reference
    gamerooms[createinfo_dict['gamekey']] = spyfallround(createinfo_dict['gamekey'], createinfo_dict['duration'], createinfo_dict['name'], socket_id) # Create instance of spyfallround() with the socketio emitted user inputs from the create game page
    
    join_room(createinfo_dict['gamekey']) # Join the gamekey room, where non-user sensitive but game-instance-sensitive can be emitted
    emit('update_players', gamerooms[createinfo_dict['gamekey']].create_players_list_html(), room=createinfo_dict['gamekey']) # signal that an update to the game's players has happened, since the host just joined the game
    #print('HTML', gamerooms[createinfo_dict['gamekey']].create_players_list())
    print('players_in_game', gamerooms[createinfo_dict['gamekey']].players)
   # print('TOTAL GAMEROOMS:', gamerooms)
    socketio.emit('')

@socketio.on('joingame')
def join_game(json, methods=['GET','POST']):
    """Check if gamekey is valid, if so add player to appropriate game"""
    global gamerooms
    global sockets_gamekey
    print('recieved join game request: '+str(json))
    socket_id = request.sid # Record the socket ids that are also the default unique rooms for each socket
    joininfo_dict = dict(json)

    if joininfo_dict['gamekey'] in gamerooms.keys(): # If the gameroom (and therefore gamekey) exists
      if joininfo_dict['name'] not in gamerooms[joininfo_dict['gamekey']].players: # If the gamekey exists and the input name ISNT taken, add the user to the gameroom and indicate an update in players
          sockets_gamekey[socket_id] = joininfo_dict['gamekey']
          print('Valid Gamekey, Valid Name, JOIN')
          gamerooms[joininfo_dict['gamekey']].players[joininfo_dict['name']] = socket_id
          print('total_players_in_game', gamerooms[joininfo_dict['gamekey']].players)
          emit('joingameserver', joininfo_dict['gamekey'], room=socket_id) # Give the go ahead for the socket to join the waiting room and display the gamekey
          join_room(joininfo_dict['gamekey']) # Join the gamekey room, where non-user sensitive but game-instance-sensitive can be emitted
          emit('update_players', gamerooms[joininfo_dict['gamekey']].create_players_list_html(), room=joininfo_dict['gamekey'])
      else:
        print('Valid Gamekey, but Name taken, DONT JOIN')
    else:
      print("Invalid Gamekey, DONT JOIN")
    socketio.emit('')

@socketio.on('startgame')
def startgame():
    """Initialize spyfall round by assigning players information like location and role"""
    global gamerooms
    global sockets_gamekey
    global possible_locations

    print('startgame')
    socket_id = request.sid # Record the socket ids that are also the default unique rooms for each socket
    gamerooms[sockets_gamekey[socket_id]].started = True # Indicate that the spyfallround has been initialized
    gamerooms[sockets_gamekey[socket_id]].assign_roles() # Shuffle and assign roles to each player
    
    for player in gamerooms[sockets_gamekey[socket_id]].players.keys(): #
        print(player, socket_id)
        # print('STORED SOCKET', gamerooms[sockets_gamekey[socket_id]].players[player])
        print('ROLE', gamerooms[sockets_gamekey[socket_id]].players_roles[player])
        
        role = gamerooms[sockets_gamekey[socket_id]].players_roles[player]
        if role != 'Spy': # If the player isn't a spy, allow the emission of the location and display "You are not the spy!"
            location = gamerooms[sockets_gamekey[socket_id]].location
            spyqualifier = "You are not the spy!"
        else: #If the player is a spy, hide the location and display "You are the spy!"
            location = '?'
            spyqualifier = "You are the spy!"
        
        emit('startgame', {"role" : role, "location" : location, "spyqualifier": spyqualifier, "possible_locations" : possible_locations_html}, room=gamerooms[sockets_gamekey[socket_id]].players[player]) # emit unique player information such as role and location to each socket
    #print('total_players FINAL', gamerooms[sockets_gamekey[socket_id]].players)

@socketio.on('newconnection')
def new_connection(json, methods=['GET','POST']):
    print('new connection: '+ str(json))
    socket_id = request.sid # Record the socket ids that are also the default unique rooms for each socket
    print('socket_id', socket_id)
if __name__ == '__main__':
    socketio.run(app, debug=True)
