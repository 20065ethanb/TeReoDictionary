from flask import Flask, render_template, redirect, request, session, flash
import sqlite3, datetime
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

# PROJECT = "C:/Users/GGPC/PycharmProjects/TeReoDictionary" # Desktop
PROJECT = "C:/Users/ethan/PycharmProjects/Te Reo Dictionary"  # Laptop
DATABASE = PROJECT + "/TeReoDictionary.db"

# variables
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "7175"
ignoredParts = [0, 4, 6, 7, 8]


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


def session_info():
    # gets session info
    return session


def category_info():
    return database_select('SELECT * FROM categories', ())


def user_info():
    return database_select('SELECT * FROM users', ())


def search_redirect(search, category_filter):
    # Redirects user based on search and filter
    categories = category_info()
    category_id = '0'
    for category in categories:
        if category[1] == category_filter:
            category_id = str(category[0])
    if search == '' and category_id == '0':
        return redirect('/words')
    elif search == '':
        return redirect('/words/category/' + category_id)
    else:
        return redirect('/words/' + category_id + '&' + search)


@app.route('/', methods=['POST', 'GET'])
def render_home():
    # home page
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        return redirect('/words/0&' + search)

    return render_template('home.html', logged_in=is_logged_in(), session_info=session_info())


@app.route('/words', methods=['POST', 'GET'])
def render_words():
    # gets search and redirects based on search and filter
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        category_filter = request.form.get('category')
        return search_redirect(search, category_filter)

    words = database_select('SELECT * FROM words', ())
    return render_template('words.html', logged_in=is_logged_in(), session_info=session_info(), word_info=words, categories=category_info(), users=user_info(), search=None)


@app.route('/words/category/<category_id>', methods=['POST', 'GET'])
def render_wordcategory(category_id):
    # gets search and redirects based on search and filter
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        category_filter = request.form.get('category')
        return search_redirect(search, category_filter)

    words = database_select('SELECT * FROM words WHERE category_id = ?', (category_id,))
    if len(words) == 0:
        words = None

    search = [int(category_id), None]
    return render_template('words.html', logged_in=is_logged_in(), session_info=session_info(), word_info=words, categories=category_info(), users=user_info(), words=words, search=search)


@app.route('/words/<search>', methods=['POST', 'GET'])
def render_wordsearch(search):
    # gets search and redirects based on search and filter
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        category_filter = request.form.get('category')
        return search_redirect(search, category_filter)

    words = []
    # Splits the search into searched word and category
    search = str(search).split('&')
    if len(search) == 2:
        all_words = database_select('SELECT * FROM words', ())
        # Checks all the parts for all the words
        for word in all_words:
            for part in word:
                # Checks to see if the search is in the part, also prevents the id from matching with the search
                if search[1] in str(part).lower() and (word[4] == int(search[0]) or search[0] == '0') and (word.index(part) not in ignoredParts):
                    # If there is a match, if the word is not already in the list it is added
                    if word not in words:
                        words.append(word)

    if len(words) == 0:
        words = None

    search[0] = int(search[0])
    return render_template('words.html', logged_in=is_logged_in(), session_info=session_info(), word_info=words, categories=category_info(), users=user_info(), search=search)


@app.route('/categories', methods=['POST', 'GET'])
def render_categories():
    # shows categories page
    return render_template('categories.html', logged_in=is_logged_in(), session_info=session_info(), categories=category_info())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    # checks if they're logged in, if so they're sent to homepage
    if is_logged_in():
        flash("Already logged in!")
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
            flash("Invalid username or password")
            return redirect('/login')

        # checks the password
        if not bcrypt.check_password_hash(db_password, password):
            flash("Invalid username or password")
            return redirect(request.referrer)

        # creates the user's session
        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['lastname'] = last_name
        session['role'] = role
        flash("Login successful")
        return redirect('/')

    return render_template('login.html', logged_in=is_logged_in(), session_info=session_info())


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
            flash("Passwords do not match!")
            return redirect('/signup')

        # make the minimum length 8 charters
        if len(password) < 8:
            flash("Passwords must be at least 8 characters!")
            return redirect('/signup')

        # changes the password for the database so the site's owner can't see it
        hashed_password = bcrypt.generate_password_hash(password)
        # insert the information unless email is already used
        try:
            database_action('INSERT INTO users (fname, lname, email, password, role) VALUES (?, ?, ?, ?, ?)',(fname, lname, email, hashed_password, role))
        except sqlite3.IntegrityError:
            flash("Email is already used!")
            return redirect('/signup')

        return redirect('/login')

    return render_template('signup.html', logged_in=is_logged_in(), session_info=session_info())


