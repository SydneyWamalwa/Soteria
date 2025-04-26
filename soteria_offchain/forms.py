from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class EcoActionForm(FlaskForm):
    description = TextAreaField('Action Description', validators=[DataRequired()])
    points = FloatField('Points Earned', validators=[DataRequired()])
    submit = SubmitField('Log Action')

class LoginForm(FlaskForm):  # <-- added
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')