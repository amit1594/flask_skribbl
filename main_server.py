from flask import Flask, render_template, request, redirect, g, session, url_for
import random
from flask_socketio import SocketIO, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging
from classes.lobby_handler import LobbyHandler
from helpers import get_prohibited_words, get_prohibited_chars
from engineio.payload import Payload
import os
import eventlet

eventlet.monkey_patch()

# configs
Payload.max_decode_packets = 200
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nLzRfxyl8U5JGSh!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.dirname(os.path.realpath(__file__)) + '\\myDB.db'
# logging.getLogger('werkzeug').disabled = True  # disabling logs
# app.logger.disabled = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
lobby_handler = LobbyHandler(socketio, db)
next_guest_num = random.randint(1000, 2000)
players_dict = dict()


class UserTbl(db.Model):
    __tablename__ = 'user_tbl'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50))
    password = db.Column(db.String(80))
    image = db.Column(db.String(80))
    wins = db.Column(db.Integer)
    words_guessed_correctly = db.Column(db.Integer)
    seconds_took_to_guess = db.Column(db.Integer)
    all_guesses = db.Column(db.Integer)
    all_games = db.Column(db.Integer)
    games_winrate = db.Column(db.Float)
    correct_guess_rate = db.Column(db.Float)
    average_time_to_guess_correctly = db.Column(db.Float)


def get_user_by_username(uname):
    """Returns the user from the DB that's username is the one inputted"""
    myUser = UserTbl.query.filter_by(username=uname).first()
    return myUser


def get_restricted_icons():
    win_restricted = {'yellow_diamond': 1, 'blue_diamond': 3, 'orange_diamond': 5, 'green_diamond': 10,
                      'red_diamond': 30, 'black_diamond': 50, 'multi_color_diamond': 100}
    correct_guesses = {'tan_diamond': 10, 'pink_diamond': 30, 'purple_diamond': 50}
    return win_restricted, correct_guesses


def get_icons_for_user(username):
    all_icons = get_all_icons()
    user = get_user_by_username(username)
    if not user:
        return all_icons
    wins = user.wins
    correct_guesses = user.words_guessed_correctly
    win_restricted, correct_guessess_restricted = get_restricted_icons()
    for icon, wins_needed in win_restricted.items():
        if wins_needed <= wins:
            all_icons[icon] = ''
        else:
            break
    for icon, guesses_needed in correct_guessess_restricted.items():
        if guesses_needed <= correct_guesses:
            all_icons[icon] = ''
        else:
            break
    return all_icons


def get_all_icons():
    # all images are saved via png
    """icons = ["anonymous", "cat", "fries", "guitar", "penguin", "pirate", "plane", "plant", "star",
             "tan_diamond", "pink_diamond", "yellow_diamond", "blue_diamond", "purple_diamond",
             "orange_diamond", "green_diamond", "red_diamond", "black_diamond", "multi_color_diamond"]"""
    icon_dict = {'anonymous': '', 'cat': '', 'fries': '', 'guitar': '', 'penguin': '', 'pirate': '', 'plane': '',
                 'plant': '', 'star': '', 'tan_diamond': '10 correct guesses', 'pink_diamond': '30 correct guesses',
                 'yellow_diamond': '1 win', 'blue_diamond': '3 wins', 'purple_diamond': '50 correct guesses',
                 'orange_diamond': '5 wins', 'green_diamond': '10 wins', 'red_diamond': '30 wins',
                 'black_diamond': '50 wins', 'multi_color_diamond': '100 wins'}
    return icon_dict


def get_lobby_player_dict(my_lobby):
    """Returns a dict of the entire lobby by: {username: score, picture}"""
    players = dict()
    for player in my_lobby.player_list:
        players[player.username] = player.score, url_for('static', filename='Images/anonymous.png')
    return players


def get_admin_sid(my_lobby):
    """Return the sid of the admin in a lobby"""
    admin = my_lobby.admin
    for sid in players_dict.keys():
        if players_dict.get(sid)[0] == admin:
            return sid
    print("Could not find admin in room {}".format(my_lobby.lobby_id))
    return None


