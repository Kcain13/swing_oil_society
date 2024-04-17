from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Golfer, Course, Tee, Hole, Round, Score, Milestone, Statistic
from forms import RegistrationForm, LoginForm, ScoreEntryForm, GolferSearchForm, CourseSearchForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///swing_oil_society.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Golfer.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_golfer = Golfer(username=form.username.data, email=form.email.data)
        db.session.add(new_golfer)
        db.session.commit()
        flash('You have been registered! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        golfer = Golfer.query.filter_by(username=form.username.data).first()
        if golfer:
            login_user(golfer, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form)


@app.route('/search_courses', methods=['GET'])
def search_courses():
    query = request.args.get('query')
    courses = Course.query.filter(Course.name.ilike(
        f'%{query}%')).all()  # This is a simple search
    return render_template('search_results.html', courses=courses)


@app.route('/search_course', methods=['POST'])
def search_course():
    data = request.json
    course_name = data['course_name']
    # Assume `fetch_courses_from_ghin_api` is a function that calls the GHIN API
    courses = fetch_courses_from_ghin_api(course_name)
    return jsonify(courses)


def fetch_courses_from_ghin_api(course_name):
    # This function would handle the API call to GHIN
    # For simplicity, assume it returns a list of dictionaries with course details
    # Example static data
    return [{'name': 'Pebble Beach', 'location': 'California'}]


@app.route('/start_round/<int:course_id>', methods=['GET', 'POST'])
@login_required
def start_round(course_id):
    if request.method == 'POST':
        # Assuming the form submission handles POST
        # Create and start the round
        new_round = Round(golfer_id=current_user.id, course_id=course_id)
        db.session.add(new_round)
        db.session.commit()
        flash('Round started successfully!', 'success')
        return redirect(url_for('enter_scores', round_id=new_round.id))
    return render_template('start_round.html', course_id=course_id)


@app.route('/submit_score', methods=['GET', 'POST'])
@login_required
def submit_score():
    form = ScoreEntryForm()
    if form.validate_on_submit():
        # Process the score submission
        flash('Score submitted successfully!', 'success')
        return redirect(url_for('dashboard'))  # Assume a dashboard view
    return render_template('submit_score.html', form=form)


@app.route('/view_golfer', methods=['POST'])
def view_golfer():
    form = GolferSearchForm()
    if form.validate_on_submit():
        golfer = Golfer.query.filter_by(
            username=form.golfer_username.data).first()
        if golfer:
            return redirect(url_for('golfer_trophy_room', golfer_id=golfer.id))
        else:
            flash('Golfer not found.', 'danger')
            return redirect(url_for('index'))
    # Redirect if not valid submission or get request
    return redirect(url_for('index'))
