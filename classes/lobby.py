from classes.player import Player
from classes.turn import Turn
from helpers import player_list_to_dict, sort_player_dict_without_images
import eventlet
import time
eventlet.monkey_patch()


class Lobby:
    def __init__(self, lobby_id, password, sock, db):
        self.lobby_id = lobby_id
        self.player_list = []
        self.admin = ""  # string, will update when a player joins
        self.password = password
        self.started = False
        self.language = "English"
        self.draw_time = 90
        self.rounds = 6
        self.gamemode = "Classic"
        self.difficulty = "Normal"
        self.points_limit = 250000
        self.custom_words = []
        self.current_turn = None  # will be changed once starts
        self.sock = sock
        self.db = db
        self.winner = None

    def is_full(self):
        ''' max players allowed in a single lobby is 10 '''
        return len(self.player_list) >= 10

    def add_player(self, username, sid, user_obj):
        """ creates a Player object by its username and sid, and appends him to the player list. """
        if len(self.player_list) == 0:
            self.admin = username
        for player in self.player_list:  # validating, same user cant enter twice
            if player.username == username:
                print("Player {} already in lobby {}".format(username, self.lobby_id))
                return
        new_player = Player(username, sid, user_obj)
        self.player_list.append(new_player)
        self.sock.emit('game_overlay', {'type': 'lobby'}, room=sid, namespace='/lobby')
        print("sent scoreboard")
        self.sock.emit('update_player_list', player_list_to_dict(self.player_list, False), room=self.lobby_id, namespace='/lobby')
        print("username '{}' with sid '{}' joined".format(username, sid))
        self.emit_settings()
        if self.current_turn:
            self.current_turn.player_joined(new_player)

    def remove_player(self, username):
        """ returns True if the lobby should be removed from lobbyhandler (no more players in room)"""
        print("player removed by Lobby")
        if len(self.player_list) <= 1:
            self.player_list = []
            self.admin = ""
            self.started = False
            return True
        i = 0
        found = False
        for p in self.player_list:
            if username == p.username:
                self.player_list.pop(i)
                if username == self.admin:  # update admin if he disconnected
                    self.admin = self.player_list[0].username
                found = True
                break
            i += 1
        self.sock.emit('update_player_list', player_list_to_dict(self.player_list, False), room=self.lobby_id,
                       namespace='/lobby')
        if found:
            if self.current_turn:
                self.current_turn.remove_player(username)
        else:
            print("Player {} was not in lobby {}".format(username, self.lobby_id))
        return False

    def emit_settings(self):
        str_custom_words = ",".join(self.custom_words)
        json = {'language': self.language, 'draw_time': self.draw_time, 'rounds': self.rounds,
                'custom_words': str_custom_words, 'points_limit': self.points_limit, 'difficulty': self.difficulty}
        if self.gamemode == "Points_Rush":
            json['gamemode'] = "Points Rush"
        elif self.gamemode == "Classic":
            json['gamemode'] = "Classic"
        self.sock.emit('settings_update', json, room=self.lobby_id, namespace='/lobby')

    def update_settings(self, language, draw_time, rounds, gamemode, points_limit, difficulty, custom_words):
        """ sets up the lobby's settings """
        if self.current_turn:  # cannot change settings mid-game
            return
        print("set up room: {}".format(self.lobby_id))
        if language in ["English", "Hebrew", "Italian", "Dutch", "French", "German"]:
            self.language = language
        if draw_time in [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]:
            self.draw_time = draw_time
        if rounds in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
            self.rounds = rounds
        self.custom_words = custom_words
        # str_custom_words = ",".join(custom_words)
        if gamemode in ["Classic", "Points_Rush"]:
            self.gamemode = gamemode
        if points_limit in [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 5000]:
            self.points_limit = points_limit
        if difficulty in ["Normal", "Difficult"]:
            self.difficulty = difficulty
        self.emit_settings()

    def validate_custom_words(self):
        if self.current_turn:
            return
        # add language filter
        new = []
        for word in self.custom_words:
            if len(word) > 2 and word.isalpha() and word not in new:
                new.append(word)
        self.custom_words = new

    def get_player_queue(self):
        """ creates a copy of the current player list as a queue of artists for the current round """
        queue = self.player_list.copy()
        return queue

    def get_game_results(self):
        my_dict = sort_player_dict_without_images(player_list_to_dict(self.player_list, True, False))
        winner = list(my_dict)[0]
        return winner, my_dict

    def start_game(self):
        """ starts the game, should be a thread target """
        self.winner = None
        self.started = True
        curr_round = 1
        should_end = False
        while len(self.player_list) > 1 and not should_end:
            self.sock.emit('game_overlay', {'type': 'new_round', 'curr_round': curr_round}, room=self.lobby_id, namespace='/lobby')
            time.sleep(2)  # allow 2 seconds of overlay
            curr_queue = self.get_player_queue()
            for artist in curr_queue:
                if should_end:  # if the point limit was reached
                    break
                if artist in self.player_list:  # ensure artist did not quit
                    curr_turn = Turn(artist, self.player_list, self.draw_time, self.language, self.lobby_id,
                                     self.rounds, curr_round, self.custom_words, self.sock, self.gamemode,
                                     self.points_limit, self.difficulty, self.db)
                    self.current_turn = curr_turn
                    should_end = curr_turn.start_turn()
            curr_round += 1
            if self.gamemode == "Classic" and curr_round > self.rounds:
                should_end = True
        if len(self.player_list) > 0:
            winner, my_dict = self.get_game_results()
            my_dict['type'] = 'game_ended'
            self.sock.emit('game_overlay', my_dict, room=self.lobby_id, namespace='/lobby')
            time.sleep(10)  # allow 10 seconds of game ended overlay
        self.sock.emit('game_overlay', {'type': 'lobby'}, room=self.lobby_id, namespace='/lobby')
        self.started = False
        if len(self.player_list) > 1:
            self.winner = winner
        print("Game done")

    def add_stroke(self, stroke_data, username):
        """ calls for add_stroke of the current turn """
        if self.current_turn:
            self.current_turn.add_stroke(stroke_data, username)

    def test_stroke(self, stroke_data, username):
        """ calls for add_stroke of the current turn """
        if self.current_turn:
            self.current_turn.test_stroke(stroke_data, username)

    def new_chat_message(self, username, message):
        if self.current_turn:
            return self.current_turn.new_chat_message(username, message)
        return None, None

    def set_turn_word(self, word, username):
        if self.current_turn:
            self.current_turn.set_word(word, username)

    def process_hint_request(self, username, my_type):
        if self.current_turn:
            self.current_turn.process_hint_request(username, my_type)

    def request_color_change(self, username, color):
        if self.current_turn:
            self.current_turn.request_color_change(username, color)

    def request_width_change(self, username, width):
        if self.current_turn:
            self.current_turn.request_width_change(username, width)

    def request_action_change(self, username, action):
        if self.current_turn:
            self.current_turn.request_action_change(username, action)

    def process_instruction(self, inst, username):
        if self.current_turn:
            self.current_turn.process_instruction(inst, username)

    def send_entire_drawing(self, sid):
        if self.current_turn:
            self.current_turn.send_entire_drawing(sid)
