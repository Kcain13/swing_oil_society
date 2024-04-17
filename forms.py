from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from models import db, GameType


def game_type_choices():
    return GameType.query.all()


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6, max=40)])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


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
    game_type = QuerySelectField(
        'Game Type', query_factory=game_type_choices, allow_blank=False, get_label='name')
    use_handicap = BooleanField('Use Handicap')
    submit = SubmitField('Start Game')


class ProfileForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email()])
    handicap = IntegerField('Handicap', validators=[Optional()])
    submit = SubmitField('Update Profile')
