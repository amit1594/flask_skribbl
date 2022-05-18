from flask import Flask, render_template, request, redirect, g, session, url_for, render_template_string
from flask_session import Session
from flask_socketio import SocketIO, join_room, rooms, leave_room
from flask_sqlalchemy import SQLAlchemy
import redis
import logging
from my_classes import LobbyHandler, Lobby, Player
from engineio.payload import Payload

# configs
Payload.max_decode_packets = 100
app = Flask(__name__)
# app.secret_key = 'nLzRfxyl8U5JGSh!'
app.config['SECRET_KEY'] = 'nLzRfxyl8U5JGSh!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///F:\\Computer_Science\\ALL_FLASK\\flask_skribbl\\myDB.db'
logging.getLogger('werkzeug').disabled = True  # disabling logs
app.logger.disabled = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
# sess = Session()
# sess.init_app(app)
lobby_handler = LobbyHandler(socketio)
next_guest_num = 1000
players_dict = dict()


@app.route('/set_email', methods=['GET', 'POST'])
def set_email():
    if request.method == 'POST':
        # Save the form data to the session object
        session['email'] = request.form['email_address']
        return redirect(url_for('get_email'))

    return """
        <form method="post">
            <label for="email">Enter your email address:</label>
            <input type="email" id="email" name="email_address" required />
            <button type="submit">Submit</button
        </form>
        """


@app.route('/get_email')
def get_email():
    return render_template_string("""
            {% if session['email'] %}
                <h1>Welcome {{ session['email'] }}!</h1>
            {% else %}
                <h1>Welcome! Please enter your email <a href="{{ url_for('set_email') }}">here.</a></h1>
            {% endif %}
        """)


@app.route('/delete_email')
def delete_email():
    # Clear the email stored in the session object
    session.pop('email', default=None)
    return '<h1>Session deleted!</h1>'


if __name__ == '__main__':
    # socketio.init_app(app, cors_allowed_origins="*")
    socketio.run(app, debug=True)
