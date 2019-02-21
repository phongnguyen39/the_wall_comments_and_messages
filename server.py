#The Wall assignment (Built in Flask)

from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = 'secret'
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-z0-9.+_-]+@[a-zA-z0-9.+_-]+\.[a-zA-Z]+$')

@app.route('/')
def index():    
    return render_template('index.html')

@app.route('/registration', methods=['post'])
def registration():
    session['emails'] = request.form['emails']

    is_valid = True

    if len(request.form['first_name']) < 3:
        is_valid = False
        # print('*'*10, False, '*'*10)
        flash('Please enter a first name that is at least two characters long')
        return redirect('/')

    if len(request.form['last_name']) < 3:
        is_valid = False
        # print('*'*10, False, '*'*10)
        flash('Please enter a last name that is at least two characters long')
        return redirect('/')

    if not EMAIL_REGEX.match(request.form['emails']):
        flash(f"{request.form['emails']} is invalid")
        return redirect('/')

    the_wall = connectToMySQL('the_wall')
    query = 'SELECT * FROM users WHERE email = %(emails)s'
    data = {
        'emails': request.form['emails']
    }
    existing_email = the_wall.query_db(query, data)
    # print('*'*20,existing_email)
    if len(existing_email) > 0:
        flash('Email already exist.')
        # print(('~'*20))
        return redirect('/')

    if len(request.form['password']) < 8:
        is_valid = False
        # print('*'*10, False, '*'*10)
        flash('Please enter a password name that is at least 8 characters long')
        return redirect('/')

    if request.form['password'] != request.form['password_conf']:
        is_valid = True
        flash('Make sure your passwords match')
        return redirect('/')

    if is_valid:
        the_wall = connectToMySQL('the_wall')
        query = 'INSERT INTO users (first_name, last_name, email, password) VALUES (%(first_name)s,%(last_name)s,%(email)s,%(password)s);'
        data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['emails'],
            'password': bcrypt.generate_password_hash(request.form['password'])
        }

        users = the_wall.query_db(query, data)
        # print('**'*20,the_wall)
        flash("You've successfully registered!")
        return redirect('/wall')

    # print('**__**'*20, users['id'])

@app.route('/login', methods=['post'])
def login():

    session['emails'] = request.form['emails']

    is_valid = True

    if not EMAIL_REGEX.match(request.form['emails']):
        flash(f"{request.form['emails']} is invalid")
        return redirect('/')

    the_wall = connectToMySQL('the_wall')
    query = 'SELECT * FROM users WHERE email = %(emails)s'
    data = {
        'emails': request.form['emails']
    }

    logins = the_wall.query_db(query, data)
    
    session['id'] = logins[0]['id']
    session['emails'] = logins[0]['email']

    if len(logins) == 0:
        flash("Failed login! Email not found.")
        return redirect('/')

    if logins:
        if bcrypt.check_password_hash(logins[0]['password'], request.form['password']):
            flash("Logged in successfully!")
            return redirect('/wall')
        else:
            flash("Failed login! Password was incorrect.")
            return redirect('/')

@app.route('/create_message', methods = ['post'])
def create_message():

    the_wall = connectToMySQL('the_wall')
    query = 'SELECT * FROM users WHERE email = %(emails)s'
    data = {
        'emails': session['emails']
    }

    logins = the_wall.query_db(query, data)
    print('~~~~~'*20,logins)

    messages= connectToMySQL('the_wall')
    query = "INSERT INTO messages (message, user_id) VALUES (%(message)s, %(user_id)s);"   #### still need to associate userid somehow
    data = {
        'message': request.form['message'],
        'user_id': logins[0]['id']
    }
    messages = messages.query_db(query,data)
    # print('*INSERTED MSG'*5,messages)

    return redirect('/wall')

@app.route('/create_comment', methods = ['post'])
def create_comment():

    the_wall = connectToMySQL('the_wall')
    query = 'SELECT users.id FROM users WHERE email = %(emails)s'
    data = {
        'emails': session['emails']
    }

    logins = the_wall.query_db(query, data)

    user_id = logins[0]['id']

    comment = connectToMySQL('the_wall')
    query = "INSERT INTO comments (comment,message_id,users_id) VALUES (%(comment)s,%(message_id)s,%(users_id)s);"  
    data = {
        'comment': request.form['comment'],
        'message_id': request.form['message_id'],
        'users_id': user_id
    }
    comment = comment.query_db(query,data)

    return redirect('/wall')

@app.route('/wall')
def wall():

    messages = connectToMySQL('the_wall')
    query = 'SELECT * FROM messages JOIN users ON messages.user_id = users.id;'
    messages =  messages.query_db(query)
    # print('*/'*20,messages)
   
    comments = connectToMySQL('the_wall')
    query = 'SELECT comments.message_id, comments.comment, users.first_name, users.last_name, comments.updated_at FROM comments JOIN users ON comments.users_id = users.id;'
    # query = 'SELECT comments.message_id, comments.comment, users.first_name, users.last_name, comments.updated_at FROM comments JOIN users ON comments.users_id = users.id JOIN messages ON messages.user_id = users.id;'
    comments = comments.query_db(query)
    # print('*/-'*20, comments)

    users = connectToMySQL('the_wall')
    query = 'SELECT first_name FROM users WHERE email = %(email)s;'
    data = {'email': session['emails']}
    logged_in_user = users.query_db(query, data)
    # print('*%'*20,logged_in_user)

    return render_template('wall.html', messages= messages, comments = comments, logged_in_user = logged_in_user)


@app.route('/logoff')
def logoff():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)