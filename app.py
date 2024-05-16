from flask import Flask, render_template, g, request, session, redirect, url_for
from database_files import get_db
import os
# This library used to genrate the hash for the passwords and recheck for password hash for security
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    user = None
    if 'user' in session:
        user = session['user']
    
    return render_template('home.html', user=user)

@app.route('/register', methods=['GET','POST'])
def register():

    if request.method =='POST':
        db = get_db()
        # This will generate the hash for password entered at the time of registeration
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.execute('insert into user(name, password, expert, admin) values(?,?,?,?)', [request.form['name'], hashed_password, '0', '0'])
        db.commit()
        return '<h1>user created!</h1>'
    return render_template('register.html')

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        db = get_db()

        name = request.form['name']
        password = request.form['password']

        user_cur = db.execute('select id, name, password from user where name = ?',[name])
        user_result = user_cur.fetchone()

        if check_password_hash(user_result['password'], password):
            session['user'] = user_result['name']
            return '<h1>pasword is correct</h1>'
        else:
            return '<h1>Password is incorect</h1>'

    return render_template('login.html')

@app.route('/answer')
def answer():
    return render_template('answer.html')

@app.route('/askaquestion')
def askaquestion():
    return render_template('askaquestion.html')

@app.route('/question')
def question():
    return render_template('question.html')

@app.route('/unanswered')
def unanswered():
    return render_template('unanwered.html')

@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)