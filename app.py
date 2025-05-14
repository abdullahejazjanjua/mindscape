from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
import psycopg2
from config import config_
from collections import defaultdict
from rag_bot import MentalHealthChatbot  

chatbot_instance = MentalHealthChatbot()
chatbot_instance.load_or_create_knowledge_base()
chatbot_instance.initialize_chain()

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

params = config_()
connection = psycopg2.connect(**params)
crsr = connection.cursor()

@app.route('/')
def home():
    return redirect(url_for('login'))

import time
@app.route('/mental_health_chatbot', methods=['GET', 'POST'])
def mental_health_chatbot():
    if request.method == 'POST':
        user_input = request.form.get('user_input', '').strip()
        action = request.form.get('action')
        if action == 'clear':
            try:
                crsr.execute("DELETE FROM bot_answers WHERE user_id = %s", (session['user_id'],))
                connection.commit()
                return render_template("mental_chatbot.html", answer=[])
            except Exception as e:
                return render_template("mental_chatbot.html", error=str(e))
        if user_input:
            try:
                crsr.execute("""
                    CREATE TABLE IF NOT EXISTS bot_answers (
                        user_id INT,
                        user_input TEXT,
                        answer TEXT,
                        time_stamp TIMESTAMP,
                        CONSTRAINT fk_users FOREIGN KEY (user_id) REFERENCES USERS(UserID)
                    )
                """)

                print(f"User input: {user_input}")
                start = time.time()
                response = chatbot_instance.retrieval_chain.invoke({"input": user_input})
                clean_answer = response['answer'].split('</think>')[-1].replace('<think>', '').strip()
                end = time.time()
                print(f"Total time: {end - start}")

                crsr.execute("""
                    INSERT INTO bot_answers (user_id, user_input, answer, time_stamp)
                    VALUES (%s, %s, %s, NOW())
                """, (session['user_id'], user_input, clean_answer))

                connection.commit()

                crsr.execute("""
                    SELECT user_input, answer
                    FROM bot_answers
                    WHERE user_id = %s 
                    ORDER BY time_stamp ASC
                """, (session['user_id'],))

                rows = crsr.fetchall()
                answer = [
                    {"user_input": row[0], "bot_answer": row[1]}
                    for row in rows
                ]

                print(answer)

                return render_template("mental_chatbot.html", answer=answer)

            except Exception as e:
                return render_template("mental_chatbot.html", error=str(e))
        else:
            flash('Please enter a message.', 'error')
            return render_template("mental_chatbot.html")

    else:
        try:
            crsr.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' AND tablename = 'bot_answers'
                )
            """)
            table_exists = crsr.fetchone()[0]

            if table_exists:
                crsr.execute("""
                    SELECT user_input, answer
                    FROM bot_answers
                    WHERE user_id = %s 
                    ORDER BY time_stamp ASC
                """, (session['user_id'],))
                

                rows = crsr.fetchall()
                answer = [
                    {"user_input": row[0], "bot_answer": row[1]}
                    for row in rows
                ]
            else:
                answer = None
            return render_template("mental_chatbot.html", answer=answer)

        except Exception as e:
            return render_template("mental_chatbot.html", error=str(e))

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
            return redirect(url_for('index')) 
        else:
            flash('Invalid username, email or password', 'error')
            return redirect(url_for('login'))  
        
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
        
        if not username or not email or not password or not name:
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
            
        crsr.execute("SELECT * FROM Users WHERE username = %s OR email = %s", (username, email))
        existing_user = crsr.fetchone()
        
        if existing_user:
            flash('Username or email already exists', 'error')
            return render_template('register.html')
        
        crsr.execute(
            "INSERT INTO Users (username, email, password, name) VALUES (%s, %s, %s, %s)",
            (username, email, password, name)
        )
        connection.commit()
        
        return redirect(url_for('login'))
   
    return render_template('register.html')


@app.route('/index')
def index():
    user_id = session.get("user_id")
    if user_id:
        return render_template('index.html')  
    else:
        return redirect(url_for('login'))

@app.route('/communities')
def communities():

    crsr.execute("SELECT * FROM Board;")
    rows = crsr.fetchall()

    boards = [
        {"BoardID": row[0], "Theme": row[1], "Date_Created": row[2], "path_to": row[3]}
        for row in rows
    ]
    
    crsr.execute("SELECT * FROM MOD_Board;")
    rowsx = crsr.fetchall()
    
    mods = [
        {"UserID": row[0], "ModID": row[1], "BoardID": row[2]}
        for row in rowsx
    ]
    crsr.execute("SELECT 1 FROM USER_MOD WHERE UserID = %s", (session['user_id'],))
    result = crsr.fetchone()
    
    if result:
        is_mod = result[0]  
    else:
        is_mod = False 

    return render_template('communities.html', boards=boards, mods=mods, is_mod=is_mod)


@app.route('/delete_board/<int:board_id>', methods=['POST'])
def delete_board(board_id):
    crsr.execute("SELECT 1 FROM USER_MOD WHERE UserID = %s", (session['user_id'],))
    result = crsr.fetchone()
    print(f"ID: {session['user_id']}")
    print(f"Result: {result}")
    if result:
        crsr.execute("DELETE FROM Board WHERE BoardID = %s", (board_id,))
        connection.commit()  
        print("Done")
    return redirect(url_for('communities')) 


@app.route('/board/<int:board_id>')
def board_detail_redirect(board_id):
    return redirect(f"/board/{board_id}/comments")


@app.route('/board/<int:board_id>/comments', methods=['GET', 'POST'])
def board_comments(board_id):
    if request.method == "POST":
        comment_text = request.form['comment_text']
        user_id = session.get('user_id')  
        parent_comment_id = request.form.get('parent_comment_id')
        
        if parent_comment_id:
            parent_comment_id = int(parent_comment_id)  
        else:
            parent_comment_id = None

        crsr.execute("""
            INSERT INTO COMMENTS (BoardID, Text, Date, UserID, ParentCommentID)
            VALUES (%s, %s, NOW(), %s, %s)
        """, (board_id, comment_text, user_id, parent_comment_id))
        
        crsr.connection.commit()

        return redirect(url_for('board_comments', board_id=board_id))
    
    crsr.execute("""
        SELECT c.CommentID, c.BoardID, c.Text, c.Date, c.UserID, c.ParentCommentID, u.Username
        FROM COMMENTS c
        JOIN USERS u ON c.UserID = u.UserID
        WHERE c.BoardID = %s
        ORDER BY c.Date ASC;
    """, (board_id,))

    rows = crsr.fetchall()

    comments = []
    for row in rows:
        comment = {
            'CommentID': row[0],
            'BoardID': row[1],
            'Text': row[2],
            'Date': row[3],
            'UserID': row[4],
            'ParentCommentID': row[5],
            'Username': row[6]
        }
        comments.append(comment)

    comment_tree = defaultdict(list)
    for comment in comments:
        comment_tree[comment['ParentCommentID']].append(comment)

    def build_thread(parent_id=None):
        threads = []
        for comment in comment_tree.get(parent_id, []):
            threads.append({
                'comment': comment,
                'replies': build_thread(comment['CommentID'])
            })
        return threads

    nested_comments = build_thread()

    return render_template("comments.html", comments=nested_comments, board_id=board_id)

if __name__ == '__main__':
    app.run(debug=True)