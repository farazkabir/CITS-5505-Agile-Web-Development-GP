from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class SignUpForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(min=2, max=80)]
    )

    email = StringField(
        "Email address",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8)]
    )

    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password")]
    )

    terms = BooleanField(
        "I agree to the community guidelines",
        validators=[DataRequired()]
    )

    submit = SubmitField("Sign up")


class SignInForm(FlaskForm):
    email = StringField(
        "Email address",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    remember = BooleanField("Remember me")

    submit = SubmitField("Sign in")