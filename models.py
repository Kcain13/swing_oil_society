from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import plotly
import plotly.express as px
import json
from flask_login import UserMixin

import bcrypt


db = SQLAlchemy()


class APIToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)

    @classmethod
    def get_current_token(cls):
        # This retrieves the most recent token that hasn't expired.
        now = datetime.utcnow()
        return cls.query.filter(cls.expiry > now).order_by(cls.expiry.desc()).first()


class Golfer(db.Model, UserMixin):
    __tablename__ = 'golfers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    ghin_id = db.Column(db.Integer, unique=True, nullable=True)
    state = db.Column(db.String(120), nullable=False)
    statistics = db.relationship(
        'Statistic', back_populates='golfer', uselist=False, lazy='select')
    milestones = db.relationship('Milestone', backref='golfer', lazy='select')

    def set_password(self, password):
        """Create hashed password."""
        password_bytes = password.encode('utf-8')
        self.password_hash = bcrypt.hashpw(
            password_bytes, bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Check hashed password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        # You can add logic to deactivate users
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)  # python 3 support

    def __repr__(self):
        return f'<User {self.username}>'


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    facility_id = db.Column(db.Integer)
    facility_name = db.Column(db.String(255))
    full_name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    updated_on = db.Column(db.DateTime)
    tees = db.relationship('Tee',
                           lazy='dynamic', back_populates='course', cascade="all, delete-orphan")


class Tee(db.Model):
    __tablename__ = 'tees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    yardage = db.Column(db.Integer)
    course = db.relationship('Course', back_populates='tees')
    holes = db.relationship('Hole', backref='tee',
                            lazy='dynamic', cascade="all, delete-orphan")


class Hole(db.Model):
    __tablename__ = 'holes'
    hole_id = db.Column(db.Integer, primary_key=True)
    # This is the ID from the API
    api_hole_id = db.Column(db.Integer, unique=True)
    tee_id = db.Column(db.Integer, db.ForeignKey('tees.id'))
    number = db.Column(db.Integer)
    par = db.Column(db.Integer)
    yardage = db.Column(db.Integer)  # Yardage for the hole
    handicap = db.Column(db.Integer)  # Handicap for the hole

    def __repr__(self):
        return f'<Hole {self.number}, Par {self.par}, Yardage {self.yardage}, Handicap {self.handicap}>'

    @classmethod
    def find_by_golfer_and_date_range(cls, golfer_id, start_date, end_date):
        return cls.query.filter(
            cls.golfer_id == golfer_id,
            cls.date_played >= start_date,
            cls.date_played <= end_date
        ).all()

    @classmethod
    def find_by_golfer_and_game_type(cls, golfer_id, game_type_id):
        return cls.query.filter_by(
            golfer_id=golfer_id,
            game_type_id=game_type_id
        ).all()


