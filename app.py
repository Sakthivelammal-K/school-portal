from flask import Flask, render_template, request, redirect, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import random
import smtplib
from email.mime.text import MIMEText

def get_student(username):
    return students.find_one({"username": username})

def get_teacher(username):
    return teachers.find_one({"username": username})

def get_courses():
    return list(courses.find())

app = Flask(__name__)
app.secret_key = "secret123"
# EMAIL CONFIGURATION
EMAIL_ADDRESS = "sakthivelammalk@gmail.com"
EMAIL_PASSWORD = "alqq rupn ytrt yokb"

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["school_portal"]

users = db["users"]
students = db["students"]
teachers = db["teachers"]
courses = db["courses"]
attendance = db["attendance"]
assignments_collection = db["assignments"]

# ---------------- LOGIN PAGE ----------------
@app.route('/')
def login_page():
    return render_template("login.html")

# ---------------- FORGOT PASSWORD PAGE ----------------
@app.route('/forgot_password')
def forgot_password():

    return render_template('forgot_password.html')
# ---------------- SEND OTP ----------------

@app.route('/send_otp', methods=['POST'])
def send_otp():

    email = request.form['email']

    # CHECK STUDENT
    user = students.find_one({"email": email})

    # CHECK TEACHER
    if not user:
        user = teachers.find_one({"email": email})

    if not user:
        flash("Email not found", "error")
        return redirect('/forgot_password')

    # GENERATE OTP
    otp = str(random.randint(100000, 999999))

    # STORE IN SESSION
    session['reset_email'] = email
    session['otp'] = otp

    # SEND EMAIL
    msg = MIMEText(f"Your OTP for password reset is: {otp}")

    msg['Subject'] = "EduPortal Password Reset OTP"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email

    try:

        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.starttls()

        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        server.sendmail(
        EMAIL_ADDRESS,
        email,
        msg.as_string()
        )

        server.quit()

        flash("OTP sent successfully", "success")

        return redirect('/verify_otp')

    except Exception as e:

        print("EMAIL ERROR:", e)

        flash(str(e), "error")

        return redirect('/forgot_password')
# ---------------- VERIFY OTP PAGE ----------------

@app.route('/verify_otp')
def verify_otp():

    return render_template('verify_otp.html')


# ---------------- VERIFY OTP ----------------

@app.route('/verify_otp', methods=['POST'])
def verify_otp_post():

    entered_otp = request.form['otp']

    if entered_otp == session.get('otp'):

        flash("OTP verified successfully", "success")

        return redirect('/new_password')

    flash("Invalid OTP", "error")

    return redirect('/verify_otp')


# ---------------- NEW PASSWORD PAGE ----------------

@app.route('/new_password')
def new_password():

    return render_template('new_password.html')


# ---------------- UPDATE PASSWORD ----------------

@app.route('/update_password', methods=['POST'])
def update_password():

    new_password = request.form['new_password']

    hashed_password = generate_password_hash(new_password)

    email = session.get('reset_email')

    # UPDATE STUDENT
    result = students.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )

    # UPDATE TEACHER
    if result.modified_count == 0:

        teachers.update_one(
            {"email": email},
            {"$set": {"password": hashed_password}}
        )

    flash("Password updated successfully", "success")

    return redirect('/')

# ---------------- SIGNUP PAGE ----------------
@app.route('/signup')
def signup():
    all_courses = list(courses.find())
    return render_template("signup.html", courses=all_courses)

# ---------------- STUDENT SIGNUP ----------------
@app.route('/student_signup', methods=['POST'])
def student_signup():

    username = request.form['username']
    email = request.form['email']
    course = request.form['course']
    password = request.form['password']

    existing = students.find_one({
        "username": username
    })

    if existing:
        flash("Student already exists", "error")
        return redirect('/signup')

    hashed_password = generate_password_hash(password)

    # FIND COURSE
    course_data = courses.find_one({
        "course_name": course
    })

    # IF COURSE NOT FOUND
    if not course_data:

        flash("Course not found", "error")
        return redirect('/signup')

    # INSERT STUDENT
    students.insert_one({

        "username": username,
        "email": email,

"courses": [
    {
        "course_name": course_data["course_name"],
        "course_description": course_data["course_description"],
        "source": "signup"
    }
],

        "password": hashed_password

    })

    session['student'] = username

    return redirect('/student_dashboard')
