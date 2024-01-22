from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, EmailField, BooleanField, MultipleFileField, \
    DateField, SelectField, DateTimeField, FormField
from wtforms.validators import DataRequired, URL


class LoginForm(FlaskForm):
    email = StringField("Email-ID", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    email = StringField("Email-ID", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Your Name", validators=[DataRequired()])
    employeeId = StringField("Employee ID", validators=[DataRequired()])
    mobile = PasswordField("Mobile", validators=[DataRequired()])
    designation = StringField("Designation", validators=[DataRequired()])
    submit = SubmitField("Register")