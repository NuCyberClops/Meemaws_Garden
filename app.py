import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv  

# Load variables from the .env file
load_dotenv()

app = Flask(__name__)

# Pull the key safely from your environment variables. 
# If it can't find it for some reason, it falls back to a temporary placeholder.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_temporary_key_for_local_dev")

# Helper function fixed to always return a dictionary for users
def load_json(filename):
    if not os.path.exists(filename):
        if filename == 'users.json':
            return {}
        return []
    with open(filename, 'r') as f:
        return json.load(f)

def save_users(users_data):
    with open('users.json', 'w') as f:
        json.dump(users_data, f, indent=4)

@app.route('/')
def index():
    plants = load_json('plants.json')
    users = load_json('users.json')
    
    username = session.get('username')
    user_plants = []
    
    if username and username in users:
        user_plant_ids = users[username].get('my_plants', [])
        user_plants = [p for p in plants if p['id'] in user_plant_ids]
        
    return render_template('index.html', plants=plants, user_plants=user_plants, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        action = request.form.get('action')
        
        users = load_json('users.json')
        
        if action == 'signup':
            if username in users:
                return render_template('login.html', error="Username already taken!")
            
            users[username] = {
                "password": password, 
                "my_plants": []
            }
            save_users(users)
            session['username'] = username
            return redirect(url_for('index'))
            print('You have successfully signed up! You may now login.')
            
        elif action == 'login':
            if username in users and users[username]['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Invalid username or password.")
                
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/plant/<plant_id>')
def detail(plant_id):
    plants = load_json('plants.json')
    plant = next((p for p in plants if p['id'] == plant_id), None)
    if not plant:
        return "Plant not found", 404
        
    username = session.get('username')
    users = load_json('users.json')
    
    is_owned = False
    if username and username in users:
        if plant_id in users[username].get('my_plants', []):
            is_owned = True
            
    return render_template('detail.html', plant=plant, username=username, is_owned=is_owned)

@app.route('/add-to-garden/<plant_id>', methods=['POST'])
def add_to_garden(plant_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
        
    users = load_json('users.json')
    if username in users:
        if plant_id not in users[username]['my_plants']:
            users[username]['my_plants'].append(plant_id)
            save_users(users)
            
    return redirect(url_for('index'))

@app.route('/delete-from-garden/<plant_id>', methods=['POST'])
def delete_from_garden(plant_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
        
    users = load_json('users.json')
    if username in users:
        # Check if the plant is in their list and remove it
        if plant_id in users[username]['my_plants']:
            users[username]['my_plants'].remove(plant_id)
            save_users(users)
            
    return redirect(url_for('index'))

@app.route('/delete-account', methods=['POST'])
def delete_account():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
        
    users = load_json('users.json')
    if username in users:
        # Permanently delete the user from the dictionary
        del users[username]
        save_users(users)
        
    # Log them out completely
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host= '0.0.0.0', port=5000)