# app/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Roadmap, Task, Progress
from app.forms import LoginForm, RegistrationForm, CareerGoalForm, TaskForm, EditProfileForm
from datetime import datetime
import google.generativeai as genai
import os
from config import Config

# Gemini API কনফিগার করুন
genai.configure(api_key=Config.GEMINI_API_KEY)

bp = Blueprint('app', __name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('app.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('app.index'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('app.dashboard'))
    return render_template('index.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('app.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('app.index'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('app.index'))


@bp.route('/dashboard')
@login_required
def dashboard():
    # Get user's tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    # Get user's progress
    progress = Progress.query.filter_by(user_id=current_user.id).all()

    # Get user's roadmap if exists
    roadmap = Roadmap.query.filter_by(user_id=current_user.id).first()

    return render_template('dashboard.html', title='Dashboard', tasks=tasks, progress=progress, roadmap=roadmap)


@bp.route('/career_goal', methods=['GET', 'POST'])
@login_required
def career_goal():
    form = CareerGoalForm()
    if form.validate_on_submit():
        # Update user's career goal
        current_user.career_goal = form.career_goal.data
        db.session.commit()

        # Generate AI roadmap
        roadmap_content = generate_roadmap(form.career_goal.data)

        # Save roadmap to database
        # প্রথমে চেক করুন ইউজারের আগে থেকে কোনো রোডম্যাপ আছে কিনা
        existing_roadmap = Roadmap.query.filter_by(user_id=current_user.id).first()
        if existing_roadmap:
            # আগের রোডম্যাপটি আপডেট করুন
            existing_roadmap.title = f"{form.career_goal.data} Roadmap"
            existing_roadmap.content = roadmap_content
            db.session.commit()
            roadmap_id = existing_roadmap.id
        else:
            # নতুন রোডম্যাপ তৈরি করুন
            roadmap = Roadmap(
                title=f"{form.career_goal.data} Roadmap",
                content=roadmap_content,
                user_id=current_user.id
            )
            db.session.add(roadmap)
            db.session.commit()
            roadmap_id = roadmap.id

        flash('Your career roadmap has been generated!')
        return redirect(url_for('app.roadmap', roadmap_id=roadmap_id))

    return render_template('career_goal.html', title='Set Career Goal', form=form)


@bp.route('/roadmap/<int:roadmap_id>')
@login_required
def roadmap(roadmap_id):
    roadmap = Roadmap.query.get_or_404(roadmap_id)
    if roadmap.user_id != current_user.id:
        flash('You can only view your own roadmaps.')
        return redirect(url_for('app.dashboard'))

    return render_template('roadmap.html', title='Career Roadmap', roadmap=roadmap)


@bp.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added successfully!')
        return redirect(url_for('app.dashboard'))

    return render_template('add_task.html', title='Add Task', form=form)


@bp.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You can only complete your own tasks.')
        return redirect(url_for('app.dashboard'))

    task.completed = True
    db.session.commit()
    flash('Task marked as completed!')
    return redirect(url_for('app.dashboard'))


@bp.route('/ai_mentor', methods=['GET', 'POST'])
@login_required
def ai_mentor():
    if request.method == 'POST':
        user_message = request.form.get('message')
        if not user_message:
            return jsonify({'response': 'Please ask a question.'})

        ai_response = get_ai_mentor_response(user_message, current_user.career_goal)
        return jsonify({'response': ai_response})

    return render_template('ai_mentor.html', title='AI Mentor')


@bp.route('/update_progress', methods=['GET', 'POST'])
@login_required
def update_progress():
    if request.method == 'POST':
        skill = request.form.get('skill')
        level = int(request.form.get('level'))
        notes = request.form.get('notes')

        # Check if progress for this skill already exists
        progress = Progress.query.filter_by(user_id=current_user.id, skill=skill).first()

        if progress:
            progress.level = level
            progress.notes = notes
        else:
            progress = Progress(
                skill=skill,
                level=level,
                notes=notes,
                user_id=current_user.id
            )
            db.session.add(progress)

        db.session.commit()
        flash('Your progress has been updated!')
        return redirect(url_for('app.dashboard'))

    return render_template('update_progress.html', title='Update Progress')


@bp.route('/profile')
@login_required
def profile():
    # Get user's data for the profile page
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    progress = Progress.query.filter_by(user_id=current_user.id).all()
    roadmaps = Roadmap.query.filter_by(user_id=current_user.id).all()

    return render_template('profile.html', title='Profile', tasks=tasks, progress=progress, roadmaps=roadmaps)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.career_goal = form.career_goal.data
        # about_me field যোগ করতে হলে models.py এ User মডেলে যোগ করতে হবে
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('app.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.career_goal.data = current_user.career_goal or 'Full Stack Developer'
    return render_template('edit_profile.html', title='Edit Profile', form=form)


# --- Helper Functions for Gemini API ---

def generate_roadmap(career_goal):
    """Generate a career roadmap using Gemini Flash API"""
    try:
        # মডেল সিলেক্ট করুন - gemini-1.5-flash হলো ফ্রি API এর জন্য
        model = genai.GenerativeModel('gemini-1.5-flash')

        # প্রম্পট তৈরি করুন
        prompt = f"Generate a detailed learning roadmap for someone who wants to become a {career_goal}. Include specific skills, resources, and timeline. Format the response in markdown with clear sections."

        # Gemini API তে রিকোয়েস্ট পাঠান
        response = model.generate_content(prompt)

        # রেসপন্স থেকে টেক্সট বের করুন
        return response.text
    except Exception as e:
        return f"Error generating roadmap: {str(e)}. Please check your Gemini API key and try again."


def get_ai_mentor_response(message, career_goal):
    """Get AI mentor response using Gemini Flash API"""
    try:
        # যদি ব্যবহারকারীর ক্যারিয়ার গোল না থাকে, তাহলে একটি ডিফল্ট গোল সেট করুন
        if not career_goal:
            career_goal = "a professional"

        # মডেল সিলেক্ট করুন - gemini-1.5-flash হলো ফ্রি API এর জন্য
        model = genai.GenerativeModel('gemini-1.5-flash')

        # প্রম্পট তৈরি করুন
        prompt = f"As a career mentor for someone who wants to become a {career_goal}, respond to the following question in a helpful and encouraging way: {message}"

        # Gemini API তে রিকোয়েস্ট পাঠান
        response = model.generate_content(prompt)

        # রেসপন্স থেকে টেক্সট বের করুন
        return response.text
    except Exception as e:
        return f"Sorry, I'm having trouble connecting right now. Please try again later. Error: {str(e)}"