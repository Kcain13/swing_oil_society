from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError, InputRequired, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField

from models import db, GameType, Course, Tee, Golfer


def game_type_choices():
    return GameType.query.all()


class SearchRoundsForm(FlaskForm):
    # Optional: remove if not needed
    golfer_id = StringField('Golfer ID', validators=[Optional()])
    start_date = DateField('Start Date', format='%Y-%m-%d',
                           validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d',
                         validators=[DataRequired()])
    game_type = QuerySelectField('Game Type', query_factory=game_type_choices,
                                 get_label='name', allow_blank=True, blank_text='Any')
    submit = SubmitField('Search Rounds')


class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    ghin_id = StringField('GHIN ID', validators=[DataRequired()])
    state = StringField('State of Residency', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Golfer.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = Golfer.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'That email is already being used. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ScoreEntryForm(FlaskForm):
    hole_number = IntegerField('Hole Number', validators=[DataRequired()])
    strokes = IntegerField('Strokes', validators=[DataRequired()])
    submit = SubmitField('Submit Score')


class GolferSearchForm(FlaskForm):
    golfer_username = StringField(
        'Golfer Username', validators=[DataRequired()])
    submit = SubmitField('Search')


class CourseSearchForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    submit = SubmitField('Search')


class GameInitiationForm(FlaskForm):
    # course = QuerySelectField('Course', query_factory=lambda: Course.query.all(
    # ), get_label='name', allow_blank=False)
    tee = SelectField('Tee', choices=[], coerce=int)  # Allow blank initially
    game_type = QuerySelectField('Game Type', query_factory=lambda: GameType.query.all(
    ), get_label='name', allow_blank=False)
    use_handicap = BooleanField('Use Handicap')
    submit = SubmitField('Start Game')

    def __init__(self, *args, course_id=None, tee_set_id=None, **kwargs):
        super(GameInitiationForm, self).__init__(*args, **kwargs)
        if course_id:
            self.course.data = Course.query.get(course_id)


class HoleEntryForm(FlaskForm):
    # number = IntegerField('Hole Number', validators=[InputRequired()])
    # par = IntegerField('Par', validators=[InputRequired()])
    # length = IntegerField('Length', validators=[InputRequired()])
    # handicap = IntegerField('Handicap', validators=[InputRequired()])
    score = IntegerField('Score', validators=[
                         InputRequired(), NumberRange(min=1, max=15)])
    fairway_hit = BooleanField('Fairway Hit')
    green_in_regulation = BooleanField('Green in Regulation')
    putts = IntegerField('Putts', validators=[
                         InputRequired(), NumberRange(min=0)])
    bunker_shots = IntegerField(
        'Bunker Shots', validators=[NumberRange(min=0)])
    penalties = IntegerField('Penalties', validators=[NumberRange(min=0)])


class ScorecardForm(FlaskForm):
    holes = FieldList(FormField(HoleEntryForm), min_entries=9, max_entries=18)
    submit = SubmitField('Submit Scores')

    def __init__(self, *args, **kwargs):
        super(ScorecardForm, self).__init__(*args, **kwargs)
        if 'hole_data' in kwargs:
            self.holes = []
            for data in kwargs['hole_data']:
                hole_form = HoleEntryForm(data=data)
                self.holes.append_entry(hole_form)


class ProfileForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email()])
    ghin_id = StringField('GHIN ID', validators=[Optional()])
    handicap = IntegerField('Handicap', validators=[Optional()])
    submit = SubmitField('Update Profile')
