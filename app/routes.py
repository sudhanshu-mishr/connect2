from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Swipe, Match, Message
from app.forms import LoginForm, RegistrationForm

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/api/users')
@login_required
def get_users():
    # Get users that current user hasn't swiped on yet
    swiped_ids = [swipe.swiped_id for swipe in current_user.swipes_made.all()]
    swiped_ids.append(current_user.id)
    users = User.query.filter(User.id.notin_(swiped_ids)).limit(10).all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'bio': user.bio,
        'image_url': user.image_url or 'https://via.placeholder.com/300x400'
    } for user in users])

@bp.route('/api/swipe', methods=['POST'])
@login_required
def swipe():
    data = request.get_json()
    swiped_id = data.get('swiped_id')
    is_like = data.get('is_like')

    if not swiped_id or is_like is None:
        return jsonify({'error': 'Invalid data'}), 400

    swipe = Swipe(swiper_id=current_user.id, swiped_id=swiped_id, is_like=is_like)
    db.session.add(swipe)

    match_found = False
    if is_like:
        # Check if the other user also liked the current user
        other_swipe = Swipe.query.filter_by(swiper_id=swiped_id, swiped_id=current_user.id, is_like=True).first()
        if other_swipe:
            match = Match(user1_id=current_user.id, user2_id=swiped_id)
            db.session.add(match)
            match_found = True

    db.session.commit()
    return jsonify({'success': True, 'match': match_found})

@bp.route('/api/matches')
@login_required
def get_matches():
    matches1 = current_user.matches_as_user1.all()
    matches2 = current_user.matches_as_user2.all()
    matches = matches1 + matches2

    result = []
    for match in matches:
        other_user = match.user2 if match.user1_id == current_user.id else match.user1
        result.append({
            'match_id': match.id,
            'user': {
                'id': other_user.id,
                'username': other_user.username,
                'image_url': other_user.image_url or 'https://via.placeholder.com/50'
            }
        })
    return jsonify(result)