# ---------------- TEACHER SIGNUP ----------------
@app.route('/teacher_signup', methods=['POST'])
def teacher_signup():

    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    existing = teachers.find_one({"username": username})

    if existing:
        flash("Teacher already exists", "error")
        return redirect('/signup')

    hashed_password = generate_password_hash(password)

    teachers.insert_one({

        "username": username,
        "email": email,
        "password": hashed_password

    })

    session['teacher'] = username

    return redirect('/teacher_dashboard')
# ---------------- STUDENT LOGIN ----------------

@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    print("Entered Email:", email)
    print("Entered Password:", password)

    # CHECK STUDENT
    student = students.find_one({
        "email": email
    })

    print("Student Found:", student)

    if student:

        print("Stored Password:", student['password'])

        if check_password_hash(student['password'], password):

            print("Student Login Success")

            session['student'] = student['username']

            return redirect('/student_dashboard')

    # CHECK TEACHER
    teacher = teachers.find_one({
        "email": email
    })

    print("Teacher Found:", teacher)

    if teacher:

        print("Stored Password:", teacher['password'])

        if check_password_hash(teacher['password'], password):

            print("Teacher Login Success")

            session['teacher'] = teacher['username']

            return redirect('/teacher_dashboard')

    flash("Invalid Email or Password", "error")

    return redirect('/')
# ---------------- TEACHER DASHBOARD ----------------
@app.route('/teacher_dashboard')
def teacher_dashboard():

    if 'teacher' not in session:
        return redirect('/')

    # TOTAL STUDENTS
    total_students = students.count_documents({})

    # TOTAL ASSIGNMENTS
    total_assignments = assignments_collection.count_documents({})

    # TEACHER COURSE COUNT
    enrolled_courses = courses.count_documents({
        "teacher": session['teacher']
    })

    return render_template(

        'teacher_dashboard.html',

        username=session['teacher'],

        total_students=total_students,

        total_assignments=total_assignments,

        course=enrolled_courses
    )
# ---------------- STUDENT DASHBOARD ----------------
@app.route('/student_dashboard')
def student_dashboard():

    if 'student' not in session:
        return redirect('/')

    student = students.find_one({"username": session['student']})

    user_courses = student.get("courses", [])

    return render_template(
        "student_dashboard.html",
        username=session['student'],
        enrolled_courses=len(user_courses),
        recent_courses=user_courses[-3:]  # last 3 courses
    )

# ---------------- COURSES PAGE ----------------
@app.route('/courses')
def courses_page():

    if 'student' not in session:
        return redirect('/')

    username = session['student']

    # FIND STUDENT

    student = students.find_one({
        "username": username
    })

    # GET ENROLLED COURSE IDS

    enrolled_course_ids = student.get(
        "enrolled_courses",
        []
    )

    # FETCH ONLY ENROLLED COURSES

    enrolled_courses = list(
        courses.find({
            "_id": {
                "$in": enrolled_course_ids
            }
        })
    )

    return render_template(
        'courses.html',
        courses=enrolled_courses,
        username=username
    )
# ---------------- COURSE DETAILS PAGE ----------------
@app.route('/course/<course_id>')
def view_course(course_id):

    if 'student' not in session:
        return redirect('/')

    course = courses.find_one({
        "_id": ObjectId(course_id)
    })

    return render_template(
        'course_details.html',
        course=course,
        username=session['student']
    )
# ---------------- ATTENDANCE PAGE ----------------
@app.route('/attendance')
def attendance():

    if 'teacher' in session:

        return render_template(
            'attendance.html',
            username=session['teacher']
        )

    return redirect('/')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'teacher' not in session:
        return redirect('/')

    student = request.form['student']
    course = request.form['course']
    status = request.form['status']

    attendance.insert_one({
        "student": student,
        "course": course,
        "status": status,
        "date": str(datetime.date.today())
    })

    flash("Attendance marked", "success")
    return redirect('/teacher_dashboard')
