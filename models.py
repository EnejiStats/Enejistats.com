from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint, UniqueConstraint, Enum as SAEnum, Index
import enum

db = SQLAlchemy()

class RoleEnum(enum.Enum):
    CTO = "cto"
    ADMIN = "admin"
    SCOUT = "scout"

class GenderEnum(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class FootEnum(enum.Enum):
    LEFT = "Left"
    RIGHT = "Right"
    BOTH = "Both"

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    founded = db.Column(db.Date)
    nationality = db.Column(db.String(60))
    badge_url = db.Column(db.String(250))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    hide_contact = db.Column(db.Boolean, default=True)
    players = db.relationship('PlayerProfile', back_populates='club')
    history = db.relationship('PlayerClubHistory', back_populates='club', cascade="all, delete-orphan")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(SAEnum(RoleEnum), default=RoleEnum.SCOUT, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scout = db.relationship('ScoutProfile', uselist=False, back_populates='user')

class ScoutProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    nationality = db.Column(db.String(60))
    photo_url = db.Column(db.String(250))
    phone = db.Column(db.String(40))
    hide_contact = db.Column(db.Boolean, default=True)
    user = db.relationship('User', back_populates='scout')
    reports = db.relationship('ScoutingReport', back_populates='scout', cascade="all, delete-orphan")

class PlayerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    middle_name = db.Column(db.String(60))
    last_name = db.Column(db.String(60), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    nationality = db.Column(db.String(60))
    gender = db.Column(SAEnum(GenderEnum))
    dominant_foot = db.Column(SAEnum(FootEnum))
    weak_foot_pct = db.Column(db.Integer)
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Integer)
    photo_url = db.Column(db.String(250))
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'))
    club = db.relationship('Club', back_populates='players')
    stats = db.relationship('PlayerMatchStat', back_populates='player', cascade="all, delete-orphan")
    history = db.relationship('PlayerClubHistory', back_populates='player', cascade="all, delete-orphan")
    reports = db.relationship('ScoutingReport', back_populates='player', cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('weak_foot_pct BETWEEN 0 AND 100', name='ck_weak_foot_pct'),
        Index('ix_player_last_name', 'last_name'),
    )

class PlayerClubHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    player = db.relationship('PlayerProfile', back_populates='history')
    club = db.relationship('Club', back_populates='history')

    __table_args__ = (
        UniqueConstraint('player_id', 'club_id', 'start_date', name='uq_club_history'),
    )

class ScoutingReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scout_id = db.Column(db.Integer, db.ForeignKey('scout_profile.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    scout = db.relationship('ScoutProfile', back_populates='reports')
    player = db.relationship('PlayerProfile', back_populates='reports')

    __table_args__ = (
        UniqueConstraint('scout_id', 'player_id', 'date_created', name='uq_scouting_entry'),
    )

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time)
    venue = db.Column(db.String(120))
    home_team = db.Column(db.String(120))
    away_team = db.Column(db.String(120))
    score_home = db.Column(db.Integer)
    score_away = db.Column(db.Integer)
    player_stats = db.relationship('PlayerMatchStat', back_populates='match', cascade="all, delete-orphan")
    team_stats = db.relationship('TeamMatchStat', back_populates='match', cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_match_date', 'date'),
    )

class PlayerMatchStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player_profile.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    minutes = db.Column(db.Integer)
    short_pass_succ = db.Column(db.Integer)
    short_pass_fail = db.Column(db.Integer)
    long_pass_succ = db.Column(db.Integer)
    long_pass_fail = db.Column(db.Integer)
    dribbles_succ = db.Column(db.Integer)
    dribbles_fail = db.Column(db.Integer)
    shots_on = db.Column(db.Integer)
    shots_off = db.Column(db.Integer)
    clearances = db.Column(db.Integer)
    aerial_won = db.Column(db.Integer)
    aerial_lost = db.Column(db.Integer)
    fouls_for = db.Column(db.Integer)
    fouls_against = db.Column(db.Integer)
    yellow = db.Column(db.Integer)
    red = db.Column(db.Integer)
    saves = db.Column(db.Integer)
    player = db.relationship('PlayerProfile', back_populates='stats')
    match = db.relationship('Match', back_populates='player_stats')

    __table_args__ = (
        UniqueConstraint('player_id', 'match_id', name='uq_player_match'),
        CheckConstraint('minutes BETWEEN 0 AND 120', name='ck_valid_minutes'),
    )

class TeamMatchStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    team_name = db.Column(db.String(120), nullable=False)
    short_pass_succ = db.Column(db.Integer)
    short_pass_fail = db.Column(db.Integer)
    long_pass_succ = db.Column(db.Integer)
    long_pass_fail = db.Column(db.Integer)
    dribbles_succ = db.Column(db.Integer)
    dribbles_fail = db.Column(db.Integer)
    shots_on = db.Column(db.Integer)
    shots_off = db.Column(db.Integer)
    clearances = db.Column(db.Integer)
    aerial_won = db.Column(db.Integer)
    aerial_lost = db.Column(db.Integer)
    fouls_for = db.Column(db.Integer)
    fouls_against = db.Column(db.Integer)
    yellow = db.Column(db.Integer)
    red = db.Column(db.Integer)
    saves = db.Column(db.Integer)
    match = db.relationship('Match', back_populates='team_stats')

    __table_args__ = (
        UniqueConstraint('team_name', 'match_id', name='uq_team_match'),
  )
