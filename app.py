from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["school_portal"]

students = db["students"]
teachers = db["teachers"]

# ---------------- LOGIN PAGE ----------------
@app.route('/')
def login_page():
    return render_template("login.html")

# ---------------- FORGOT PASSWORD PAGE ----------------
@app.route('/forgot_password')
def forgot_password():

    return render_template('forgot_password.html')

# ---------------- RESET PASSWORD ----------------
@app.route('/reset_password', methods=['POST'])
def reset_password():

    username = request.form['username']
    new_password = request.form['new_password']

    hashed_password = generate_password_hash(new_password)

    # Update student password
    students.update_one(
        {"username": username},
        {"$set": {"password": hashed_password}}
    )

    return redirect('/')
# ---------------- SIGNUP PAGE ----------------
@app.route('/signup')
def signup_page():
    return render_template("signup.html")

# ---------------- STUDENT SIGNUP ----------------
@app.route('/student_signup', methods=['POST'])
def student_signup():

    username = request.form['username']
    password = request.form['password']
    course = request.form['course']

    existing = students.find_one({"username": username})

    if existing:
        return "Student already exists"

    hashed_password = generate_password_hash(password)

    students.insert_one({

        "username": username,
        "password": hashed_password,
        "course": course

    })

    session['student'] = username

    return redirect('/student_dashboard')
# ---------------- TEACHER SIGNUP ----------------
@app.route('/teacher_signup', methods=['POST'])
def teacher_signup():

    username = request.form['username']
    password = request.form['password']

    existing = teachers.find_one({"username": username})

    if existing:
        return "Teacher already exists"

    hashed_password = generate_password_hash(password)

    teachers.insert_one({
        "username": username,
        "password": hashed_password
    })

    session['teacher'] = username

    return redirect('/teacher_dashboard')

# ---------------- STUDENT LOGIN ----------------
@app.route('/student_login', methods=['POST'])
def student_login():

    username = request.form['username']
    password = request.form['password']

    user = students.find_one({"username": username})

    if user and check_password_hash(user['password'], password):

        session['student'] = username

        return redirect('/student_dashboard')

    return "Invalid Student Login"

# ---------------- TEACHER LOGIN ----------------
@app.route('/teacher_login', methods=['POST'])
def teacher_login():

    username = request.form['username']
    password = request.form['password']

    user = teachers.find_one({"username": username})

    if user and check_password_hash(user['password'], password):

        session['teacher'] = username

        return redirect('/teacher_dashboard')

    return "Invalid Teacher Login"

@app.route('/student_dashboard')
def student_dashboard():

    if 'student' in session:

        return render_template(
            'student_dashboard.html',
            username=session['student']
        )

    return redirect('/')
# ---------------- STUDENT COURSES PAGE ----------------
@app.route('/student_courses')
def student_courses():

    if 'student' in session:

        return render_template(
            "student_courses.html",
            username=session['student']
        )

    return redirect('/')

# ---------------- TEACHER CLASSES PAGE ----------------
@app.route('/teacher_classes')
def teacher_classes():

    if 'teacher' in session:

        return render_template(
            "teacher_classes.html",
            username=session['teacher']
        )

    return redirect('/')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)