@app.route('/logout')
def logout():
    # removes all info from the user's session
    [session.pop(key) for key in list(session.keys())]
    flash("You have been logged out!", "info")
    return redirect('/')


@app.route('/about')
def about():
    # functions to change data automatically
    """
    words = database_select('SELECT * FROM words', ())
    new_date = datetime.strptime("9 11 1901", "%d %m %Y").date()
    for word in words:
        database_action('UPDATE words SET last_edited_date=? WHERE id=?',(new_date, word[0]))
        database_action('UPDATE words SET last_edited_by_id=? WHERE id=?',(7, word[0]))
        database_action('UPDATE words SET image_name=? WHERE id=?',('noimage', word[0]))
    """
    return render_template('about.html', logged_in=is_logged_in(), session_info=session_info())


@app.route('/add', methods=['POST', 'GET'])
def add():
    # checks if the user is a teacher
    if is_logged_in():
        if session['role'] != 'Teacher':
            return redirect('/')
    else:
        return redirect('/')

    if request.method == 'POST':
        # gets info from form and formats it
        maori = request.form.get('maori').title().strip()
        english = request.form.get('english').title().strip()
        definition = request.form.get('definition').capitalize().strip()
        word_category = request.form.get('category')
        category_id = 0
        for category in category_info():
            if category[1] == word_category:
                category_id = category[0]
        level = request.form.get('level')
        user_id = session['user_id']
        edited_date = datetime.today().strftime('%Y-%m-%d')
        image_name = request.form.get('image_name').lower()
        valid_image_name = 'noimage'
        # credit goes to stack overflow for "os.listdir"
        for file in os.listdir(PROJECT + "/static/images"):
            filename = file.split('.')[0]
            if image_name == filename.lower():
                valid_image_name = filename

        # adds word to database
        database_action('INSERT INTO words (english_word, maori_word, definition, category_id, level, last_edited_date, last_edited_by_id, image_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',(english, maori, definition, category_id, level, edited_date, user_id, valid_image_name))
        flash("Your word has been added!", "info")

    return render_template('edit.html', logged_in=is_logged_in(), session_info=session_info(), categories=category_info(), word_info=None)


@app.route('/edit/<word_id>', methods=['POST', 'GET'])
def edit(word_id):
    # checks if the user is a teacher
    if is_logged_in():
        if session['role'] != 'Teacher':
            return redirect('/')
    else:
        return redirect('/')

    if request.method == 'POST':
        # gets info from form and formats it
        maori = request.form.get('maori').title().strip()
        english = request.form.get('english').title().strip()
        definition = request.form.get('definition').capitalize().strip()
        word_category = request.form.get('category')
        category_id = 0
        for category in category_info():
            if category[1] == word_category:
                category_id = category[0]
        level = request.form.get('level')
        user_id = session['user_id']
        edited_date = datetime.today().strftime('%Y-%m-%d')
        image_name = request.form.get('image_name')
        valid_image_name = 'noimage'
        # credit goes to stack overflow for "os.listdir"
        for file in os.listdir(PROJECT + "/static/images"):
            filename = file.split('.')[0]
            if image_name == filename:
                valid_image_name = filename

        # updates the existing word to have new info
        database_action('UPDATE words SET english_word=?, maori_word=?, definition=?, category_id=?, level=?, last_edited_date=?, last_edited_by_id=?, image_name=? WHERE id=?',(english, maori, definition, category_id, level, edited_date, user_id, valid_image_name, word_id))
        flash("The word has been updated!", "info")

    word_info = database_select('SELECT * FROM words WHERE id=?',(word_id,))[0]

    return render_template('edit.html', logged_in=is_logged_in(), session_info=session_info(), categories=category_info(), word_info=word_info)


@app.route('/delete/<word_id>')
def render_delete(word_id):
    # gets the selected word's info
    word_info = database_select('SELECT * FROM words WHERE id=?',(word_id,))[0]
    return render_template('delete.html', logged_in=is_logged_in(), session_info=session_info(), word_info=word_info, categories=category_info(), users=user_info())


@app.route('/delete_word/<word_id>')
def delete(word_id):
    # checks if user is teacher
    if is_logged_in():
        if session['role'] != 'Teacher':
            return redirect('/')
    else:
        return redirect('/')

    # deletes the word from the database
    database_action('DELETE FROM words WHERE id = ?', (word_id,))
    flash("The word has been deleted!", "info")
    return redirect('/words')


if __name__ == '__main__':
    app.run()
