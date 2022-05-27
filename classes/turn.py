from classes.player import Player
from helpers import get_color_by_name, player_list_to_dict, sort_player_dict, sort_player_dict_without_images
from helpers import get_prohibited_chars, get_prohibited_words, validate_width, validate_color, getRandomNumbers
import eventlet
import time
import os
eventlet.monkey_patch()


class Turn:
    def __init__(self, artist, player_list, max_time, language, room, total_rounds, current_round, custom_words, sock,
                 gamemode, points_limit, difficulty, db):
        self.total_rounds = total_rounds  # int
        self.current_round = current_round  # int
        self.active = True
        self.artist = artist  # Player obj
        self.player_list = player_list  # list of player obj
        self.max_turn_time = max_time  # int
        self.current_time = max_time  # int
        self.language = language  # string
        self.word_options = ()  # tuple of strings
        self.word = None  # string
        self.waiting_for_word = False
        self.room = room  # id - string
        self.all_guessed = False
        self.guessed = dict()  # dict {username: added_points)}
        self.strokes = []  # list of json
        self.used_hints = []  # list of usernames
        self.hints = []  # list
        self.current_overlay = ""
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.custom_words = custom_words
        self.sock = sock  # socket
        self.points_limit = points_limit
        self.return_end_of_game = False
        self.color = get_color_by_name('black')
        self.width = 2
        self.action = 'pen'  # drawing action
        self.instructions = []
        self.db = db

    def terminate(self):
        """ terminates the turn """
        self.active = False

    def send_current_overlay(self):
        for p in self.player_list:
            if self.current_overlay == "" or self.current_overlay == "lobby":
                self.sock.emit('game_overlay', {'type': 'lobby'}, room=p.sid, namespace='/lobby')
            elif self.current_overlay == "artist_choosing_a_word":
                if p.username == self.artist.username:
                    json = {'type': "word_to_choose_from", 'current_round': self.current_round,
                            'total_rounds': self.total_rounds, 'w1': self.word_options[0],
                            'w2': self.word_options[1], 'w3': self.word_options[2], 'gamemode': self.gamemode}
                else:
                    json = {'type': self.current_overlay, 'artist': self.artist.username, 'gamemode': self.gamemode,
                            'current_round': self.current_round, 'total_rounds': self.total_rounds}
                self.sock.emit('game_overlay', json, room=p.sid, namespace='/lobby')
            elif self.current_overlay == "guessing_view":
                json = {'time': self.current_time}
                if p.username == self.artist.username:
                    json['type'] = 'artist_view'
                    json['word'] = self.get_encoded_word(True, True)
                elif p.username in self.used_hints:
                    json['type'] = self.current_overlay
                    json['encoded_word'] = self.get_encoded_word(False, True)
                    json['need_hint_box'] = False
                else:  # did not use a hint
                    json['type'] = self.current_overlay
                    json['encoded_word'] = self.get_encoded_word(False, False)
                    json['need_hint_box'] = True
                self.sock.emit('game_overlay', json, room=p.sid, namespace='/lobby')
            elif self.current_overlay == "turn_ended":
                my_dict = self.guessed
                my_dict['type'] = 'turn_ended'
                self.sock.emit('game_overlay', my_dict, room=self.room, namespace='/lobby')

    def send_current_scoreboard(self):
        """ emits the current scoreboard """
        if not self.active:
            return
        my_dict = sort_player_dict(player_list_to_dict(self.player_list, True, True))
        # print(my_dict)
        self.sock.emit('update_scoreboard', my_dict, room=self.room, namespace='/lobby')

    def get_player_object_by_username(self, username):
        """ returns the respective player object to the username, returns None if username doesn't exist """
        if not self.active:
            return None
        for player in self.player_list:
            if player.username == username:
                return player
        return None

    def remove_player(self, username):
        """ removes player from guessed and emits current scoreboard
            note: the player_list updates automatically, so this method does not change it """
        if not self.active:
            return
        print("player removed by Turn")
        self.guessed.pop(username, None)  # None used to not throw exception if username doesnt exist in dict
        self.sock.emit('chat_message', {'type': 'left_alert', 'username': username}, room=self.room, namespace='/lobby')
        self.send_current_scoreboard()
        if username == self.artist.username or len(self.player_list) < 2:
            self.terminate()

    def did_all_guess(self):
        """ Returns true if everyone (except the artist) guessed correctly """
        if not self.active:
            return False
        for player in self.player_list:
            if player.username != self.artist.username and player.username not in self.guessed.keys():
                print(self.guessed)
                print(player.username)
                return False
        return True

    def char_difference(self, msg):
        if not self.active or not self.word:
            return False
        if len(msg) != len(self.word):
            return False
        counter = 0
        for index in range(len(self.word)):
            if self.word[index].upper() != msg[index].upper():
                counter += 1
        return counter

    def add_points_to_player(self, player):
        if not self.active or self.word is None or player not in self.player_list:
            return None, None
        time_diff = self.max_turn_time - self.current_time
        if player.username == self.artist.username:
            if len(self.guessed) == 0:
                self.artist.add_points(0)
                return None, None
            try:
                points_received = (50 * len(self.guessed)) - time_diff + 20 * len(self.word)
                points_received = max(int(points_received), 0)
                self.artist.add_points(points_received)
            except ZeroDivisionError:
                points_received = 0
                self.artist.add_points(0)
        else:
            points_received = int(1000 - (5 * time_diff) - 50 * len(self.guessed) + 10 * len(self.word))
            player.add_points(points_received)
            '''if not player.is_guest():
                print(player.user)
                player.user.words_guessed_correctly += 1
                player.user.seconds_took_to_guess += time_diff
                self.db.session.commit()
                print(self.db, self.db.session)
                print("commited: ", player.user.words_guessed_correctly)'''
        self.send_current_scoreboard()
        if player.score > self.points_limit:
            self.terminate()
            self.return_end_of_game = True
            return
        print("Gave", player.username, points_received, "Points")
        return points_received, time_diff

    def new_chat_message(self, username, message):
        """ processes a  chat message"""
        if not self.active or not self.word:
            return False, None, None
        player = self.get_player_object_by_username(username)
        if not player:  # unrecognized username
            print("unrecognized username")
            return True, None, None
        # put in language filter
        prohibited_chars = get_prohibited_chars()
        for c in prohibited_chars:
            if c in message:
                self.sock.emit('chat_message', {'username': username, 'message': '', 'type': 'prohibited'},
                               room=player.sid, namespace='/lobby')
                return True, None, None
        prohibited_words = get_prohibited_words()
        for word in prohibited_words:
            if word in message:
                self.sock.emit('chat_message', {'username': username, 'message': '', 'type': 'prohibited'},
                               room=player.sid, namespace='/lobby')
                return True, None, None
        json = {'username': username, 'message': message}
        if username in self.guessed.keys() or username == self.artist.username:  # if guessed correctly before
            json['type'] = "guessed_chat"
            for tempP in self.player_list:  # send to everyone who already guessed
                if tempP.username in self.guessed.keys():
                    self.sock.emit('chat_message', json, room=tempP.sid, namespace='/lobby')
            self.send_to_artist('chat_message', json)
            return False, None, None
        elif message.upper() == self.word.upper():  # correct guess
            print("Giving guesser points for correct guess")
            points, time_diff = self.add_points_to_player(player)
            if points is not None:
                self.guessed[username] = points
            self.reduce_time(self.current_time // 3)
            self.all_guessed = self.did_all_guess()
            self.sock.emit('chat_message', {'username': username, 'type': 'correct'}, room=self.room, namespace='/lobby')
            return True, points, time_diff
        else:
            for tempP in self.player_list:
                if tempP.username == username and self.char_difference(message) == 1:  # almost correct
                    json['type'] = "almost_correct"
                    self.sock.emit('chat_message', json, room=tempP.sid, namespace='/lobby')
                else:  # every one else sees it as a regular message
                    json['type'] = "regular"
                    self.sock.emit('chat_message', json, room=tempP.sid, namespace='/lobby')
        return True, None, None

    def add_current_width_instruction(self):
        inst = {'inst_type': 'change_width', 'width': self.width}
        self.instructions.append(inst)
        self.send_to_all('new_instruction', inst)

    def add_current_color_instruction(self):
        inst = {'inst_type': 'change_color', 'color': self.color}
        self.instructions.append(inst)
        self.send_to_all('new_instruction', inst)

    def add_current_action_instruction(self):
        inst = {'inst_type': 'change_action', 'action': self.action}
        self.instructions.append(inst)
        self.send_to_all('new_instruction', inst)
        print("Sent to all: ", inst)

    def send_all_instructions(self, room):
        for inst in self.instructions:
            self.sock.emit('new_instruction', inst, room=room, namespace='/lobby')

    def send_entire_drawing(self, sid):
        self.sock.emit('new_instruction', {'inst_type': 'clear'}, room=sid, namespace='/lobby')
        self.send_all_instructions(sid)

    def process_instruction(self, inst, username):
        print("Received new istruction:\n", inst)
        if not self.active or username != self.artist.username or 'inst_type' not in inst:
            return
        inst_type = inst.get('inst_type')
        if inst_type == "clear":
            self.send_to_all('new_instruction', {'inst_type': 'clear'})
            self.instructions = []
            self.add_current_width_instruction()
            self.add_current_color_instruction()
            self.add_current_action_instruction()
        elif inst_type == "undo":
            index = len(self.instructions) - 1
            for i in self.instructions[::-1]:
                curr_type = self.instructions[index].get('inst_type')
                if curr_type == "stroke" or curr_type == "fill":
                    print("i:", i)
                    print("inst at index:", self.instructions[index])
                    self.instructions.pop(index)
                    self.send_to_all('new_instruction', {'inst_type': 'clear'})
                    self.send_all_instructions(self.room)  # send to all
                    print("all instructions after:\n", self.instructions)
                    return
                index -= 1
        elif inst_type == "stroke":
            if self.action == 'pen' and len(inst.get('pixels_x', [])) > 0:
                self.instructions.append(inst)
                self.send_to_all_except_artist('new_instruction', inst)
        elif inst_type == "fill":
            if self.action == 'fill':
                self.instructions.append(inst)
                self.send_to_all('new_instruction', inst)
        elif inst_type == "change_width":
            width = inst.get('width', 2)
            if validate_width(width):
                self.width = int(width)  # validate_width made sure its possible!
                self.add_current_width_instruction()
        elif inst_type == "change_color":
            color = inst.get('color', 'black')
            if validate_color(color):
                self.color = get_color_by_name(color)
                self.add_current_color_instruction()
        elif inst_type == "change_action":
            action = inst.get('action', 'pen')
            print("The action i got from inst is", action)
            if action in ['pen', 'fill']:
                self.action = action
                self.add_current_action_instruction()

    def test_stroke(self, stroke_data, username):
        """ appends stroke data and emits to all to draw the stroke"""
        if not self.active or username != self.artist.username:
            return
        # if 'draw_color' in stroke_data.keys() and not validate_color(stroke_data.get('draw_color')):
        #     stroke_data['draw_color'] = 'black'
        draw_op = stroke_data.get('op', None)
        print("got stroke:\n", stroke_data)
        if draw_op == 'undo':
            if len(self.strokes) > 0:
                self.strokes.pop()
                self.send_to_all('draw_test_stroke', {'op': 'clear'})
            for stroke in self.strokes:
                self.send_to_all('draw_test_stroke', stroke)
        elif self.action == 'fill':
            print('filling: ')
            json = {'op': 'fill', 'x': stroke_data.get('x'), 'y': stroke_data.get('y')}
            self.send_to_all('draw_test_stroke', json)
        else:  # regular stroke
            self.strokes.append(stroke_data)  # careful
            self.send_to_all_except_artist('draw_test_stroke', stroke_data)

    def request_color_change(self, username, color):
        if not self.active or username != self.artist.username or not validate_color(color):
            return
        self.color = get_color_by_name(color)
        self.add_current_color_instruction()
        self.send_to_all('color_changed', {'draw_color': self.color})
        print("sent color change:", self.color)

    def request_width_change(self, username, width):
        if not self.active or username != self.artist.username or not validate_width(width):
            return
        self.width = int(width)  # validate_width made sure its possible!
        self.add_current_width_instruction()
        self.send_to_all('width_changed', {'width': self.width})
        print("sent width change:", self.width)

    def request_action_change(self, username, action):
        print("Attempting to change action:", action)
        if not self.active or username != self.artist.username or action not in ['pen', 'fill']:
            return
        self.action = action
        self.add_current_action_instruction()
        self.send_to_all('action_changed', {'action': self.action})
        print("sent action change:", self.action)

    def player_joined(self, player):
        """ emits current scoreboard and send previous strokes to the new player """
        if not self.active:
            return
        self.send_current_overlay()
        self.sock.emit('chat_message', {'type': 'join_alert', 'username': player.username}, room=self.room, namespace='/lobby')
        for stroke in self.strokes:
            self.sock.emit('draw_stroke', stroke, room=player.sid, namespace='/lobby')

    def generate_words(self, language):
        """ generates 3 words from the specified language (will be English if incorrect language) """
        path = os.path.dirname(os.path.realpath(__file__))
        if self.language == "English":
            path += "\\static\\words\\english.txt"
        elif self.language == "Hebrew":
            path += "\\static\\words\\hebrew.txt"
        elif self.language == "Italian":
            path += "\\static\\words\\italian.txt"
        elif self.language == "Dutch":
            path += "\\static\\words\\dutch.txt"
        elif self.language == "French":
            path += "\\static\\words\\french.txt"
        elif self.language == "German":
            path += "\\static\\words\\german.txt"
        else:
            return "test", "testy", "error"
        with open(path, 'rb') as f:
            text = f.read().decode(errors='replace').split()
        for word in self.custom_words:
            if word not in text:
                text.append(word)
        indexes = getRandomNumbers(len(text) - 1, 3)
        return text[indexes[0]], text[indexes[1]], text[indexes[2]]

    def get_encoded_word(self, is_artist, bought_hint):
        """ returns the word, with every letter not in hints replaced by '_' """
        encoded_word = []  # list of ascii values
        if is_artist:
            for index in range(len(self.word)):
                encoded_word.append(ord(self.word[index]))
            return encoded_word
        # there is an extra bought hint at the end but we wanna do every max_time / (hints + 1), so it is fine.
        time_for_hint = self.max_turn_time // (len(self.hints))
        time_passed = self.max_turn_time - self.current_time
        amount_of_hints = min(len(self.hints) - 1, time_passed // time_for_hint)
        curr_hints = self.hints.copy()[:amount_of_hints]
        if bought_hint:  # if bought the hint
            curr_hints.append(self.hints[-1])
        if self.difficulty == "Normal":
            for index in range(len(self.word)):
                if index in curr_hints:
                    encoded_word.append(ord(self.word[index]))
                else:
                    encoded_word.append(ord("_"))
                if index < len(self.word) - 1:  # if not last char
                    encoded_word.append(ord(" "))
        elif self.difficulty == "Difficult":
            for index in range(len(self.word)):
                encoded_word.append(ord("_"))
                if index < len(self.word) - 1:  # if not last char
                    encoded_word.append(ord(" "))
            for i in "     ":
                encoded_word.append(ord(i))
            for index in range(len(curr_hints)):
                encoded_word.append(ord(self.word[curr_hints[index]]))
                if index < len(self.word) - 1:  # if not last char
                    for i in ", ":
                        encoded_word.append(ord(i))
        # print(encoded_word)
        return encoded_word

    def set_word(self, word, username):
        if self.active and self.waiting_for_word and username == self.artist.username:
            self.word = word

    def print_players(self):
        for p in self.player_list:
            print(p.username)

    def send_to_all(self, event_name, json):
        self.sock.emit(event_name, json, room=self.room, namespace='/lobby')

    def send_to_all_except_artist(self, event_name, json):
        print('artist is ' + self.artist.username)
        for p in self.player_list:
            if p.username != self.artist.username:
                print('sent to ' + p.username)
                self.sock.emit(event_name, json, room=p.sid, namespace='/lobby')

    def send_to_artist(self, event_name, json):
        self.sock.emit(event_name, json, room=self.artist.sid, namespace='/lobby')

    def request_word(self):
        """ request the artist to choose a word out of 3, setups overlay as needed """
        print("start requestion words")
        word_options = self.generate_words(self.language)
        self.word_options = word_options
        self.current_overlay = "artist_choosing_a_word"
        self.send_current_overlay()
        timer = 15  # 15 seconds to decide on a word, else will choose the first one
        self.waiting_for_word = True
        while len(self.player_list) > 1 and self.word is None and timer > 0:  # other events will set self.word
            print("word choosing timer: " + str(timer))
            timer -= 1
            time.sleep(1)
        self.waiting_for_word = False
        if timer == 0:  # finished timer, first word will be chosen
            print("Timer finished, word will be", self.word_options[0])
            self.word = self.word_options[0]
        elif self.word is not None:  # artist chose a word
            print("Artist chose:", self.word)
            if self.word != word_options[0] and self.word != word_options[1] and self.word != word_options[2]:
                # if chose an invalid word somehow
                self.word = self.word_options[0]
                print("Fixing to:", self.word)
        else:  # not enough players
            print("Not enough players")
            self.print_players()
            self.terminate()
            return
        # setting up the entire game's hints
        # there will be (len(self.word) // 3) + 1 regular hints, and an extra one for the 'bought hint'
        self.word = self.word.lower()
        print(self.word, len(self.word))
        self.hints = getRandomNumbers(len(self.word) - 1, (len(self.word) // 3) + 2)
        self.current_overlay = "guessing_view"
        self.reduce_time(0)

    def process_hint_request(self, username, my_type):
        if not self.active or username in self.used_hints or username in self.guessed:
            return
        player = self.get_player_object_by_username(username)
        if player is None:
            return
        json = {'type': "hint_alert", "username": username}
        if my_type == "public":
            if player.score > 150:
                json['hint_type'] = "public"
                player.score -= 150
                for p in self.player_list:
                    if p not in self.used_hints:
                        self.used_hints.append(p.username)
                self.sock.emit('chat_message', json, room=self.room, namespace='/lobby')
                self.send_current_scoreboard()
                self.used_hints.append(username)
                self.send_current_overlay()
        elif my_type == "private":
            if player.score > 350:
                json['hint_type'] = "private"
                player.score -= 350
                self.used_hints.append(username)
                self.sock.emit('chat_message', json, room=self.room, namespace='/lobby')
                self.send_current_scoreboard()
                self.used_hints.append(username)
                self.send_current_overlay()

    def reduce_time(self, seconds):
        if not self.active:
            return
        if self.current_time - seconds <= 0:
            self.current_time = 0
            return
        # the game is still going
        self.current_time -= seconds
        self.send_current_overlay()

    def start_turn(self):
        if not self.active or len(self.player_list) < 2:
            print("finished here")
            self.active = False
            return
        self.sock.emit('chat_message', {'type': 'turn_started', 'artist': self.artist.username}, room=self.room, namespace='/lobby')
        self.send_current_scoreboard()
        self.request_word()
        print("finished requesting words")
        self.add_current_width_instruction()
        self.add_current_color_instruction()
        self.add_current_action_instruction()
        while self.active and len(self.player_list) > 1 and self.current_time > 0 and not self.all_guessed:
            self.reduce_time(1)
            # print("turn timer: " + str(self.current_time))
            time.sleep(1)
        self.current_overlay = "turn_ended"
        points, time_diff = self.add_points_to_player(self.artist)
        if points is not None:
            self.guessed[self.artist.username] = points
        self.send_current_overlay()
        self.sock.emit('chat_message', {'type': 'turn_ended', 'last_word': self.word}, room=self.room, namespace='/lobby')
        time.sleep(5)  # allow for 5 seconds of the end of turn overlay
        self.active = False
        self.terminate()
        return self.return_end_of_game