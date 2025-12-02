# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class CareerGoalForm(FlaskForm):
    career_goal = SelectField('Career Goal',
                              choices=[
                                  ('Full Stack Developer', 'Full Stack Developer'),
                                  ('Data Scientist', 'Data Scientist'),
                                  ('Mobile App Developer', 'Mobile App Developer'),
                                  ('DevOps Engineer', 'DevOps Engineer'),
                                  ('UI/UX Designer', 'UI/UX Designer'),
                                  ('Machine Learning Engineer', 'Machine Learning Engineer'),
                                  ('Cybersecurity Specialist', 'Cybersecurity Specialist'),
                                  ('Cloud Architect', 'Cloud Architect'),
                                  ('Blockchain Developer', 'Blockchain Developer'),
                                  ('Other', 'Other')
                              ],
                              validators=[DataRequired()])
    submit = SubmitField('Generate Roadmap')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    due_date = DateField('Due Date', format='%Y-%m-%d')
    submit = SubmitField('Add Task')

# app/forms.py - ফাইলের শেষে যোগ করুন
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    career_goal = SelectField('Career Goal',
                              choices=[
                                  ('Full Stack Developer', 'Full Stack Developer'),
                                  ('Data Scientist', 'Data Scientist'),
                                  ('Mobile App Developer', 'Mobile App Developer'),
                                  ('DevOps Engineer', 'DevOps Engineer'),
                                  ('UI/UX Designer', 'UI/UX Designer'),
                                  ('Machine Learning Engineer', 'Machine Learning Engineer'),
                                  ('Cybersecurity Specialist', 'Cybersecurity Specialist'),
                                  ('Cloud Architect', 'Cloud Architect'),
                                  ('Blockchain Developer', 'Blockchain Developer'),
                                  ('Other', 'Other')
                              ])
    about_me = TextAreaField('About Me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Save Changes')