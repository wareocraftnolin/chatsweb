from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, join_room, emit
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

# Dummy user data (replace with your actual user data)
users = {
    'user1': 'password1',
    'user2': 'password2'
}

# Dictionary to store room IDs for each pair of users
# This is just a simple example. You may need a more sophisticated way to manage rooms.
user_rooms = {}

# Dictionary to store messages for each room
message_storage = {}

def is_logged_in():
    return 'username' in session

def validate_login(username, password):
    return username in users and users[username] == password

# Function to store a message for a specific room
def store_message_for_room(room_id, message):
    if room_id in message_storage:
        message_storage[room_id].append(message)
    else:
        message_storage[room_id] = [message]

@app.route('/')
def home():
    if is_logged_in():
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if validate_login(username, password):
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('index.html', error='Invalid username or password')

    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/login')
    
    # Get the list of registered usernames
    registered_users = list(users.keys())
    
    return render_template('dashboard.html', username=session['username'], registered_users=registered_users)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if is_logged_in():
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return render_template('signup.html', error='Username already exists')

        users[username] = password
        return redirect('/login')

    return render_template('signup.html')

@socketio.on('connect')
def handle_connect():
    if is_logged_in():
        join_room(session['username'])

# WebSocket event for receiving and sending messages
# WebSocket event for receiving and sending messages
@socketio.on('message')
def handle_message(data):
    message = data.get('message') or data.get('content')
    room_id = data['room_id']
    
    if message:
        sender = session['username']  # Get the sender's username
        message_with_sender = f"{sender}: {message}"
        
        # Store and broadcast the message as usual
        store_message_for_room(room_id, message_with_sender)
        emit('message', {'content': message_with_sender, 'sender': sender}, room=room_id)
    else:
        print("Error: No 'message' or 'content' key found in data")

# Route to render the chat interface
@app.route('/chat/<other_user>')
def chat(other_user):
    if not is_logged_in():
        return redirect('/login')
    
    # Pass the username to the chat template
    return render_template('chat.html', other_user=other_user, username=session['username'])

if __name__ == '__main__':
    socketio.run(app, debug=True)