from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from config import config_

# Configure application
app = Flask(__name__)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

params = config_()
connection = psycopg2.connect(**params)
crsr = connection.cursor()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
       
        if not username or not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
        
        crsr.execute("SELECT UserID, username, email, password FROM Users WHERE username = %s", (username,))
        user = crsr.fetchone()

        if user and user[1] == username and user[2] == email and user[3] == password:
            session["user_id"] = user[0]
            flash("Login successful")
            return redirect(url_for('index'))  # Corrected route
        else:
            flash('Invalid username, email or password', 'error')
            return redirect(url_for('login'))  # Added redirect to login
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        # Check if fields are provided
        if not username or not email or not password or not name:
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
            
        # Check if user already exists
        crsr.execute("SELECT * FROM \"User\" WHERE username = %s OR email = %s", (username, email))
        existing_user = crsr.fetchone()
        
        if existing_user:
            flash('Username or email already exists', 'error')
            return render_template('register.html')
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Insert new user
        crsr.execute(
            "INSERT INTO \"User\" (username, email, password, name) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, name)
        )
        connection.commit()
        
        flash('Registration successful, please login', 'success')
        return redirect(url_for('login'))
   
    return render_template('register.html')


@app.route('/index')
def index():
    user_id = session.get("user_id")
    if user_id:
        flash('Welcome back!', 'success')
        return render_template('index.html')  # Render the main page for logged-in users
    else:
        flash('Please log in to access the homepage', 'info')
        return redirect(url_for('login'))

@app.route('/communities')
def communities():
    return render_template('communities.html')


if __name__ == '__main__':
    app.run(debug=True)
