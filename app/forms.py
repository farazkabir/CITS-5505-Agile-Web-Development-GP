"""
WTForms form definitions for authentication and profile management.

Each form includes server-side validation; the templates also add matching
client-side validation via ``validation.js``.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class SignUpForm(FlaskForm):
    """New-user registration form with password confirmation and terms consent."""

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
    """Returning-user sign-in form with optional *remember me* flag."""

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


class ProfileForm(FlaskForm):
    """Account settings form for updating display name, bio, and website."""

    display_name = StringField(
        "Display Name",
        validators=[DataRequired(), Length(min=2, max=80)]
    )

    email = StringField(
        "Email Address",
        validators=[DataRequired(), Email()]
    )

    bio = StringField(
        "Bio",
        validators=[Length(max=160)]
    )

    website = StringField(
        "Website",
        validators=[Length(max=255)]
    )

    submit = SubmitField("Save Changes")