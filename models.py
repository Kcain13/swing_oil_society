from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Golfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    statistics = db.relationship(
        'Statistic', back_populates='golfer', uselist=False)
    milestones = db.relationship('Milestone', backref='golfer')


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))


class Tee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    holes = db.relationship('Hole', backref='tee')


class Hole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tee_id = db.Column(db.Integer, db.ForeignKey('tee.id'))
    par = db.Column(db.Integer)


class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_played = db.Column(db.DateTime, default=datetime.utcnow)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfer.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    scores = db.relationship('Score', backref='round')


class GameType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Names like "Match Play", "Stroke Play", "Tournament Play"
    name = db.Column(db.String(50))
    # A brief description of the game type
    description = db.Column(db.String(255))


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    hole_id = db.Column(db.Integer, db.ForeignKey('hole.id'))
    strokes = db.Column(db.Integer)


class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfer.id'))
    type = db.Column(db.String(50))
    date = db.Column(db.Date)
    details = db.Column(db.String(255))


class Statistic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfer.id'))
    average_score = db.Column(db.Float)
    fairway_hit_percentage = db.Column(db.Float)
    green_in_regulation_percentage = db.Column(db.Float)
    putts_per_round = db.Column(db.Float)
    golfer = db.relationship('Golfer', back_populates='statistics')