def send_startable(my_lobby):
    """ Sends to the admin of the lobby if the game may start (if there are atleast 2 players)"""
    if len(my_lobby.player_list) >= 2:
        socketio.emit('allowed_to_start', {'flag': "true"}, room=get_admin_sid(my_lobby), namespace='/lobby')
    else:
        socketio.emit('allowed_to_start', {'flag': "false"}, room=get_admin_sid(my_lobby), namespace='/lobby')


def create_new_room(room, password):
    """If the room's ID doesn't exist already, opens a new room in lobby_handler"""
    if room not in lobby_handler.lobbies:  # new lobby
        if len(password) == 0:
            password = None
        lobby_handler.add_lobby(room, password)


def get_lobbies():
    """Returns a list of all lobbies by: (lobby_id, amount_of_players, lobby_password)"""
    my_rooms = []
    for lobby_id in lobby_handler.lobbies:
        curr_lob = lobby_handler.get_lobby(lobby_id)
        my_rooms.append((lobby_id, len(curr_lob.player_list), curr_lob.started, curr_lob.password is not None))
    return my_rooms


def validate_change_icon(icon, username, sid, my_namespace):
    options = get_icons_for_user(username)
    if options.get(icon, '') == '':
        user = get_user_by_username(username)
        user.image = icon
        db.session.commit()
        socketio.emit('icon_changed', {'icon': icon}, room=sid, namespace=my_namespace)
    else:
        print('icon denied')


@app.before_request
def before_request():
    """g.user = None
    if 'username' in session:
        user = get_user_by_username(session['username'])
        g.user = user"""
    global next_guest_num
    if 'username' not in session:
        session['username'] = "Guest" + str(next_guest_num)
        next_guest_num += random.randint(1, 5)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method != 'POST':  # form not submitted
        return render_template('login.html')
    session.pop('username', None)
    username = request.form.get('username')
    password = request.form.get('password')
    print("Login attempt: {} | {}".format(username, password))
    user = get_user_by_username(username)
    if user and user.password == password:
        session['username'] = username
        g.user = user
        return redirect(url_for('main_page'))
    return render_template('login.html', cred_error="Credentials incorrect")


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method != 'POST':  # form not submitted
        return render_template('register.html')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    prohibited_chars = get_prohibited_chars()
    for c in prohibited_chars:
        if c in username:
            return render_template('register.html', alert="char", not_allowed=c, username=username, email=email)
    prohibited_words = get_prohibited_words()
    for word in prohibited_words:
        if word in username:
            return render_template('register.html', alert="word", not_allowed=word, username=username, email=email)
    user = get_user_by_username(username)
    # do not allow usernames: 'type', 'username', 'word', 'artist', 'Guest + num'
    if user:
        return render_template('register.html', alert="taken", username=username, email=email)
    new_user = UserTbl(username=username, email=email, image="anonymous",
                       wins=0, words_guessed_correctly=0, seconds_took_to_guess=0, all_guesses=0, all_games=0,
                       games_winrate=0, correct_guess_rate=0, average_time_to_guess_correctly=0)
    db.session.add(new_user)
    db.session.commit()
    session['username'] = new_user.username
    g.user = user
    return redirect(url_for('main_page'))


@app.route('/update_user_info', methods=['POST', 'GET'])
def update_user_info():
    username = session['username']
    user = get_user_by_username(username)
    if not user:
        return render_template('no_guests_allowed.html')
    if request.method != 'POST':  # form not submitted
        return render_template('update_user_info.html', username=username, email=user.email,
                               image=user.image, my_icons=get_icons_for_user(username))
    attempted_username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    prohibited_chars = get_prohibited_chars()
    for c in prohibited_chars:
        if c in attempted_username:
            return render_template('update_user_info.html', alert="char", not_allowed=c, username=attempted_username, email=email,
                                   image=user.image, my_icons=get_icons_for_user(username))
    prohibited_words = get_prohibited_words()
    for word in prohibited_words:
        if word in attempted_username:
            return render_template('update_user_info.html', alert="word", not_allowed=word, username=attempted_username, email=email,
                                   image=user.image, my_icons=get_icons_for_user(username))
    existing_user = get_user_by_username(attempted_username)
    if username != attempted_username and existing_user:
        return render_template('update_user_info.html', alert="taken", username=attempted_username, email=email,
                               image=user.image, my_icons=get_icons_for_user(username))

    user.username = attempted_username
    user.password = password
    user.email = email
    db.session.commit()
    session['username'] = attempted_username
    g.user = user
    return redirect(url_for('main_page'))


