from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # Use environment variable for the secret key

# Initialize the databases
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def init_data_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Route: Home/Login Page
@app.route('/')
def home():
    return '''
    <div style="text-align: center; background-color: lightgrey; padding: 20px; height: 100vh;">
        <h1>Login</h1>
        <form method="POST" action="/login">
            <label for="username">Username:</label><br>
            <input type="text" id="username" name="username" required><br><br>
            <label for="password">Password:</label><br>
            <input type="password" id="password" name="password" required><br><br>
            <button type="submit">Login</button>
        </form>
        <br>
        <a href="/register">Register</a>
    </div>
    '''

# Route: Handle Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):  # user[2] is the hashed password
        session['user_id'] = user[0]
        session['username'] = user[1]
        return redirect('/dashboard')
    else:
        flash("Login failed! Invalid username or password.", "danger")
        return redirect('/')

# Route: Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            flash("Registration successful! <a href='/'>Go to Login</a>", "success")
            return redirect('/')
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
            return redirect('/register')

    return '''
    <h1>Register</h1>
    <form method="POST">
        <label for="username">Username:</label><br>
        <input type="text" id="username" name="username" required><br><br>
        <label for="password">Password:</label><br>
        <input type="password" id="password" name="password" required><br><br>
        <button type="submit">Register</button>
    </form>
    '''

# Route: Dashboard (Protected Page)
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        conn.close()

        # Create HTML for each item (including an Edit button)
        item_rows = ""
        for item in items:
            item_rows += f'''
            <tr>
                <td>{item[0]}</td>
                <td>{item[1]}</td>
                <td>{item[2]}</td>
                <td><a href="/edit/{item[0]}">Edit</a></td>
            </tr>
            '''

        return f'''
        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: lightgrey;">
            <div>
                <form method="POST" action="/search">
                    <input type="text" name="search" placeholder="Search...">
                    <button type="submit">Search</button>
                </form>
            </div>
            <div>
                <button onclick="location.href='/new'">NEW</button>
            </div>
            <div>
                Logged in as {session['username']}
            </div>
        </div>
        <div style="text-align: right; margin-right: 20px;">
            <button onclick="location.href='/logout'">Logout</button>
        </div>
        <hr>
        <div style="padding: 10px;">
            <h1>Welcome to the Dashboard!</h1>
            <p>Use the search bar or navigation buttons above.</p>
            <table border="1" style="width: 100%; text-align: left;">
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Action</th>
                </tr>
                {item_rows}
            </table>
        </div>
        '''
    else:
        return redirect('/')

# Route: New Record (Add New Item)
@app.route('/new', methods=['GET', 'POST'])
def new():
    if 'user_id' not in session:
        flash("You must be logged in to create a new item.", "danger")
        return redirect('/')

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO items (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        conn.close()

        flash("New item added successfully!", "success")
        return redirect('/dashboard')

    return '''
    <h1>Create New Item</h1>
    <form method="POST">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name" required><br><br>
        <label for="description">Description:</label><br>
        <textarea id="description" name="description"></textarea><br><br>
        <button type="submit">Add Item</button>
    </form>
    <br>
    <a href="/dashboard">Back to Dashboard</a>
    '''

# Route: Edit Record (Edit Existing Item)
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    if 'user_id' not in session:
        flash("You must be logged in to edit an item.", "danger")
        return redirect('/')

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Fetch the item to be edited
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()

    if not item:
        flash("Item not found!", "danger")
        return redirect('/dashboard')

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        cursor.execute("UPDATE items SET name = ?, description = ? WHERE id = ?", (name, description, item_id))
        conn.commit()
        conn.close()

        flash("Item updated successfully!", "success")
        return redirect('/dashboard')

    conn.close()

    return f'''
    <h1>Edit Item</h1>
    <form method="POST">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name" value="{item[1]}" required><br><br>
        <label for="description">Description:</label><br>
        <textarea id="description" name="description">{item[2]}</textarea><br><br>
        <button type="submit">Update Item</button>
    </form>
    <br>
    <a href="/dashboard">Back to Dashboard</a>
    '''

# Route: Search Page
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        flash("You must be logged in to access the search page.", "danger")
        return redirect('/')

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        search_query = request.form['search']
        cursor.execute("SELECT * FROM items WHERE name LIKE ?", (f"%{search_query}%",))
        results = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM items")
        results = cursor.fetchall()

    conn.close()

    html = '''
    <div style="display: flex; justify-content: space-between; padding: 10px; background-color: lightgrey;">
        <div>
            <form method="POST" action="/search">
                <input type="text" name="search" placeholder="Search...">
                <button type="submit">Search</button>
            </form>
        </div>
        <div>
            <button onclick="location.href='/new'">NEW</button>
        </div>
        <div>
            Logged in as {username}
        </div>
    </div>
    <div style="text-align: right; margin-right: 20px;">
        <button onclick="location.href='/logout'">Logout</button>
    </div>
    <hr>
    <div style="padding: 10px;">
        <table border="1" style="width: 100%; text-align: left;">
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
            </tr>
    '''.format(username=session['username'])

    for item in results:
        html += f"<tr><td>{item[0]}</td><td>{item[1]}</td><td>{item[2]}</td></tr>"

    html += """
        </table>
        <br>
        <p>Displaying {count} of {total} rows</p>
        <a href='/dashboard'>Back to Dashboard</a>
    </div>
    """.format(count=len(results), total=len(results))

    return html

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect('/')

if __name__ == '__main__':
    init_db()  # Ensure user database is initialized on app startup
    init_data_db()  # Ensure data database is initialized on app startup
    app.run(debug=True, host="0.0.0.0", port=5001)
