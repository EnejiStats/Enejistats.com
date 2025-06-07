from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, DateField,
    IntegerField, SelectField, BooleanField, FileField, TextAreaField
)
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange

class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')

class PlayerRegistrationForm(FlaskForm):
    first_name    = StringField('First Name', validators=[DataRequired()])
    middle_name   = StringField('Middle Name', validators=[Optional()])
    last_name     = StringField('Last Name', validators=[DataRequired()])
    dob           = DateField('Date of Birth', validators=[DataRequired()])
    nationality   = StringField('Nationality', validators=[DataRequired()])
    gender        = SelectField('Gender', choices=[('male','Male'), ('female','Female'), ('other','Other')])
    dominant_foot = SelectField('Dominant Foot', choices=[('left','Left'), ('right','Right'), ('both', 'Both')])
    weak_foot_pct = IntegerField('Weak Foot %', validators=[DataRequired(), NumberRange(min=0, max=100)])
    height_cm     = IntegerField('Height (cm)', validators=[Optional()])
    weight_kg     = IntegerField('Weight (kg)', validators=[Optional()])
    photo         = FileField('Passport Photo')
    club_id       = SelectField('Club (if contract)', coerce=int)
    submit        = SubmitField('Register Player')

class ClubRegistrationForm(FlaskForm):
    name         = StringField('Club Name', validators=[DataRequired()])
    founded      = DateField('Established', validators=[DataRequired()])
    nationality  = StringField('Nationality', validators=[DataRequired()])
    badge        = FileField('Badge')
    email        = StringField('Public Email', validators=[Optional(), Email()])
    phone        = StringField('Public Phone', validators=[Optional(), Length(max=40)])
    hide_contact = BooleanField('Hide Contact Details', default=True)
    submit       = SubmitField('Register Club')

class ScoutRegistrationForm(FlaskForm):
    full_name    = StringField('Full Name', validators=[DataRequired()])
    nationality  = StringField('Nationality', validators=[DataRequired()])
    photo        = FileField('Passport Photo')
    email        = StringField('Email', validators=[Optional(), Email()])
    phone        = StringField('Phone', validators=[Optional(), Length(max=40)])
    hide_contact = BooleanField('Hide Contact Details', default=True)
    submit       = SubmitField('Register Scout')

class ScoutingReportForm(FlaskForm):
    player_id = SelectField('Player', coerce=int, validators=[DataRequired()])
    notes     = TextAreaField('Observations', validators=[Optional()])
    rating    = IntegerField('Rating (1–10)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    submit    = SubmitField('Submit Report')

class PlayerClubHistoryForm(FlaskForm):
    player_id  = SelectField('Player', coerce=int, validators=[DataRequired()])
    club_id    = SelectField('Club', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date   = DateField('End Date', validators=[Optional()])
    submit     = SubmitField('Add History')
