from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from app import db
from app.models import Post, User,followers

profile_bp = Blueprint('profile', __name__)
# app/routes/profile.py
from flask import request

@profile_bp.route('/profile')
@login_required
def profile():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=current_user).order_by(Post.created_at.desc()).paginate(page=page, per_page=3)
    return render_template('profile/profile.html', title='Profile', posts=posts)

@profile_bp.route('/profile/<string:username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    Followingcheck = current_user.is_following(user)
    return render_template('profile/profile.html', title=f'{username}\'s Profile', user=user, posts=posts,Followingcheck=Followingcheck)


import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/profile/upload_picture', methods=['POST'])
@login_required
def upload_picture():
    file = request.files.get('image_file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1]
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.root_path, 'static/img', unique_filename)
        file.save(filepath)

        # Remove old profile picture if it's not default
        if current_user.image_file != 'default.png':
            old_path = os.path.join(current_app.root_path, 'static/img', current_user.image_file)
            if os.path.exists(old_path):
                os.remove(old_path)

        current_user.image_file = unique_filename
        db.session.commit()
        flash('Profile picture updated successfully!', 'success')
    else:
        flash('Invalid file type. Please upload an image.', 'danger')

    return redirect(url_for('profile.profile'))

@profile_bp.route('/remove_picture', methods=['POST'])
@login_required
def remove_picture():
    if current_user.image_file != 'default.png':
        try:
            os.remove(os.path.join(current_app.root_path, 'static/img', current_user.image_file))
        except Exception:
            flash('Failed to delete image.', 'danger')
        current_user.image_file = 'default.png'
        db.session.commit()
        flash('Profile picture removed.', 'info')
    return redirect(url_for('profile.profile'))


@profile_bp.route('/follow/<string:username>', methods=['POST', 'GET'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash('You cannot follow yourself.', 'warning')
        return redirect(url_for('profile.user_profile', username=username))
    if not current_user.is_following(user):
        current_user.follow(user)
        db.session.commit()
        flash(f'You are now following {user.username}!', 'success')
    else:
        flash(f'You are already following {user.username}.', 'info')
    return redirect(url_for('profile.user_profile', username=username))

@profile_bp.route('/unfollow/<string:username>', methods=['POST', 'GET'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash('You cannot unfollow yourself.', 'warning')
        return redirect(url_for('profile.user_profile', username=username))
    if current_user.is_following(user):
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You have unfollowed {user.username}.', 'info')
    else:
        flash(f'You are not following {user.username}.', 'info')
    return redirect(url_for('profile.user_profile', username=username))

@profile_bp.route('/followers')
@login_required
def follower_list():
    users = current_user.followers.all()
    title = "Followers"
    return render_template('profile/follow_list.html', users=users, title=title)

@profile_bp.route('/<string:username>/followers')
@login_required
def user_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = user.followers.all()
    title = f"{username}'s Followers"
    return render_template('profile/follow_list.html', users=users, title=title)

@profile_bp.route('/following')
@login_required
def following():
    users = current_user.followed.all()
    if not users:
        flash('You are not following anyone', 'info')
    title = "Following"
    return render_template('profile/follow_list.html', users=users, title=title)

@profile_bp.route('/<string:username>/following')
@login_required
def user_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    users = user.followed.all()
    title = f"{username}'s Following"
    return render_template('profile/follow_list.html', users=users, title=title)
# or wherever you want to redirect