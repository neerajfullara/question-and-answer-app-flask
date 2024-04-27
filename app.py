from flask import Flask, render_template, g, request
from database_files import get_db

# This library used to genrate the hash for the passwords and recheck for password hash for security
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def index():
    return render_template('home.html')

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

@app.route('/login')
def login():
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

if __name__ == "__main__":
    app.run(debug=True)