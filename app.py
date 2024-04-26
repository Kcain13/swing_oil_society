
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
import plotly.express as px
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Golfer, Course, Tee, Hole, Round, Score, Milestone, Statistic, connect_db, GameType, check_and_create_milestones
from forms import RegistrationForm, LoginForm, ScoreEntryForm, GolferSearchForm, CourseSearchForm, GameInitiationForm, ProfileForm, SearchRoundsForm
from services import fetch_course_details, get_admin_token, search_courses, fetch_golfer_handicap, save_course_data
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file


app = Flask(__name__)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///swing_oil_society'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['GHIN_ADMIN_USER'] = os.getenv('GHIN_ADMIN_USER')
app.config['GHIN_ADMIN_PASSWORD'] = os.getenv('GHIN_ADMIN_PASSWORD')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")


if not app.config['GHIN_ADMIN_USER'] or not app.config['GHIN_ADMIN_PASSWORD']:
    raise Exception("API credentials are not set in environment variables.")

connect_db(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Specify the login route


@login_manager.user_loader
def load_user(user_id):
    return Golfer.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    form = CourseSearchForm()
    return render_template('home.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_golfer = Golfer(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data,
            ghin_id=form.ghin_id.data,
            state=form.state.data
        )
        new_golfer.set_password(form.password.data)
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
        if golfer and golfer.check_password(form.password.data):
            login_user(golfer, remember=form.remember_me.data)

            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('home')
            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


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


@app.route('/search_courses_route', methods=['GET', 'POST'])
@login_required
def search_courses_route():
    form = CourseSearchForm()
    if form.validate_on_submit():  # checks if the form submission is valid
        query = form.course_name.data  # directly using the validated form data
        courses = search_courses(query)  # Corrected function call
        if courses:
            save_course_data(courses)
            return render_template('search_courses.html', courses=courses, form=form)
        else:
            flash('Failed to fetch course data', 'error')
            # render the form again with the error message
            return render_template('search_courses.html', form=form)
    return render_template('search_courses.html', form=form)


@app.route('/courses/<int:course_id>')
@login_required
def view_course(course_id):
    try:
        course_details = fetch_course_details(course_id)
        if course_details:
            # Ensure that we are passing the expected data to the template
            return render_template('view_course.html', course=course_details)
        else:
            # If no course details are found, inform the user and redirect
            flash('Course details could not be retrieved.', 'error')
            return redirect(url_for('search_courses_route'))
    except Exception as e:
        # Log the exception and provide a feedback message
        # current_app.logger.error(f"Error retrieving course details: {e}")
        flash('Failed to retrieve course details due to an error.', 'error')
        return redirect(url_for('search_courses_route'))


@app.route('/start_round/<int:course_id>', methods=['GET', 'POST'])
@login_required
def start_round(course_id):
    course_details = fetch_course_details(course_id)
    if request.method == 'POST':
        if not course_details:
            flash('Could not retrieve course details. Please try again.', 'error')
            return render_template('start_round.html', course=None)

        tee_id = request.form['tee_id']
        new_round = Round(golfer_id=current_user.id,
                          course_id=course_id, tee_id=tee_id)
        db.session.add(new_round)
        db.session.commit()
        flash('Round started successfully!', 'success')
        return redirect(url_for('scorecard', round_id=new_round.id))
    else:
        if not course_details:
            flash('Could not retrieve course details. Please try again.', 'error')
            return render_template('start_round.html', course=None)

        return render_template('start_round.html', course=course_details)


@app.route('/scorecard/<int:round_id>', methods=['GET', 'POST'])
@login_required
def scorecard(round_id):
    round = Round.query.get_or_404(round_id)
    view = request.args.get('view', default='current', type=str)
    hole_number = request.args.get('hole', type=int)

    if request.method == 'POST':
        # Handle POST-specific logic here, such as score updates.
        pass

    # This checks and loads the holes based on the selected view
    if view == 'current' and hole_number:
        holes = [Hole.query.get(hole_number)]
    elif view == 'front':
        holes = Hole.query.filter(Hole.course_id == round.course_id).filter(
            Hole.number <= 9).order_by(Hole.number).all()
    elif view == 'back':
        holes = Hole.query.filter(Hole.course_id == round.course_id).filter(
            Hole.number > 9).order_by(Hole.number).all()
    else:
        holes = [Hole.query.get(hole_number)] if hole_number else []

    return render_template('scorecard.html', round=round, holes=holes)


@app.route('/submit_score', methods=['POST'])
@login_required
def submit_score(round_id):
    form = ScoreEntryForm()
    if form.validate_on_submit():
        score = Score(
            round_id=round_id,
            hole_id=form.hole_number.data,
            strokes=form.strokes.data
        )
        db.session.add(score)
        db.session.commit()

        # Check and create milestones after score submission
        check_and_create_milestones(golfer_id=current_user.id, score=score)

        flash('Score submitted successfully!', 'success')
        return redirect(url_for('enter_scores', round_id=round_id))
    return render_template('submit_score.html', form=form, round_id=round_id)


def check_milestones(score, hole):
    golfer_id = score.round.golfer_id
    if score.strokes == 1:
        create_milestone(golfer_id, "Hole-in-One",
                         f"Achieved hole-in-one on hole {hole.number}")

    if (hole.par == 4 and score.strokes == 2) or (hole.par == 5 and score.strokes == 3):
        create_milestone(golfer_id, "Eagle",
                         f"Achieved eagle on hole {hole.number}")

    if hole.par == 5 and score.strokes == 2:
        create_milestone(golfer_id, "Albatross",
                         f"Achieved albatross on hole {hole.number}")

    if hole.par == 4 and score.strokes == 4 and score.bunker_shots >= 2:
        create_milestone(golfer_id, "Double-Sandy",
                         f"Achieved double-sandy on hole {hole.number}")


def create_milestone(golfer_id, type, details):
    date = datetime.utcnow()
    new_milestone = Milestone(
        golfer_id=golfer_id, type=type, details=details, date=date)
    db.session.add(new_milestone)
    db.session.commit()


def check_tournament_win(golfer_id):
    # Placeholder for checking if a golfer won a tournament
    # You would need to implement the logic based on your application's data
    create_milestone(golfer_id, "Tournament Win", "Won a tournament")


@app.route('/complete_round/<int:round_id>', methods=['POST'])
@login_required
def complete_round(round_id):
    round = Round.query.get_or_404(round_id)
    game_type = GameType.query.filter_by(id=round.game_type_id).first()

    # Update leaderboard based on game type rules
    game_type.update_leaderboard(round_id)

    # Update golfer statistics
    statistics = Statistic.query.filter_by(
        golfer_id=round.golfer_id).first()
    if not statistics:
        statistics = Statistic(golfer_id=round.golfer_id)
        db.session.add(statistics)
    statistics.update_statistics(round)

    db.session.commit()
    flash('Round completed and leaderboard updated!', 'success')
    return redirect(url_for('round_details', round_id=round_id))


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
            return redirect(url_for('home'))
    return redirect(url_for('home'))


@app.route('/golfer/<int:golfer_id>/rounds')
def view_golfer_rounds(golfer_id):
    golfer = Golfer.query.get_or_404(golfer_id)
    rounds = golfer.rounds.order_by(Round.date_played.desc()).all()
    return render_template('golfer_rounds.html', golfer=golfer, rounds=rounds)


@app.route('/round_details/<int:round_id>')
def round_details(round_id):
    round = Round.query.get_or_404(round_id)
    total_score = round.total_score()
    average_score = round.average_score_per_hole()
    best_score = round.best_score()
    worst_score = round.worst_score()
    graph_json = round.create_score_chart()
    return render_template('round_details.html', round=round, total_score=total_score,
                           average_score=average_score, best_score=best_score, worst_score=worst_score, graph_json=graph_json)


@app.route('/search_rounds', methods=['GET', 'POST'])
def search_rounds():
    form = SearchRoundsForm()  # Assume this form is defined to accept dates and game type
    if form.validate_on_submit():
        rounds = Round.find_by_golfer_and_date_range(
            golfer_id=current_user.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        return render_template('rounds_search_results.html', rounds=rounds)
    return render_template('search_rounds.html', form=form)


@app.route('/golfer/<int:golfer_id>/profile')
@login_required
def golfer_profile(golfer_id):
    golfer = Golfer.query.get_or_404(golfer_id)
    handicap = fetch_golfer_handicap(golfer.ghin_id)
    return render_template('golfer_profile.html', golfer=golfer, handicap=handicap)


@app.route('/golfer/<int:golfer_id>/trophy_room', methods=['GET'])
@login_required
def golfer_trophy_room(golfer_id):
    golfer = Golfer.query.get_or_404(golfer_id)
    # Ensure that golfer.ghin_id, golfer.last_name, and golfer.state are not None
    if golfer.ghin_id and golfer.last_name and golfer.state:
        handicap = fetch_golfer_handicap(
            golfer.ghin_id, golfer.last_name, golfer.state)
    else:
        handicap = "Not available"  # or handle it as appropriate if any info is missing
    milestones = golfer.milestones
    return render_template('golfer_trophy_room.html', golfer=golfer, milestones=milestones, handicap=handicap)

# Route to record a milestone for a golfer


@app.route('/golfer/<int:golfer_id>/add_milestone', methods=['GET', 'POST'])
@login_required
def add_milestone(golfer_id):
    if request.method == 'POST':
        milestone_type = request.form.get('milestone_type')
        details = request.form.get('details')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        new_milestone = Milestone(
            golfer_id=golfer_id, type=milestone_type, details=details, date=date)
        db.session.add(new_milestone)
        db.session.commit()
        flash('Milestone added successfully!', 'success')
        return redirect(url_for('view_golfer', golfer_id=golfer_id))
    return render_template('add_milestone.html', golfer_id=golfer_id)


@app.route('/golfer/<int:golfer_id>/statistics', methods=['GET', 'POST'])
@login_required
def view_statistics(golfer_id):
    golfer = Golfer.query.get_or_404(golfer_id)
    if request.method == 'POST':
        # Assuming there's a form to update statistics
        golfer.statistics.average_score = request.form['average_score']
        # Update other fields similarly
        db.session.commit()
        flash('Statistics updated successfully!', 'success')
    return render_template('view_statistics.html', golfer=golfer)


if __name__ == '__main__':
    app.run(debug=True)