@socketio.on('request_icon_change', namespace='/update_user_info')
def handle_icon_change_from_update_user_info(json):
    username = session['username']
    icon = json.get('icon', None)
    validate_change_icon(icon, username, request.sid, '/update_user_info')


@app.route('/main', methods=['POST', 'GET'])
def main_page():
    username = session['username']
    user = get_user_by_username(username)
    if request.method == 'POST':  # requesting to join/create a lobby
        op = request.form.get('op')
        room = request.form.get('room_id')
        room_password = request.form.get('room_password')
        if op == "create":  # creating a new room
            if room not in lobby_handler.lobbies:
                create_new_room(room, room_password)
                session['room'] = room
                session['room_password'] = room_password
                return redirect(url_for('lobby'))
            else:  # lobby id already exists
                return render_template('main.html', my_icons=get_icons_for_user(username), rooms=get_lobbies(), prev_id=room,
                                       prev_pass=room_password, alert="create", guest=user is None)
        elif op == "join":  # joining a room
            actual_pass = lobby_handler.get_lobby(room).password
            # print("Real pass is '{}', got pass '{}'". format(actual_pass, room_password))
            if actual_pass is None or actual_pass == room_password:
                session['room'] = room
                session['room_password'] = room_password
                return redirect(url_for('lobby'))
            else:  # incorrect password
                return render_template('main.html', my_icons=get_icons_for_user(username), rooms=get_lobbies(), prev_id=room,
                                       prev_pass=room_password, alert="join", guest=user is None)
    else:  # regular main view
        """if not g.user:  # not logged
            return redirect(url_for('login'))"""
        if user:
            return render_template('main.html', my_icons=get_icons_for_user(username), rooms=get_lobbies(),
                                   image=user.image, guest=user is None)
        else:
            return render_template('main.html', my_icons=get_icons_for_user(username), rooms=get_lobbies(),
                                   image="anonymous", guest=user is None)


@socketio.on('request_icon_change', namespace='/main_page')
def handle_icon_change_from_main_page(json):
    username = session['username']
    icon = json.get('icon', None)
    validate_change_icon(icon, username, request.sid, '/main_page')


@socketio.on('get_all_lobbies', namespace='/main_page')
def get_all_lobbies():
    my_dict = dict()
    for lob_id in lobby_handler.lobbies.keys():
        my_lobby = lobby_handler.get_lobby(lob_id)
        my_dict[lob_id] = (len(my_lobby.player_list), my_lobby.started, my_lobby.password is not None)
    socketio.emit('update_lobbies_list', my_dict, namespace='/main_page')
    # print("send all lobies, ", my_dict)


@app.route('/lobby', methods=['POST', 'GET'])
def lobby():
    """if not g.user:
        return redirect(url_for('login'))"""
    if 'room' not in session or 'room_password' not in session:
        return redirect(url_for('main_page'))
    room = session['room']
    room_password = session['room_password']
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby or this_lobby.is_full():
        return redirect(url_for('main_page'))
    # print(room, room_password)
    actual_pass = this_lobby.password
    if actual_pass is None or actual_pass == room_password:
        return render_template('lobby.html', room=room, room_pass=room_password,
                               players=["test1", "test2", "test3"])
    else:
        return redirect(url_for('main_page'))


@socketio.on('requestEntireDrawing', namespace='/lobby')
def request_entire_drawing():
    room = session['room']
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.send_entire_drawing(request.sid)


@socketio.on('new_stroke', namespace='/lobby')
def handle_new_stroke(json):
    room = session['room']
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    print("got stroke")
    this_lobby.add_stroke(json, username)