class Round(db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    date_played = db.Column(db.DateTime, default=datetime.utcnow)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfers.id'))
    course_id = db.Column(db.Integer)
    tee_id = db.Column(db.Integer)
    game_type_id = db.Column(db.Integer, db.ForeignKey('game_types.id'))
    use_handicap = db.Column(db.Boolean, default=False)
    scores = db.relationship('Score', backref='round', lazy='dynamic')
    golfer = db.relationship('Golfer', backref='rounds')
    # course = db.relationship('Course', backref='rounds')
    game_type = db.relationship('GameType', back_populates='rounds')

    def __repr__(self):
        return f'<Round on {self.date_played.strftime("%Y-%m-%d")} by Golfer {self.golfer_id}>'

    def total_score(self):
        return sum(score.score for score in self.scores.all())

    def fairway_hits_percentage(self):
        fairway_hits = sum(1 for score in self.scores if score.fairway_hit)
        return (fairway_hits / len(self.scores)) * 100 if self.scores else 0

    def average_score_per_hole(self):
        """Calculate the average score per hole for the round."""
        total_scores = self.total_score()
        num_holes = self.scores.count()
        return total_scores / num_holes if num_holes else None

    def best_score(self):
        """Find the best (lowest) score of the round."""
        return min((score.score for score in self.scores.all()), default=None)

    def worst_score(self):
        """Find the worst (highest) score of the round."""
        return max((score.score for score in self.scores.all()), default=None)

    def calculate_round_statistics(self):
        scores = self.scores.all()  # Ensure you fetch scores only once per function call
        total_score = sum(score.score for score in scores)
        first_nine_score = sum(
            score.score for score in scores if score.hole_number <= 9)
        last_nine_score = sum(
            score.score for score in scores if score.hole_number > 9)
        total_putts = sum(score.putts for score in scores)
        total_penalties = sum(score.penalties for score in scores)
        total_bunker_shots = sum(score.bunker_shots for score in scores)
        num_scores = len(scores)

        fairways_hit = sum(1 for score in scores if score.fairway_hit)
        greens_in_regulation = sum(
            1 for score in scores if score.green_in_regulation)

        statistics = {
            'total_score': total_score,
            'first_nine_score': first_nine_score,
            'last_nine_score': last_nine_score,
            'total_putts': total_putts,
            'fairways_hit_ratio': f"{fairways_hit}/{num_scores}",
            'greens_in_regulation_ratio': f"{greens_in_regulation}/{num_scores}",
            'total_penalties': total_penalties,
            'total_bunker_shots': total_bunker_shots,
        }

        return statistics

    def create_score_chart(self):
        scores = self.scores.order_by('hole_number').all()

        # Calculate average scores by par type, making sure to handle division by zero
        par3_scores = [s.score for s in scores if s.hole_par == 3]
        par4_scores = [s.score for s in scores if s.hole_par == 4]
        par5_scores = [s.score for s in scores if s.hole_par == 5]

        par3_avg = sum(par3_scores) / len(par3_scores) if par3_scores else 0
        par4_avg = sum(par4_scores) / len(par4_scores) if par4_scores else 0
        par5_avg = sum(par5_scores) / len(par5_scores) if par5_scores else 0

        # Create bar chart for average scores by par
        fig = px.bar(
            x=['Par 3', 'Par 4', 'Par 5'],
            y=[par3_avg, par4_avg, par5_avg],
            labels={'x': 'Hole Par', 'y': 'Average Score'},
            title="Average Scores by Hole Par"
        )
        fig.update_layout(
            xaxis_title="Hole Par",
            yaxis_title="Average Score",
            title="Average Score by Hole Par"
        )

        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graph_json


class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    # hole_id = db.Column(db.Integer, db.ForeignKey('holes.api_hole_id'))
    hole_number = db.Column(db.Integer)
    hole_par = db.Column(db.Integer)
    hole_handicap = db.Column(db.Integer)
    yardage = db.Column(db.Integer)
    score = db.Column(db.Integer)
    fairway_hit = db.Column(db.Boolean, default=False)
    green_in_regulation = db.Column(db.Boolean, default=False)
    putts = db.Column(db.Integer)
    bunker_shots = db.Column(db.Integer)
    penalties = db.Column(db.Integer)

    def is_fairway_hit(self):
        return self.fairway_hit

    def is_green_in_regulation(self):
        return self.green_in_regulation


class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.Integer, primary_key=True)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfers.id'))
    type = db.Column(db.String(50))
    date = db.Column(db.Date)
    details = db.Column(db.String(255))

    @staticmethod
    def create(golfer_id, type, details):
        date = datetime.utcnow()
        new_milestone = Milestone(
            golfer_id=golfer_id, type=type, details=details, date=date)
        db.session.add(new_milestone)
        db.session.commit()


class Statistic(db.Model):
    __tablename__ = 'statistics'
    id = db.Column(db.Integer, primary_key=True)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfers.id'))
    average_score = db.Column(db.Float)
    fairway_hit_percentage = db.Column(db.Float)
    green_in_regulation_percentage = db.Column(db.Float)
    putts_per_round = db.Column(db.Float)
    total_rounds_played = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    total_losses = db.Column(db.Integer, default=0)
    golfer = db.relationship('Golfer', back_populates='statistics')
    birdies = db.Column(db.Integer, default=0)
    pars = db.Column(db.Integer, default=0)
    bogeys = db.Column(db.Integer, default=0)
    double_bogeys = db.Column(db.Integer, default=0)

    def update(self, score):
        hole = Hole.query.get(score.hole_id)
        self.total_rounds_played += 1
        if score.strokes == hole.par - 1:
            self.birdies += 1
        elif score.strokes == hole.par:
            self.pars += 1
        elif score.strokes == hole.par + 1:
            self.bogeys += 1
        elif score.strokes == hole.par + 2:
            self.double_bogeys += 1
        db.session.commit()


def check_and_create_milestones(score):
    hole = Hole.query.get(score.hole_id)
    golfer_id = score.round.golfer_id
    # Milestone checks...
    if score.strokes == 1:
        Milestone.create(golfer_id, "Hole-in-One",
                         f"Achieved hole-in-one on hole {hole.number}")

    if (hole.par == 4 and score.strokes == 2) or (hole.par == 5 and score.strokes == 3):
        Milestone.create(golfer_id, "Eagle",
                         f"Achieved eagle on hole {hole.number}")

    if hole.par == 5 and score.strokes == 2:
        Milestone.create(golfer_id, "Albatross",
                         f"Achieved albatross on hole {hole.number}")

    if hole.par == 4 and score.strokes == 4 and score.bunker_shots >= 2:
        Milestone.create(golfer_id, "Double-Sandy",
                         f"Achieved double-sandy on hole {hole.number}")


