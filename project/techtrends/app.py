import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_count
    connection = sqlite3.connect('database.db')
    db_connection_count += 1
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


# Function to get the number of posts available in the database
def get_post_count():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) from posts').fetchone()
    connection.close()
    return post_count[0]


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.debug(f"Could not find post with ID {post_id} - does not exist")
      return render_template('404.html'), 404
    else:
      app.logger.debug(f"Retrieved article with title {post[2]}")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug("Retrieved About Us page")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.debug(f"Created article with title {title}")
            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )

    return response


@app.route('/metrics')
def metrics():
    response = app.response_class(
        response=json.dumps({"db_connection_count": db_connection_count, "post_count": get_post_count()}),
        status=200,
        mimetype='application/json'
    )

    return response

# start the application on port 3111
if __name__ == "__main__":
    logging_format = "%(levelname)s:%(name)s:%(asctime)s:%(message)s"

    logging.basicConfig(
            level=logging.DEBUG,
            format=logging_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.StreamHandler(sys.stderr)
            ]
        )

    app.run(host='0.0.0.0', port='3111')
