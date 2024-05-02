from flask import Flask, render_template, redirect, request, session, flash
import sqlite3, datetime
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

# DATABASE = "C:/Users/GGPC/PycharmProjects/TeReoDictionary/TeReoDictionary.db" # Desktop
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


@app.route('/', methods=['POST', 'GET'])
def render_home():
    # gets search
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        return redirect('/words/' + search)

    return render_template('home.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/words', methods=['POST', 'GET'])
def render_words():
    # gets search
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        return redirect('/words/' + search)

    words = database_select('SELECT * FROM words', ())
    return render_template('words.html', logged_in=is_logged_in(), user_info=user_info(), word_info=words)


@app.route('/words/')
def words_redirect():
    return redirect('/words')


@app.route('/words/category/<category_id>', methods=['POST', 'GET'])
def render_wordcategory(category_id):
    # gets search
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        return redirect('/words/' + search)

    category = database_select('SELECT category FROM categories WHERE category_id = ?', (category_id,))[0][0]
    words = database_select('SELECT * FROM words WHERE category = ?', (category,))

    if len(words) == 0:
        words = None
    return render_template('words.html', logged_in=is_logged_in(), user_info=user_info(), word_info=words)


@app.route('/words/<search>', methods=['POST', 'GET'])
def render_wordsearch(search):
    # gets search
    if request.method == 'POST':
        search = request.form.get('search').lower().strip()
        return redirect('/words/' + search)

    words = []
    all_words = database_select('SELECT * FROM words', ())
    # Checks all the parts for all the words
    for word in all_words:
        for part in word:
            # Checks to see if the search is in the part, also prevents the id from matching with the search
            if search in str(part).lower() and (part != word[0] and part != word[6] and part != word[7] and part != word[8]):
                # If there is a match, if the word is not already in the list it is added
                if word not in words:
                    words.append(word)

    if len(words) == 0:
        words = None
    return render_template('words.html', logged_in=is_logged_in(), user_info=user_info(), word_info=words)


@app.route('/categories', methods=['POST', 'GET'])
def render_categories():
    categories = database_select('SELECT * FROM categories', ())
    return render_template('categories.html', logged_in=is_logged_in(), user_info=user_info(), categories=categories)


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

    return render_template('signup.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/logout')
def logout():
    # removes all info from the user's session
    [session.pop(key) for key in list(session.keys())]
    flash("You have been logged out!", "info")
    return redirect('/')


@app.route('/about')
def about():
    #words = database_select('SELECT * FROM words', ())
    #new_date = datetime.strptime("9 11 1901", "%d %m %Y").date()
    #for word in words:
    #    database_action('UPDATE words SET last_edited_date=? WHERE id=?',(new_date, word[0]))
    #    database_action('UPDATE words SET last_edited_by=? WHERE id=?',('ET', word[0]))
    #    database_action('UPDATE words SET image_name=? WHERE id=?',('noimage', word[0]))
    return render_template('about.html', logged_in=is_logged_in(), user_info=user_info())


@app.route('/add', methods=['POST', 'GET'])
def add():
    if is_logged_in():
        if session['role'] != 'Teacher':
            return redirect('/')
    else:
        return redirect('/')

    if request.method == 'POST':
        maori = request.form.get('maori').title().strip()
        english = request.form.get('english').title().strip()
        definition = request.form.get('definition').capitalize().strip()
        category = request.form.get('category')
        level = request.form.get('level')
        user = session['firstname'] + session['lastname']
        edited_date = datetime.today().strftime('%Y-%m-%d')
        image_name = request.form.get('image_name')
        if image_name == None:
            image_name = 'noimage'

        database_action('INSERT INTO words (english_word, maori_word, definition, category, level, last_edited_date, last_edited_by, image_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',(english, maori, definition, category, level, edited_date, user, image_name))
        flash("Your word has been added!", "info")

    categories = database_select('SELECT * FROM categories', ())

    return render_template('edit.html', logged_in=is_logged_in(), user_info=user_info(), categories=categories, word_info=None)


@app.route('/edit/<word_id>', methods=['POST', 'GET'])
def edit(word_id):
    if is_logged_in():
        if session['role'] != 'Teacher':
            return redirect('/')
    else:
        return redirect('/')

    if request.method == 'POST':
        maori = request.form.get('maori').title().strip()
        english = request.form.get('english').title().strip()
        definition = request.form.get('definition').capitalize().strip()
        category = request.form.get('category')
        level = request.form.get('level')
        user = session['firstname'] + session['lastname']
        edited_date = datetime.today().strftime('%Y-%m-%d')
        image_name = request.form.get('image_name')
        if image_name == None:
            image_name = 'noimage'

        database_action('UPDATE words SET english_word=?, maori_word=?, definition=?, category=?, level=?, last_edited_date=?, last_edited_by=?, image_name=? WHERE id=?',(english, maori, definition, category, level, edited_date, user, image_name, word_id))
        flash("The word has been updated!", "info")

    categories = database_select('SELECT * FROM categories', ())
    word_info = database_select('SELECT * FROM words WHERE id=?',(word_id,))[0]

    return render_template('edit.html', logged_in=is_logged_in(), user_info=user_info(), categories=categories, word_info=word_info)


@app.route('/delete/<word_id>')
def delete(word_id):
    if is_logged_in():
        if session['role'] != 'Teacher':
            return redirect('/')
    else:
        return redirect('/')

    database_action('DELETE FROM words WHERE id = ?', (word_id,))
    flash("The word has been deleted!", "info")
    return redirect('/words')


if __name__ == '__main__':
    app.run()
