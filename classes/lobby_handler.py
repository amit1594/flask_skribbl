from classes.lobby import Lobby
import eventlet
eventlet.monkey_patch()


class LobbyHandler:
    """
        A class that represents a handler for all lobbies.

        ...

        Attributes
        ----------
        lobbies : dict {lobby_id: lobby}
            a dict of all lobbies
        sock : Socket
            the socket the game will go over with

        Methods
        -------
        add_lobby(lobby_id, password):
            adds a new lobby to the list
        remove_lobby(lobby_id):
            removes the lobby with the given id
        get_lobby(lobby_id):
            returns the corresponding lobby or None if doesn't exist

    """
    def __init__(self, socket):
        self.lobbies = dict()
        self.sock = socket

    def add_lobby(self, lobby_id, password):
        if lobby_id in self.lobbies.keys():
            print("Lobby {} already exists".format(lobby_id))
            return
        new_lobby = Lobby(lobby_id, password, self.sock)
        self.lobbies[lobby_id] = new_lobby

    def remove_lobby(self, lobby_id):
        if lobby_id not in self.lobbies.keys():
            print("Lobby {} does not exist".format(lobby_id))
            return
        self.lobbies[lobby_id].started = False  # close lobby
        if self.lobbies[lobby_id].current_turn:  # close turn
            self.lobbies[lobby_id].current_turn.terminate()
        self.lobbies.pop(lobby_id)

    def get_lobby(self, lobby_id):
        if lobby_id in self.lobbies.keys():
            return self.lobbies[lobby_id]
        print("Lobby {} does not exist".format(lobby_id))
        return None
