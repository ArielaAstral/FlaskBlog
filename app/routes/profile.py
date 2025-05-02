from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from app import db
from app.models import Post, User

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    return render_template('profile/profile.html', title='Profile', posts=posts)

@profile_bp.route('/profile/<string:username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('profile/profile.html', title=f'{username}\'s Profile', user=user, posts=posts)


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

