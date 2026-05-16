from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(message="Username is required."),
        Length(min=3, max=64, message="Must be between 3 and 64 characters.")
    ])
    email = StringField("Email", validators=[
        DataRequired(message="Email is required."),
        Email(message="Invalid email address.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Minimum 6 characters.")
    ])
    password2 = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Passwords do not match.")
    ])
    submit = SubmitField("Sign Up")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(message="Please enter your username.")
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Please enter your password.")
    ])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")
