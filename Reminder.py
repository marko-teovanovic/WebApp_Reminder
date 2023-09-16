from os import abort
from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)
next_id = 1
reminders = {}

def get_db_connection():
    conn = sqlite3.connect('web_reminders.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table(): 
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        priority INTEGER NOT NULL
                    )''')

    conn.commit()
    conn.close()

create_table()

def delete_reminder(reminder_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))

    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/addReminder')
def add():
    return render_template('addReminder.html')

@app.route('/updateReminder')
def upd():
    return render_template('updateReminder.html')

@app.route('/showReminder', methods=['POST'])
def save_reminder():
    name = request.form['name']
    content = request.form['content']
    priority = int(request.form['priority']) 

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO reminders (title, content, priority) VALUES (?, ?, ?)",
                   (name, content, priority))

    conn.commit()
    conn.close()

    reminder = {
        'title': name,
        'content': content,
        'priority': priority,
    }

    return render_template('showReminder.html', reminder=reminder)

@app.route('/allReminders')
def show_all_reminders():
    page = request.args.get('page', 1, type=int)
    per_page = 5

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reminders")
    total_reminders = cursor.fetchone()[0]
    total_pages = (total_reminders + per_page - 1) // per_page

    if page < 1 or page > total_pages:
        abort(404)

    offset = (page - 1) * per_page
    cursor.execute("SELECT * FROM reminders LIMIT ? OFFSET ?", (per_page, offset))
    reminders = cursor.fetchall()
    conn.close()

    return render_template('allReminders.html', reminders=reminders, page=page, total_pages=total_pages)

@app.route('/deleteReminder/<int:reminder_id>', methods=['POST'])
def delete_single_reminder(reminder_id):
    delete_reminder(reminder_id)
    return render_template('deletedReminder.html', reminder_id=reminder_id)

@app.route('/updateReminder/<int:reminder_id>', methods=['GET', 'POST'])
def update_reminder(reminder_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,))
    reminder = cursor.fetchone()

    if not reminder:
        abort(404)

    if request.method == 'POST':
        try:
            title = request.form['title']
            content = request.form['content']
            priority = int(request.form['priority'])

            cursor.execute("UPDATE reminders SET title=?, content=?, priority=? WHERE id=?",
                           (title, content, priority, reminder_id))

            conn.commit()

            cursor.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,))
            updated_reminder = cursor.fetchone()

            conn.close()

            return render_template('showReminder.html', reminder=updated_reminder)

        except KeyError:
            message = "Incomplete form data. Please provide all required fields."
            return render_template('updateReminder.html', reminder=reminder, error_message=message)

    conn.close()
    return render_template('updateReminder.html', reminder=reminder)

if __name__ == '__main__':
    app.run(debug=True)