# ---------------- ASSIGNMENTS PAGE ----------------
@app.route('/assignments')
def assignments_page():

    # STUDENT VIEW
    if 'student' in session:

        all_assignments = assignments_collection.find()

        return render_template(
            'assignments.html',
            username=session['student'],
            role="student",
            assignments=all_assignments
        )

    # TEACHER VIEW
    elif 'teacher' in session:

        all_assignments = assignments_collection.find()

        return render_template(
            'assignments.html',
            username=session['teacher'],
            role="teacher",
            assignments=all_assignments
        )

    return redirect('/')

@app.route('/add_assignment', methods=['POST'])
def add_assignment():

    if 'teacher' not in session:
        return redirect('/')

    title = request.form['title']
    description = request.form['description']
    deadline = request.form['deadline']

    assignments_collection.insert_one({
        "title": title,
        "description": description,
        "deadline": deadline,
        "teacher": session['teacher']
    })
    flash("Assignment added successfully", "success")

    return redirect('/teacher_assignments')
# ---------------- PROGRESS PAGE ----------------
@app.route('/progress')
def progress():

    if 'student' in session:

        return render_template(
            'progress.html',
            username=session['student']
        )

    return redirect('/')


# ---------------- SETTINGS PAGE ----------------
# ---------------- STUDENT SETTINGS ----------------
@app.route('/student_setting')
def student_settings():

    if 'student' not in session:
        return redirect('/')

    user = students.find_one({"username": session['student']})

    enrolled_courses = user.get("courses", [])

    print("ENROLLED:", enrolled_courses)  # DEBUG

    return render_template(
        "student_setting.html",
        user=user,
        courses=list(courses.find({}, {"_id": 0})),
        enrolled_courses=enrolled_courses
    )

@app.route('/enroll_course', methods=['POST'])
def enroll_course():

    if 'student' not in session:
        return redirect('/')

    course_name = request.form.get('course_name')

    course = courses.find_one({"course_name": course_name})

    if not course:
        return redirect('/student_setting')

    students.update_one(
        {"username": session['student']},
        {
            "$addToSet": {
                "courses": {
    "course_name": course["course_name"],
    "course_description": course["course_description"],
    "source": "settings"
}
            }
        }
    )

    return redirect('/student_setting')

@app.route('/debug')
def debug():

    student = students.find_one({"username": session['student']})

    return str(student)

@app.route('/unenroll_course', methods=['POST'])
def unenroll_course():

    if 'student' not in session:
        return redirect('/')

    course_name = request.form['course_name']

    students.update_one(
        {"username": session['student']},
        {
            "$pull": {
                "courses": {
                    "course_name": course_name
                }
            }
        }
    )

    return redirect('/student_setting')
# ---------------- TEACHER SETTINGS ----------------
@app.route('/settings')
def settings():

    if 'teacher' in session:

        user = teachers.find_one({
            "username": session['teacher']
        })

        return render_template(
            'settings.html',
            username=session['teacher'],
            role="teacher",
            user=user
        )

    return redirect('/')
# ---------------- UPDATE SETTINGS ----------------
@app.route('/update_settings', methods=['POST'])
def update_settings():

    if 'student' not in session:
        return redirect('/')

    old_username = session['student']

    new_username = request.form['new_username']
    new_password = request.form['new_password']

    hashed_password = generate_password_hash(new_password)

    students.update_one(
        {"username": old_username},
        {
            "$set": {
                "username": new_username,
                "password": hashed_password
            }
        }
    )

    session['student'] = new_username

    flash("Changes updated successfully", "success")
    return redirect('/settings')
# ---------------- STUDENT COURSES PAGE ----------------
@app.route('/student_courses')
def student_courses():

    if 'student' not in session:
        return redirect('/')

    student = students.find_one({
        "username": session['student']
    })

    enrolled_courses = student.get("courses", [])

    return render_template(
        "student_courses.html",
        enrolled_courses=enrolled_courses
    )
# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ---------------- TEACHER STUDENTS ----------------
@app.route('/teacher_students')
def teacher_students():

    if 'teacher' not in session:
        return redirect('/')

    all_students = list(students.find())

    for student in all_students:
        courses_data = student.get("courses", [])

        signup_courses = []

        for c in courses_data:

            # if format is correct dict
            if isinstance(c, dict) and "course_name" in c:
                signup_courses.append(c["course_name"])

            # if old format is string
            elif isinstance(c, str):
                signup_courses.append(c)

        student["signup_courses"] = signup_courses

        return render_template(
        'teacher_students.html',
        students=all_students,
        username=session['teacher']
    )
    return redirect('/')
# ---------------- TEACHER CLASSES ----------------
@app.route('/teacher_classes')
def teacher_classes():

    if 'teacher' not in session:
        return redirect('/')

    all_courses = courses.find()

    return render_template(
        'teacher_classes.html',
        username=session['teacher'],
        courses=all_courses
    )

@app.route('/add_course', methods=['POST'])
def add_course():

    if 'teacher' not in session:
        return redirect('/')

    course_name = request.form['course_name']
    course_description = request.form['course_description']

    courses.insert_one({

        "course_name": course_name,
        "course_description": course_description,
        "teacher": session['teacher']

    })

    flash("Course added successfully", "success")

    return redirect('/teacher_classes')
# ---------------- TEACHER ASSIGNMENTS ----------------
@app.route('/teacher_assignments')
def teacher_assignments():

    if 'teacher' not in session:
        return redirect('/')

    all_assignments = assignments_collection.find({
        "teacher": session['teacher']
    })

    return render_template(
        'teacher_assignments.html',
        username=session['teacher'],
        assignments=all_assignments
    )

# ---------------- OPEN EDIT PAGE ----------------

@app.route('/edit_assignment/<assign_id>')
def edit_assignment(assign_id):

    if 'teacher' not in session:
        return redirect('/')

    assignment = assignments_collection.find_one({
        "_id": ObjectId(assign_id)
    })

    return render_template(
        'edit_assignment.html',
        assignment=assignment
    )

    flash("Assignment updated successfully", "success")

    return redirect('/teacher_assignments')

@app.route('/update_assignment/<assign_id>', methods=['POST'])
def update_assignment(assign_id):

    if 'teacher' not in session:
        return redirect('/')

    assignments_collection.update_one(
        {"_id": ObjectId(assign_id)},
        {
            "$set": {
                "title": request.form['title'],
                "description": request.form['description'],
                "deadline": request.form['deadline']
            }
        }
    )

    flash("Assignment updated successfully", "success")

    return redirect('/teacher_assignments')


@app.route('/delete_assignment/<assign_id>')
def delete_assignment(assign_id):

    if 'teacher' not in session:
        return redirect('/')

    assignments_collection.delete_one({"_id": ObjectId(assign_id)})

    flash("Assignment deleted successfully", "success")
    return redirect('/teacher_assignments')
print("DELETE CALLED ONCE")

# ---------------- TEACHER REPORTS ----------------
@app.route('/teacher_reports')
def teacher_reports():

    if 'teacher' in session:

        # TOTAL COUNTS
        total_students = students.count_documents({})
        total_courses = courses.count_documents({})
        total_assignments = assignments_collection.count_documents({})

        return render_template(
            'teacher_reports.html',
            username=session['teacher'],
            total_students=total_students,
            total_courses=total_courses,
            total_assignments=total_assignments
        )

    return redirect('/')

@app.route('/delete_course/<course_id>')
def delete_course(course_id):

    if 'teacher' not in session:
        return redirect('/')

    courses.delete_one({"_id": ObjectId(course_id)})

    flash("Course deleted successfully", "success")

    return redirect('/teacher_classes')

@app.route('/edit_course/<course_id>', methods=['POST'])
def edit_course(course_id):
    courses.update_one(
        {"_id": ObjectId(course_id)},
        {
            "$set": {
                "course_name": request.form['course_name'],
                "course_description": request.form['course_description']
            }
        }
    )
    flash("Course updated successfully", "success")
    return redirect('/teacher_classes')

if __name__ == '__main__':
    app.run(debug=True)