class GameType(db.Model):
    __tablename__ = 'game_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    # Detailed rules or settings for the game type
    rules = db.Column(db.Text, nullable=True)

    rounds = db.relationship('Round', back_populates='game_type')

    def __repr__(self):
        return f'<GameType {self.name}>'

    def update_leaderboard(self, round_id):
        round = Round.query.get(round_id)
        scores = Score.query.filter_by(round_id=round_id).all()
        # Implement logic to update the leaderboard based on this game type's rules
        if self.name == "Match Play":
            self.process_match_play(scores)
        elif self.name == "Stroke Play":
            self.process_stroke_play(scores)
        elif self.name == "Tournament Play":
            self.process_tournament_play(round.golfer_id)
        elif self.name == "Solo Play":
            self.process_solo_play(round)
        # Add other game types as needed

    def process_match_play(self, scores):
        # Logic to process scores in match play
        # Update points and determine match outcomes
        # Assuming scores are organized by hole and golfer
        golfer_scores = {score.golfer_id: 0 for score in scores}
        for hole_number in range(1, 19):  # Typical 18 holes
            hole_scores = {
                score.golfer_id: score.strokes for score in scores if score.hole_number == hole_number}
            min_strokes = min(hole_scores.values())
            for golfer_id, strokes in hole_scores.items():
                if strokes == min_strokes and list(hole_scores.values()).count(min_strokes) == 1:
                    golfer_scores[golfer_id] += 1

        # Update leaderboard
        for golfer_id, points in golfer_scores.items():
            leaderboard_entry = Leaderboard.query.filter_by(
                golfer_id=golfer_id, game_type_id=self.id).first()
            if not leaderboard_entry:
                leaderboard_entry = Leaderboard(
                    golfer_id=golfer_id, game_type_id=self.id, score=points)
                db.session.add(leaderboard_entry)
            else:
                leaderboard_entry.score += points
            db.session.commit()

    def process_stroke_play(self, scores):
        # Aggregate scores by golfer
        golfer_scores = {}
        for score in scores:
            if score.golfer_id not in golfer_scores:
                golfer_scores[score.golfer_id] = 0
            golfer_scores[score.golfer_id] += score.strokes

        # Update leaderboard
        for golfer_id, total_score in golfer_scores.items():
            leaderboard_entry = Leaderboard.query.filter_by(
                golfer_id=golfer_id, game_type_id=self.id).first()
            if not leaderboard_entry:
                leaderboard_entry = Leaderboard(
                    golfer_id=golfer_id, game_type_id=self.id, score=total_score)
                db.session.add(leaderboard_entry)
            else:
                leaderboard_entry.score = total_score
            db.session.commit()

    def process_tournament_play(self, golfer_id):
        # Assume the tournament lasts 4 rounds, calculate cumulative score
        rounds = Round.query.filter_by(
            golfer_id=golfer_id, game_type_id=self.id).limit(4).all()
        # total_score() needs to be defined in Round model
        total_score = sum(round.total_score() for round in rounds)
        leaderboard_entry = Leaderboard.query.filter_by(
            golfer_id=golfer_id, game_type_id=self.id).first()
        if not leaderboard_entry:
            leaderboard_entry = Leaderboard(
                golfer_id=golfer_id, game_type_id=self.id, score=total_score)
            db.session.add(leaderboard_entry)
        else:
            leaderboard_entry.score = total_score  # Update the total score
        db.session.commit()

    def process_solo_play(self, round):
        # Calculate the total score for the round and possibly update golfer statistics directly.
        total_score = round.total_score()

        # Check if statistics exist for the golfer and update them.
        statistics = Statistic.query.filter_by(
            golfer_id=round.golfer_id).first()
        if not statistics:
            statistics = Statistic(
                golfer_id=round.golfer_id,
                average_score=total_score,  # Initialize with the score of this round
                total_rounds_played=1,  # This is their first recorded round
                average_strokes_per_round=total_score  # Same as average score initially
            )
            db.session.add(statistics)
        else:
            # Update the existing statistics.
            rounds_played = statistics.total_rounds_played + 1
            statistics.average_score = (
                (statistics.average_score * statistics.total_rounds_played) + total_score) / rounds_played
            statistics.average_strokes_per_round = (
                (statistics.average_strokes_per_round * statistics.total_rounds_played) + total_score) / rounds_played
            statistics.total_rounds_played = rounds_played

        db.session.commit()


# class ScoreDetail(db.Model):
#     __tablename__ = 'score_details'
#     id = db.Column(db.Integer, primary_key=True)
#     round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
#     hole_id = db.Column(db.Integer, db.ForeignKey('holes.id'))
#     score = db.Column(db.Integer)
#     fairway_hit = db.Column(db.Boolean)
#     green_in_regulation = db.Column(db.Boolean)
#     putts = db.Column(db.Integer)
#     bunker_shots = db.Column(db.Integer)
#     penalties = db.Column(db.Integer)


class Leaderboard(db.Model):
    __tablename__ = 'leaderboards'
    id = db.Column(db.Integer, primary_key=True)
    golfer_id = db.Column(db.Integer, db.ForeignKey('golfers.id'))
    game_type_id = db.Column(db.Integer, db.ForeignKey('game_types.id'))
    score = db.Column(db.Integer)
    position = db.Column(db.Integer, nullable=True)

    golfer = db.relationship('Golfer', backref='leaderboard_entries')
    game_type = db.relationship('GameType', backref='leaderboard_entries')

    def __repr__(self):
        return f'<Leaderboard #{self.id}: Golfer {self.golfer_id} - GameType {self.game_type_id} - Score {self.score}>'


def connect_db(app):
    """Connect to database with the Flask app."""
    app.app_context().push()
    db.app = app
    db.init_app(app)
