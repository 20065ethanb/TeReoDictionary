from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import date

# DATABASE = "C:/Users/GGPC/PycharmProjects/Te Reo Dictionary/TeReoDictionary.db" # Desktop
DATABASE = "C:/Users/ethan/PycharmProjects/Te Reo Dictionary/TeReoDictionary.db"  # Laptop

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "7175"


def create_connection(db_file):
    # create a database connection to the SQLite
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def database_select(query, info):
    # selects stuff from database
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, info)
    info = cur.fetchall()
    con.close()
    return info


def database_action(query, info):
    # executes actions to database
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, info)
    con.commit()
    con.close()
    return None


def is_logged_in():
    # checks if your logged in
    if session.get('email') is None:
        return False
    else:
        return True


def user_info():
    # gets user info
    return session


@app.route('/')
def render_home():
    return render_template('home.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    # checks if they're logged in, if so they're sent to homepage
    if is_logged_in():
        return redirect('/')

    # get your email and password
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        # checks account info to see if it is valid, error will occur if the email does not exist
        try:
            # selects your account info
            user_data = database_select("SELECT id, fname, lname, password, role FROM users WHERE email= ?", (email,))[0]

            user_id = user_data[0]
            first_name = user_data[1]
            last_name = user_data[2]
            db_password = user_data[3]
            role = user_data[4]
        except IndexError:
            return redirect('/login?error=Invalid+username+or+password')

        # checks the password
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        # creates the user's session
        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['lastname'] = last_name
        session['role'] = role
        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    # checks if you're logged in, if you your send to the home page
    if is_logged_in():
        return redirect('/')

    # gets your signup information
    if request.method == 'POST':
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        # checks if your passwords are the same
        if password != password2:
            return redirect('/signup?error=Passwords+do+not+match')

        # make the minimum length 8 charters
        if len(password) < 8:
            return redirect('/signup?error=Passwords+must+be+at+least+8+characters')

        # changes the password for the database so the site's owner can't see it
        hashed_password = bcrypt.generate_password_hash(password)
        # insert the information unless email is already used
        try:
            database_action('INSERT INTO users (fname, lname, email, password, role) VALUES (?, ?, ?, ?, ?)',(fname, lname, email, hashed_password, role))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        return redirect('/login')

    return render_template('signup.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/logout')
def logout():
    # removes all info from the user's session
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time!')


@app.route('/about')
def about():
    return render_template('about.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/edit')
def edit():  # put application's code here
    return render_template('edit.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/categories')
def categories():
    return render_template('categories.html', logged_in=is_logged_in(), user_info=user_info())


if __name__ == '__main__':
    app.run()
