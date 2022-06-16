from classes.player import Player
from helpers import get_color_by_name, player_list_to_dict, sort_player_dict
from helpers import validate_width, validate_color, getRandomNumbers, is_valid_text
import eventlet
import time
import os
eventlet.monkey_patch()


class Turn:
    """
        A class that represents a turn of a game.

        ...

        Attributes
        ----------
        artist : Player
            Player object of the artist
        active : bool
            bool to represent if the turn is going on
        player_list : list of Players
            list containing all the Player objects in the game
        max_time : int
            maximum time a turn can take
        current_time : int
            time left until the turn finishes
        language : str
            name of the language the game is playing with
        room : str
            id of room
        total_rounds : int
            amount of rounds to finish an entire game (not a turn)
        current_round : str
            the number of current round playing
        custom_words : list of str
            list of words that are added to the language's list to play with
        sock : Socket
            the socket the game is playing over
        gamemode : str
            the game type, either Classic or Points_Rush
        points_limit : int
            If the gamemode is Points_Rush - this is the maximum points to reach before winning
        difficulty : str
            the difficulty of the game, either Normal or Difficult
        word_options : tuple of strings
            a tuple of the 3 words the artist can choose from
        word : str
            the word the artist is drawing
        waiting_for_word : bool
            True if the artist is choosing a word, else False
        all_guessed : bool
            True if everyone guessed correctly, else False
        guessed : dict {username: points_received}
            a dict with every correct guessed as key and the points he received as value
        used_hints : list of int
            list of the indexes at which the hints will be, the last one is reserved for a bought hint.
        current_overlay : str
            the overlay the turn is currently seeing
        return_end_of_game : bool
            True if the gamemode is Points_Rush and a player exceeded the maximum points, else False.
        color : str
            the current color the artist is drawing with
        width : list of int
            the current width of pen the artist is drawing with
        action : str
            the action the artist is doing, either pen or fill
        instructions : list of dicts
            list of all drawing instructions

        Methods
        -------
        terminate():
            turns self.active to False
        send_current_overlay():
            sends to every player the overlay he should see currently
        send_current_scoreboard():
            sends to everyone the current scoreboard
        get_player_object_by_username(username):
            returns the player object of the player with this username, if doesn't exist returns None
        remove_player(username):
            removes the corresponding player from the game
        did_all_guess():
            returns true if everyone (except the artist) guessed correctly
        char_difference(msg):
            returns the amount of chars in msg that are different from self.word
        add_points_to_player(player):
            calculates and adds the points to the player
        new_chat_message(username, message):
            processes a chat message
        add_current_width_instruction():
            appends to self.instructions the current width
        add_current_color_instruction():
            appends to self.instructions the current color
        add_current_action_instruction():
            appends to self.instructions the current action
        send_all_instructions(room):
            sends all of the instructions to the given room (of socket)
        send_entire_drawing(room):
            sends a 'clear' instruction, then sends all of the instructions to the given room
        process_instruction(inst, username):
            processes a given instructions and send to all guessers accordingly
        request_color_change(username, color):
            if the requester is the artist, changes the current color and sends to all that the color has changed.
        request_width_change(username, width):
            if the requester is the artist, changes the current width and sends to all that the width has changed.
        request_action_change(username, action):
            if the requester is the artist, changes the current action and sends to all that the action has changed.
        player_joined(player):
            handles player join
        generate_words():
            generates 3 random words from the language's list and the custom words
        get_encoded_word(is_artist, bought_hint):
            returns the appropriate 'word display', based of hints.
        set_word(word, username):
            if the username is the artist and self.waiting_for_word, sets the word.
        print_players():
            prints the list of players
        send_to_all(event_name, json):
            sends the appropriate event + json to self.room
        send_to_all_except_artist(event_name, json):
            sends the appropriate event + json to everyone except the artist
        send_to_artist(event_name, json):
            sends the appropriate event + json to the artist
        request_word():
            begins the wait for the artist to choose a word
        process_hint_request(username, my_type):
            processes the hint request

        reduce_time(seconds):
            reduces the given time from self.current_time
        start_turn():
            starts the turn
    """

    def __init__(self, artist, player_list, max_time, language, room, total_rounds, current_round, custom_words, sock,
                 gamemode, points_limit, difficulty):
        self.total_rounds = total_rounds
        self.current_round = current_round
        self.active = True
        self.artist = artist
        self.player_list = player_list
        self.max_turn_time = max_time
        self.current_time = max_time
        self.language = language
        self.word_options = ()
        self.word = None
        self.waiting_for_word = False
        self.room = room
        self.all_guessed = False
        self.guessed = dict()
        self.used_hints = []
        self.hints = []
        self.current_overlay = ""
        self.gamemode = gamemode
        self.difficulty = difficulty
        self.custom_words = custom_words
        self.sock = sock
        self.points_limit = points_limit
        self.return_end_of_game = False
        self.color = get_color_by_name('black')
        self.width = 2
        self.action = 'pen'
        self.instructions = []

    def terminate(self):
        """ Terminates the turn """
        self.active = False

    def send_current_overlay(self):
        """ Sends to every player the overlay he should see currently """
        for p in self.player_list:
            if self.current_overlay == "" or self.current_overlay == "lobby":  # if the overlay is lobby
                self.sock.emit('game_overlay', {'type': 'lobby'}, room=p.sid, namespace='/lobby')
            elif self.current_overlay == "artist_choosing_a_word":  # if the overlay is artist_choosing_a_word
                if p.username == self.artist.username:
                    json = {'type': "word_to_choose_from", 'current_round': self.current_round,
                            'total_rounds': self.total_rounds, 'w1': self.word_options[0],
                            'w2': self.word_options[1], 'w3': self.word_options[2], 'gamemode': self.gamemode}
                else:
                    json = {'type': self.current_overlay, 'artist': self.artist.username, 'gamemode': self.gamemode,
                            'current_round': self.current_round, 'total_rounds': self.total_rounds}
                self.sock.emit('game_overlay', json, room=p.sid, namespace='/lobby')
            elif self.current_overlay == "guessing_view":  # if the overlay is guessing_view
                json = {'time': self.current_time}
                if p.username == self.artist.username:  # the artist should see an artist_view
                    json['type'] = 'artist_view'
                    json['word'] = self.get_encoded_word(True, True)
                elif p.username in self.used_hints:  # different for if the player used a hint
                    json['type'] = self.current_overlay
                    json['encoded_word'] = self.get_encoded_word(False, True)
                    json['need_hint_box'] = False
                else:  # did not use a hint
                    json['type'] = self.current_overlay
                    json['encoded_word'] = self.get_encoded_word(False, False)
                    json['need_hint_box'] = True
                self.sock.emit('game_overlay', json, room=p.sid, namespace='/lobby')
            elif self.current_overlay == "turn_ended":  # if the overlay is turn_ended
                my_dict = self.guessed
                my_dict['type'] = 'turn_ended'
                self.sock.emit('game_overlay', my_dict, room=self.room, namespace='/lobby')

    def send_current_scoreboard(self):
        """ Sends the current scoreboard to everyone """
        if not self.active:
            return
        my_dict = sort_player_dict(player_list_to_dict(self.player_list, True, True))
        self.sock.emit('update_scoreboard', my_dict, room=self.room, namespace='/lobby')

    def get_player_object_by_username(self, username):
        """ Returns the respective player object by the username or None if username doesn't exist """
        if not self.active:
            return None
        for player in self.player_list:
            if player.username == username:
                return player
        return None

    def remove_player(self, username):
        """ Removes player from self.guessed and sends the new scoreboard.
            Note: the player_list updates automatically, so this method does not change it """
        if not self.active:
            return
        self.guessed.pop(username, None)  # None used to not throw exception if username doesnt exist in dict
        self.sock.emit('chat_message', {'type': 'left_alert', 'username': username}, room=self.room, namespace='/lobby')
        self.send_current_scoreboard()
        if username == self.artist.username or len(self.player_list) < 2:  # terminate if artist left
            self.terminate()

    def did_all_guess(self):
        """ Returns true if everyone (except the artist) guessed correctly """
        if not self.active:
            return False
        for player in self.player_list:
            if player.username != self.artist.username and player.username not in self.guessed.keys():
                return False
        return True

    def char_difference(self, msg):
        """ Returns the amount of char the given text is different from self.word """
        if not self.active or not self.word:
            return len(self.word)
        if len(msg) != len(self.word):
            return len(self.word)
        counter = 0
        for index in range(len(self.word)):
            if self.word[index].upper() != msg[index].upper():  # we don't care about upper/lower case
                counter += 1
        return counter

    def add_points_to_player(self, player):
        """ Adds the appropriate amount of points to the given player """
        if not self.active or self.word is None or player not in self.player_list:
            return 0, 0
        points_received = 0
        time_diff = self.max_turn_time - self.current_time
        if player.username == self.artist.username:  # if artist
            if len(self.guessed) == 0:
                self.artist.add_points(0)
                return 0, 0
            points_received = (50 * len(self.guessed)) - time_diff + 20 * len(self.word)  # calc for artist
            points_received = max(points_received, 0)
            self.artist.add_points(points_received)
        else:
            points_received = int(1000 - (5 * time_diff) - 50 * len(self.guessed) + 10 * len(self.word))  # calc for guesser
            player.add_points(points_received)
        self.send_current_scoreboard()  # sending the new scoreboard
        if self.gamemode == "Points_Rush" and player.score > self.points_limit:  # if went over the points limit in Points_Rush
            self.terminate()
            self.return_end_of_game = True
            return
        print("Gave", player.username, points_received, "Points")
        return points_received, time_diff

    def new_chat_message(self, username, message):
        """ Processes a  chat message. Returns:  is_a_guess, points_received, time_diff """
        if not self.active:
            return False, None, None
        player = self.get_player_object_by_username(username)
        if not player:  # unrecognized username
            return True, None, None
        if not is_valid_text(message):  # language filter
            self.sock.emit('chat_message', {'username': username, 'message': '', 'type': 'prohibited'},
                           room=player.sid, namespace='/lobby')
            return True, None, None
        json = {'username': username, 'message': message}
        if not self.word:  # if while word choosing
            if username == self.artist.username:
                json['type'] = "guessed_chat"
                self.send_to_artist('chat_message', json)  # he should also see the message
            else:  # not the artist
                json['type'] = "regular"
                self.send_to_all('chat_message', json)
            return False, None, None
        # this is assuming the word is chosen
        if username in self.guessed.keys() or username == self.artist.username:  # if guessed correctly before
            json['type'] = "guessed_chat"
            for tempP in self.player_list:  # send to everyone who already guessed
                if tempP.username in self.guessed.keys():
                    self.sock.emit('chat_message', json, room=tempP.sid, namespace='/lobby')
            self.send_to_artist('chat_message', json)  # he should also see the message
            return False, None, None
        elif message.upper() == self.word.upper():  # correct guess
            result = self.add_points_to_player(player)
            if not result:
                return False, None, None
            points, time_diff = self.add_points_to_player(player)
            if points is not None:
                self.guessed[username] = points
            self.reduce_time(self.current_time // 3)  # reduce the time
            self.all_guessed = self.did_all_guess()  # check if everyone guessed
            self.sock.emit('chat_message', {'username': username, 'type': 'correct'}, room=self.room, namespace='/lobby')
            return True, points, time_diff
        else:  # incorrect guess
            for tempP in self.player_list:
                if tempP.username == username and self.char_difference(message) == 1:  # almost correct
                    json['type'] = "almost_correct"
                    self.sock.emit('chat_message', json, room=tempP.sid, namespace='/lobby')
                else:  # every one else sees it as a regular message
                    json['type'] = "regular"
                    self.sock.emit('chat_message', json, room=tempP.sid, namespace='/lobby')
        return True, None, None

    def add_current_width_instruction(self):
        """ Adds an instruction with the current width and sends it to all """
        inst = {'inst_type': 'change_width', 'width': self.width}
        self.instructions.append(inst)
        self.send_to_all('new_instruction', inst)

    def add_current_color_instruction(self):
        """ Adds an instruction with the current color and sends it to all """
        inst = {'inst_type': 'change_color', 'color': self.color}
        self.instructions.append(inst)
        self.send_to_all('new_instruction', inst)

    def add_current_action_instruction(self):
        """ Adds an instruction with the current action and sends it to all """
        inst = {'inst_type': 'change_action', 'action': self.action}
        self.instructions.append(inst)
        self.send_to_all('new_instruction', inst)

    def send_all_instructions(self, room):
        """ Sends every instruction to everyone inside the given room """
        for inst in self.instructions:
            self.sock.emit('new_instruction', inst, room=room, namespace='/lobby')

    def send_entire_drawing(self, room):
        """ Sends 'clear' instruction, and then every instruction to everyone inside the given room """
        self.sock.emit('new_instruction', {'inst_type': 'clear'}, room=room, namespace='/lobby')
        self.send_all_instructions(room)

    def process_instruction(self, inst, username):
        """ Processes an instruction """
        if not self.active or username != self.artist.username or 'inst_type' not in inst:
            return
        inst_type = inst.get('inst_type', None)
        print(inst)
        if inst_type == "clear":
            self.send_to_all('new_instruction', {'inst_type': 'clear'})
            self.instructions = []
            self.add_current_width_instruction()
            self.add_current_color_instruction()
            self.add_current_action_instruction()
        elif inst_type == "undo":
            index = len(self.instructions) - 1
            for i in self.instructions[::-1]:  # search from the last backwards
                curr_type = self.instructions[index].get('inst_type')
                if curr_type == "stroke" or curr_type == "fill":  # if is a stroke or a fill instruction
                    self.instructions.pop(index)  # remove it
                    self.send_entire_drawing(self.room)
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
                self.color = get_color_by_name(color)  # get the rgb
                self.add_current_color_instruction()
        elif inst_type == "change_action":
            action = inst.get('action', 'pen')
            if action in ['pen', 'fill']:
                self.action = action
                self.add_current_action_instruction()

    def request_color_change(self, username, color):
        """ Changes the color if the requester is the artist """
        if not self.active or username != self.artist.username or not validate_color(color):
            return
        self.color = get_color_by_name(color)
        self.add_current_color_instruction()
        self.send_to_all('color_changed', {'draw_color': self.color})

    def request_width_change(self, username, width):
        """ Changes the width if the requester is the artist """
        if not self.active or username != self.artist.username or not validate_width(width):
            return
        self.width = int(width)  # validate_width made sure its possible!
        self.add_current_width_instruction()
        self.send_to_all('width_changed', {'width': self.width})

    def request_action_change(self, username, action):
        """ Changes the action if the requester is the artist """
        if not self.active or username != self.artist.username or action not in ['pen', 'fill']:
            return
        self.action = action
        self.add_current_action_instruction()
        self.send_to_all('action_changed', {'action': self.action})

    def player_joined(self, player):
        """ Sends the new scoreboard to all and sends all previous strokes to the new player """
        if not self.active:
            return
        self.send_current_overlay()
        self.sock.emit('chat_message', {'type': 'join_alert', 'username': player.username}, room=self.room, namespace='/lobby')
        self.send_current_scoreboard()
        self.send_all_instructions(player.sid)

    def generate_words(self):
        """ Generates 3 words from the specified language (will be English if incorrect language) and custom words """
        path = os.path.dirname(os.path.realpath(__file__))
        how_many_to_skip = 0
        for c in path[::-1]:
            if c.isalpha():
                how_many_to_skip += 1
            else:
                break
        path = path[:-how_many_to_skip]  # removes the '\\classes'
        if self.language == "Hebrew":
            path += "static\\words\\hebrew.txt"
        elif self.language == "Italian":
            path += "static\\words\\italian.txt"
        elif self.language == "Dutch":
            path += "static\\words\\dutch.txt"
        elif self.language == "French":
            path += "static\\words\\french.txt"
        elif self.language == "German":
            path += "static\\words\\german.txt"
        else:
            path += "static\\words\\english.txt"
        with open(path, 'rb') as f:
            text_lst = f.read().decode(errors='replace').split()
        for word in self.custom_words:  # adds the custom words
            if word not in text_lst:
                text_lst.append(word)
        indexes = getRandomNumbers(len(text_lst) - 1, 3)
        return text_lst[indexes[0]], text_lst[indexes[1]], text_lst[indexes[2]]

    def get_encoded_word(self, is_artist, bought_hint):
        """ Returns the word, with '_' instead of some letters, according to the given parameters """
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
        if self.difficulty == "Normal":  # giving the correct place in the word for the hint
            for index in range(len(self.word)):
                if index in curr_hints:
                    encoded_word.append(ord(self.word[index]))
                else:
                    encoded_word.append(ord("_"))
                if index < len(self.word) - 1:  # if not last char
                    encoded_word.append(ord(" "))
        elif self.difficulty == "Difficult":  # the entire word is replace with '_' and then adds the hints afterwards
            for index in range(len(self.word)):
                encoded_word.append(ord("_"))
                if index < len(self.word) - 1:  # if not last char
                    encoded_word.append(ord(" "))
            for i in "     ":  # a bit of space between the word and the hints
                encoded_word.append(ord(i))
            for index in range(len(curr_hints)):
                encoded_word.append(ord(self.word[curr_hints[index]]))
                if index < len(self.word) - 1:  # if not last char
                    for i in ", ":
                        encoded_word.append(ord(i))
        return encoded_word

    def set_word(self, word, username):
        """ Sets the word """
        if self.active and self.waiting_for_word and username == self.artist.username:
            self.word = word

    def print_players(self):
        """ Prints the username of every player in the lobby """
        for p in self.player_list:
            print(p.username)

    def send_to_all(self, event_name, json):
        """ Sends the event_name + json to every one in the room """
        self.sock.emit(event_name, json, room=self.room, namespace='/lobby')

    def send_to_all_except_artist(self, event_name, json):
        """ Sends the event_name + json to every one in the room except the artist """
        for p in self.player_list:
            if p.username != self.artist.username:
                self.sock.emit(event_name, json, room=p.sid, namespace='/lobby')

    def send_to_artist(self, event_name, json):
        """ Sends the event_name + json to the artist """
        self.sock.emit(event_name, json, room=self.artist.sid, namespace='/lobby')

    def request_word(self):
        """ Request the artist to choose a word out of 3, setups overlay as needed """
        print("start requestion words")
        word_options = self.generate_words()
        self.word_options = word_options
        self.current_overlay = "artist_choosing_a_word"
        self.send_current_overlay()
        timer = 15  # 15 seconds to decide on a word, else will the first one is chosen
        self.waiting_for_word = True
        while len(self.player_list) > 1 and self.word is None and timer > 0:  # other events will set self.word
            timer -= 1
            time.sleep(1)
        self.waiting_for_word = False
        if timer == 0:  # finished timer, first word is chosen
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
        self.hints = getRandomNumbers(len(self.word) - 1, (len(self.word) // 3) + 2)
        self.current_overlay = "guessing_view"
        self.reduce_time(0)

    def process_hint_request(self, username, my_type):
        """ Processes the hint request """
        if not self.active or username in self.used_hints or username in self.guessed:
            return
        player = self.get_player_object_by_username(username)
        if player is None:
            return
        json = {'type': "hint_alert", "username": username}
        if my_type == "public":  # if bought for everyone
            if player.score > 150:
                json['hint_type'] = "public"
                player.score -= 150  # the cost is 150 points
                for p in self.player_list:
                    if p not in self.used_hints:
                        self.used_hints.append(p.username)
                self.sock.emit('chat_message', json, room=self.room, namespace='/lobby')
                self.send_current_scoreboard()
                self.send_current_overlay()
        elif my_type == "private":
            if player.score > 350:
                json['hint_type'] = "private"
                player.score -= 350  # the cost is 350 points
                self.used_hints.append(username)
                self.sock.emit('chat_message', json, room=self.room, namespace='/lobby')
                self.send_current_scoreboard()
                self.send_current_overlay()

    def reduce_time(self, seconds):
        """ Reduce the self.current_time by the given amount """
        if not self.active:
            return
        if self.current_time - seconds <= 0:
            self.current_time = 0
            return
        # the game is still going
        self.current_time -= seconds
        self.send_current_overlay()

    def start_turn(self):
        """ Starting the turn """
        if not self.active or len(self.player_list) < 2:
            self.active = False
            return
        self.sock.emit('chat_message', {'type': 'turn_started', 'artist': self.artist.username}, room=self.room, namespace='/lobby')
        self.send_current_scoreboard()
        self.request_word()  # waiting for a word to be chosen
        # setup instructions
        self.add_current_width_instruction()
        self.add_current_color_instruction()
        self.add_current_action_instruction()
        # the actual playing (drawing - guessing)
        while self.active and len(self.player_list) > 1 and self.current_time > 0 and not self.all_guessed:
            self.reduce_time(1)
            time.sleep(1)
        self.current_overlay = "turn_ended"
        points, time_diff = self.add_points_to_player(self.artist)  # adding points to the artist at the end of the turn
        if points is not None:
            self.guessed[self.artist.username] = points
        if len(self.player_list) > 1:  # will show turn_ended only if there are at least 2 players
            self.send_current_overlay()
            self.sock.emit('chat_message', {'type': 'turn_ended', 'last_word': self.word}, room=self.room, namespace='/lobby')
            time.sleep(5)  # allow for 5 seconds of the 'end of turn' overlay
        self.terminate()
        return self.return_end_of_game  # return whether the entire game should end (for Points_Rush)