@socketio.on('artist_chose_word', namespace='/lobby')
def handle_artist_choice(json):
    print("Received artists word")
    room = session['room']
    chosen = json.get('chosen_word')
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.set_turn_word(chosen, username)


@socketio.on('request_hint', namespace='/lobby')
def handle_hint_request(json):
    room = session['room']
    username = session['username']
    hint_type = json.get('type')
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.process_hint_request(username, hint_type)


@socketio.on('player_join', namespace='/lobby')
def handle_join():
    room = session['room']
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    room_pass = session['room_password']
    if this_lobby.password is not None and this_lobby.password != room_pass:
        redirect(url_for('main_page'))
    join_room(room, namespace='/lobby')
    user = get_user_by_username(session['username'])
    this_lobby.add_player(username, request.sid, user)
    players_dict[request.sid] = (username, room)
    # send scoreboard
    if username == this_lobby.admin:
        socketio.emit('admin_update', {'admin': username}, room=room, namespace='/lobby')
    send_startable(this_lobby)
    get_all_lobbies()


@socketio.on('disconnect', namespace='/lobby')
def lobby_disconnect():
    if players_dict.get(request.sid) is None:
        print("ended here")
        return
    username, room = players_dict.get(request.sid)
    players_dict.pop(request.sid)
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.remove_player(username)
    if len(this_lobby.player_list) < 1:  # was last in lobby
        lobby_handler.remove_lobby(room)
        print('closed room {}'.format(room))
    else:  # more left in the lobby
        socketio.emit('admin_update', {'admin': this_lobby.admin}, room=room, namespace='/lobby')
        send_startable(this_lobby)
        print("Disconnected {}".format(username))
    leave_room(room)
    get_all_lobbies()
    session.pop('room', None)
    session.pop('room_password', None)


@socketio.on("test_stroke", namespace='/lobby')
def test_arr(json):
    room = session['room']
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.test_stroke(json, username)


@socketio.on('request_game_start', namespace='/lobby')
def start_game():
    room = session['room']
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    print("Lobby '{}', user '{}', requested game start".format(room, username))
    if not this_lobby:
        return
    if this_lobby.admin == username and len(this_lobby.player_list) > 1:  # validating
        # this_lobby.start_game()
        for player in this_lobby.player_list:
            print("scanning " + player.username)
            user = get_user_by_username(player.username)
            if user:
                print("added a game to " + player.username)
                user.all_games += 1
                user.games_winrate = round((user.wins / (user.all_games + 1)) * 100, 1)
        db.session.commit()
        socketio.start_background_task(this_lobby.start_game())
        get_all_lobbies()
        winner = this_lobby.winner
        if winner:
            user = get_user_by_username(winner)
            if user:
                user.wins += 1
                user.games_winrate = round(((user.wins + 1) / user.all_games) * 100, 1)
        db.session.commit()


@socketio.on('update_lobby_settings', namespace='/lobby')
def update_lobby_settings(json):
    room = session['room']
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    print("Lobby '{}', user '{}', requested game start".format(room, username))
    if not this_lobby:
        return
    try:
        if this_lobby.admin == username:  # validating that the admin sent it
            custom_words = json.get('custom_words').split(",")
            this_lobby.update_settings(json.get('language'), int(json.get('draw_time')), int(json.get('rounds')),
                                       json.get('gamemode'), int(json.get('points_limit')), json.get('difficulty'),
                                       custom_words)
    except ValueError:
        print("Value error")
        print(json.get('language'), json.get('draw_time'), json.get('rounds'), json.get('custom_words').split(","))
        this_lobby.emit_settings()


@socketio.on('request_color_change', namespace='/lobby')
def request_color_change(json):
    room = session['room']
    username = session['username']
    color = json.get('color')
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.request_color_change(username, color)


@socketio.on('request_width_change', namespace='/lobby')
def request_color_change(json):
    room = session['room']
    username = session['username']
    width = json.get('width')
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.request_width_change(username, width)


@socketio.on('request_action_change', namespace='/lobby')
def request_action_change(json):
    room = session['room']
    username = session['username']
    action = json.get('action')
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    this_lobby.request_action_change(username, action)


