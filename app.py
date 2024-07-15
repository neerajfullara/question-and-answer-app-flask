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

def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']

        db = get_db()
        user_cur = db.execute('select id, name, password,expert, admin from user where name = ?',[user])
        user_result = user_cur.fetchone()

    return user_result

@app.route('/')
def index():
    user = get_current_user()
    db = get_db()

    question_cur = db.execute('select question.id as question_id, quetion_text, askers.name as asker_name, experts.name as expert_name from question join user as askers on askers.id = question.ask_by_id join user experts on experts.id = question.expert_id where question.answer_text is not null')
    question_result = question_cur.fetchall()


    return render_template('home.html', user=user, questions = question_result)

@app.route('/register', methods=['GET','POST'])
def register():

    user = get_current_user()

    if request.method =='POST':
        db = get_db()
        existing_user_cur = db.execute('select id from user where name = ?', [request.form['name']])
        existing_user = existing_user_cur.fetchone()

        if existing_user:
            return render_template('register.html', user = user, error = 'User already exist!')
        # This will generate the hash for password entered at the time of registeration
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.execute('insert into user(name, password, expert, admin) values(?,?,?,?)', [request.form['name'], hashed_password, '0', '0'])
        db.commit()
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/login', methods=['POST','GET'])
def login():

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        db = get_db()

        name = request.form['name']
        password = request.form['password']

        user_cur = db.execute('select id, name, password from user where name = ?',[name])
        user_result = user_cur.fetchone()

        if check_password_hash(user_result['password'], password):
            session['user'] = user_result['name']
            return redirect(url_for('index'))
        else:
            return '<h1>Password is incorect</h1>'

    return render_template('login.html', user=user)

@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()

    if request.method == 'POST':
        db.execute('update question set answer_text = ? where id = ?', [request.form['answer'], question_id])
        db.commit()

        return redirect(url_for('unanswered'))

    question_cur = db.execute('select id, quetion_text from  question where id = ?', [question_id])
    question = question_cur.fetchone()

    return render_template('answer.html', user=user, question = question)

@app.route('/askaquestion', methods=['GET','POST'])
def askaquestion():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    db = get_db()

    if request.method == 'POST':
        db.execute('insert into question (quetion_text, ask_by_id, expert_id) values (?,?,?)',[request.form['question'],user['id'], request.form['expert']])
        db.commit()
        return redirect(url_for('index'))

    expert_cur = db.execute('select id, name from user where expert = 1')
    expert_results = expert_cur.fetchall()

    return render_template('askaquestion.html', user=user, experts = expert_results)

@app.route('/question/<question_id>')
def question(question_id):

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    question_cur = db.execute('select question.quetion_text, question.answer_text, askers.name as asker_name, experts.name as expert_name from question join user as askers on askers.id = question.ask_by_id join user experts on experts.id = question.expert_id where question.id = ?', [question_id])
    question = question_cur.fetchone()

    return render_template('question.html', user=user, questions=question)

@app.route('/unanswered')
def unanswered():

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['expert'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()

    question_cur = db.execute('select question.id, question.quetion_text, user.name from question join user on user.id = question.ask_by_id where question.answer_text is null and question.expert_id = (?)', [user['id']])
    questions = question_cur.fetchall()

    return render_template('unanswered.html', user=user, questions=questions)

@app.route('/users')
def users():

    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    
    if user['admin'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()
    users_cur = db.execute('select id, name, expert, admin from user')
    users_results = users_cur.fetchall()
    return render_template('users.html', user=user , users=users_results)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/promote/<user_id>')
def promote(user_id):

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if user['admin'] == 0:
        return redirect(url_for('index'))
    
    db = get_db()
    db.execute('update user set expert = 1 where id = ?',[user_id])
    db.commit()
    return redirect(url_for('users'))

if __name__ == "__main__":
    app.run(debug=True)