from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
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
    course = QuerySelectField('Course', query_factory=lambda: Course.query.all(
    ), get_label='name', allow_blank=False)
    tee = SelectField('Tee', choices=[], coerce=int)  # Allow blank initially
    game_type = QuerySelectField('Game Type', query_factory=lambda: GameType.query.all(
    ), get_label='name', allow_blank=False)
    use_handicap = BooleanField('Use Handicap')
    submit = SubmitField('Start Game')

    def __init__(self, *args, course_id=None, tee_set_id=None, **kwargs):
        super(GameInitiationForm, self).__init__(*args, **kwargs)
        if course_id:
            self.course.data = Course.query.get(course_id)
            # Setting choices for the 'tee' field
            tee_choices = [(tee.id, tee.name)
                           for tee in Tee.query.filter_by(course_id=course_id).all()]
            self.tee.choices = tee_choices  # Set the choices directly
            if tee_set_id:
                self.tee.data = tee_set_id  # Assuming tee_set_id is the ID you want to select


class ProfileForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email()])
    ghin_id = StringField('GHIN ID', validators=[Optional()])
    handicap = IntegerField('Handicap', validators=[Optional()])
    submit = SubmitField('Update Profile')