@socketio.on('client_instruction', namespace='/lobby')
def process_client_instruction(json):
    room = session['room']
    username = session['username']
    this_lobby = lobby_handler.get_lobby(room)
    if this_lobby:
        this_lobby.process_instruction(json, username)


@socketio.on('new_chat_message', namespace='/lobby')
def new_chat_message_handler(json):
    room = session['room']
    username = session['username']
    msg = json.get('message')
    if msg == "win":
        print(db, db.session)
        user = get_user_by_username("amit123")
        print(user)
        user.wins += 1
        db.session.commit()
    print("Got message")
    this_lobby = lobby_handler.get_lobby(room)
    if not this_lobby:
        return
    is_a_guess, points, time_diff = this_lobby.new_chat_message(username, msg)
    if not is_a_guess:
        return
    user = get_user_by_username(session['username'])
    if user:
        if points is not None:
            user.words_guessed_correctly += 1
            user.seconds_took_to_guess += time_diff
            user.average_time_to_guess_correctly = round(((user.seconds_took_to_guess + time_diff) / (user.words_guessed_correctly + 1)), 1)
        user.correct_guess_rate = round(((user.words_guessed_correctly + 1) / (user.all_guesses + 1)) * 100, 1)
        user.all_guesses += 1
        db.session.commit()


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session['username']
    user = get_user_by_username(username)
    if not user:
        return render_template('no_guests_allowed.html')
    wins = user.wins
    amount_of_correct_guesses = user.words_guessed_correctly
    seconds_took_to_guess = user.seconds_took_to_guess
    amount_of_guesses = user.all_guesses
    amount_of_games = user.all_games
    games_winrate = user.games_winrate
    correct_guess_rate = user.correct_guess_rate
    avg_time_to_guess_correctly = user.average_time_to_guess_correctly
    #sql = text('SELECT * from user_tbl WHERE user_tbl.book_price > 100')
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.all_games > ' + str(amount_of_games))
    place_by_games_played = db.engine.execute(sql).fetchall()[0][0] + 1
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.wins > ' + str(wins))
    place_by_games_won = db.engine.execute(sql).fetchall()[0][0] + 1
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.all_games >= 5 AND user_tbl.games_winrate > ' + str(games_winrate))
    place_by_winrate = db.engine.execute(sql).fetchall()[0][0] + 1
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.all_guesses > ' + str(amount_of_guesses))
    place_by_amount_of_guesses = db.engine.execute(sql).fetchall()[0][0] + 1
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.words_guessed_correctly > ' + str(amount_of_correct_guesses))
    place_by_amount_of_correct_guesses = db.engine.execute(sql).fetchall()[0][0] + 1
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.all_guesses >= 5 AND user_tbl.correct_guess_rate > ' + str(correct_guess_rate))
    place_by_correct_guess_rate = db.engine.execute(sql).fetchall()[0][0] + 1
    sql = text('SELECT COUNT(user_tbl.id) FROM user_tbl WHERE user_tbl.all_guesses >= 5 AND user_tbl.average_time_to_guess_correctly > ' + str(avg_time_to_guess_correctly))
    place_by_average_seconds_per_correct_guess = db.engine.execute(sql).fetchall()[0][0] + 1
    return render_template('profile.html', amount_of_games_played=amount_of_games, place_by_games_played=place_by_games_played,
                           games_won=wins, place_by_games_won=place_by_games_won, games_winrate=games_winrate,
                           place_by_winrate=place_by_winrate, amount_of_guesses=amount_of_guesses, place_by_amount_of_guesses=place_by_amount_of_guesses,
                           amount_of_correct_guesses=amount_of_correct_guesses, place_by_amount_of_correct_guesses=place_by_amount_of_correct_guesses,
                           correct_guess_rate=correct_guess_rate, place_by_correct_guess_rate=place_by_correct_guess_rate,
                           seconds_took_to_guess=seconds_took_to_guess, seconds_for_correct_guess=avg_time_to_guess_correctly,
                           place_by_average_seconds_per_correct_guess=place_by_average_seconds_per_correct_guess,
                           username=username, image=user.image)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('main_page'))


if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0", port=80)
