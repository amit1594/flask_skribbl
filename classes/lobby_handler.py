from classes.lobby import Lobby
import eventlet
eventlet.monkey_patch()


class LobbyHandler:
    def __init__(self, socket, db):
        self.lobbies = dict()
        self.sock = socket
        self.db = db

    def add_lobby(self, lobby_id, password):
        if lobby_id in self.lobbies.keys():
            print("Lobby {} already exists".format(lobby_id))
            return
        new_lobby = Lobby(lobby_id, password, self.sock, self.db)
        self.lobbies[lobby_id] = new_lobby

    def remove_lobby(self, lobby_id):
        if lobby_id not in self.lobbies.keys():
            print("Lobby {} not deleted, it does not exist".format(lobby_id))
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
