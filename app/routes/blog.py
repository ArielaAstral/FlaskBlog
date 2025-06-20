from flask import Blueprint, render_template, url_for, flash, redirect, request, abort,jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Post,User,followers
from sqlalchemy.exc import IntegrityError


blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
@blog_bp.route('/global_feed')

def global_feed():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=3)
    return render_template('blog/global_feed.html', posts=posts, title='Blog Feed')


@blog_bp.route('/feed')
@login_required
def feed():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == current_user.id).order_by(Post.created_at.desc()).paginate(page=page, per_page=3)
    if posts.total==0:
        flash("Follow anyone to see their blogs here",'info')
    return render_template('blog/feed.html', posts=posts, title='Blog Feed')



@blog_bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required', 'danger')
            return redirect(url_for('blog.create_post'))
        
        post = Post(title=title, content=content, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('blog.global_feed'))
    
    return render_template('blog/create.html', title='New Post')

@blog_bp.route('/post/page=<int:page>&post_id=<int:post_id>')
def post(post_id,page):
    post = Post.query.get_or_404(post_id)
    print(page)
    return render_template('blog/view.html', title=post.title, post=post,posn='local',page=page)

@blog_bp.route('/global_post/page=<int:page>&post_id=<int:post_id>')
def global_post(post_id,page):
    post = Post.query.get_or_404(post_id)
    return render_template('blog/view.html', title=post.title, post=post,posn='global',page=page)

@blog_bp.route('/profile_post/post_id=<int:post_id>')
def profile_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('blog/view.html', title=post.title, post=post,posn='profile')

@blog_bp.route('/post/<string:posn>&post_id=<int:post_id>&edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id,posn):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required', 'danger')
            return redirect(url_for('blog.edit_post', post_id=post.id,posn=posn))
        
        post.title = title
        post.content = content
        db.session.commit()
        flash('Your post has been updated!', 'success')
        if posn=='pp':
            return redirect(url_for('profile.profile'))
        else:
            return redirect(url_for('blog.global_post', post_id=post.id, page=1))
    
    return render_template('blog/edit.html', title='Edit Post', post=post,posn=posn)



@blog_bp.route('/post/post_id=<int:post_id>&delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('blog.global_feed'))


@blog_bp.route('/users')
@login_required
def users():
    all_users= User.query.all()
    return render_template('blog/user_list.html',users=all_users)

from flask import jsonify

@blog_bp.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)

    try:
        if current_user.has_liked_post(post):
            current_user.unlike_post(post)
            action = 'unliked'
        else:
            current_user.like_post(post)
            action = 'liked'

        db.session.commit()

        return jsonify({
            'status': 'success',
            'action': action,
            'like_count': post.like_count
        })

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Already liked/unliked (conflict)'
        }), 400