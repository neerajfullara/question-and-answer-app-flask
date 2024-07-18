from flask import Flask, render_template, g, request, session, redirect, url_for
from database_files import get_db
import os
from flask_sqlalchemy import SQLAlchemy
# This library used to genrate the hash for the passwords and recheck for password hash for security
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()

    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()

def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']

        db = get_db()
        db.execute('select id, name, password,expert, admin from users where name = %s',(user,))
        user_result = db.fetchone()

    return user_result

@app.route('/')
def index():
    user = get_current_user()
    db = get_db()

    db.execute(
        '''select question.id as question_id, quetion_text, askers.name as asker_name, experts.name as expert_name 
        from question join users as askers on askers.id = question.ask_by_id 
        join users experts on experts.id = question.expert_id where question.answer_text is not null'''
        )
    question_result = db.fetchall()


    return render_template('home.html', user=user, questions = question_result)

@app.route('/register', methods=['GET','POST'])
def register():

    user = get_current_user()

    if request.method =='POST':
        db = get_db()
        db.execute('select id from users where name = %s', (request.form['name'],))
        existing_user = db.fetchone()

        if existing_user:
            return render_template('register.html', user = user, error = 'User already exist!')
        # This will generate the hash for password entered at the time of registeration
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.execute('''insert into users(name, password, expert, admin) 
                   values(%s,%s,%s,%s)''', (request.form['name'], hashed_password, '0', '0'))
        return redirect(url_for('index'))
    return render_template('register.html', user=user)

@app.route('/login', methods=['POST','GET'])
def login():

    user = get_current_user()
    error = None

    if request.method == 'POST':
        db = get_db()

        name = request.form['name']
        password = request.form['password']

        db.execute('select id, name, password from users where name = %s',(name,))
        user_result = db.fetchone()

        # login failure
        if user_result:
            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                error = 'Password is incorect'
        else:
            error = 'User name is incorrect'

    return render_template('login.html', user=user, error=error)

@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if not user['expert']:
        return redirect(url_for('index'))
    
    db = get_db()

    if request.method == 'POST':
        db.execute('update question set answer_text = %s where id = %s', (request.form['answer'], question_id))
        db.commit()

        return redirect(url_for('unanswered'))

    db.execute('select id, quetion_text from  question where id = %s', (question_id,))
    question = db.fetchone()

    return render_template('answer.html', user=user, question = question)

@app.route('/askaquestion', methods=['GET','POST'])
def askaquestion():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    db = get_db()

    if request.method == 'POST':
        db.execute('insert into question (quetion_text, ask_by_id, expert_id) values (%s,%s,%s)',(request.form['question'],user['id'], request.form['expert']))
        db.commit()
        return redirect(url_for('index'))

    db.execute('select id, name from users where expert = True')
    expert_results = db.fetchall()

    return render_template('askaquestion.html', user=user, experts = expert_results)

@app.route('/question/<question_id>')
def question(question_id):

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    db.execute(
        '''select question.quetion_text, question.answer_text, askers.name as asker_name, experts.name as expert_name 
        from question join users as askers on askers.id = question.ask_by_id 
        join users experts on experts.id = question.expert_id where question.id = %s''', (question_id,)
        )
    question = db.fetchone()

    return render_template('question.html', user=user, questions=question)

@app.route('/unanswered')
def unanswered():

    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if not user['expert']:
        return redirect(url_for('index'))
    
    db = get_db()

    db.execute(
        '''select question.id, question.quetion_text, users.name from question 
        join users on user.id = question.ask_by_id where question.answer_text is null 
        and question.expert_id = (%s)''', (user['id'],)
        )
    questions = db.fetchall()

    return render_template('unanswered.html', user=user, questions=questions)

@app.route('/users')
def users():

    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    
    if not user['admin']:
        return redirect(url_for('index'))
    
    db = get_db()
    db.execute('select id, name, expert, admin from users')
    users_results = db.fetchall()
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
    
    if not user['admin']:
        return redirect(url_for('index'))
    
    db = get_db()
    db.execute('update users set expert = True where id = %s',(user_id,))
    return redirect(url_for('users'))

if __name__ == "__main__":
    app.run(debug=True)