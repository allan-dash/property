from datetime import datetime, timezone, timedelta
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import relationship
from app import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from time import time


followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(512), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    def time_ago(self):
        now = datetime.now(timezone.utc)  # Use current time in UTC, timezone-aware

        # Ensure post timestamp is in UTC
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)  # Make timestamp UTC-aware if it's naive

        delta = now - self.timestamp

        # Calculate time difference in minutes, hours, days, etc.
        if delta < timedelta(minutes=1):
            return "Just now"
        elif delta < timedelta(hours=1):
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta < timedelta(days=30):
            days = delta.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif delta < timedelta(days=365):
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'public' or 'private'
    creation_date: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    memberships = db.relationship('GroupMembership', back_populates='group')

class GroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    role = db.Column(db.String(10), nullable=True)  # 'owner', 'admin', 'user'
    status = db.Column(db.String(10), nullable=False, default='pending')  # 'pending', 'approved'
    user = db.relationship('User', back_populates='memberships')
    group = db.relationship('Group', back_populates='memberships')

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    display_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    registration_date: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')
    memberships = db.relationship('GroupMembership', back_populates='user')
    socket_id = db.Column(db.String(128), unique=True, nullable=True)

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)
    
    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)
    
    def post_count(self):
        # Count the number of posts created by the user
        return db.session.query(Post).filter_by(user_id=self.id).count()
    
class PostTag(db.Model):
    __tablename__ = 'post_tags'
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('post.id'), primary_key=True)
    tag_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('tag.id'), primary_key=True)
    
class Tag(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True)

    def __repr__(self):
        return f'<Tag {self.name}>'

class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    author: so.Mapped[User] = so.relationship(back_populates='posts')

    # Use List from typing module for type hinting
    tags: so.Mapped[List["Tag"]] = so.relationship('Tag', secondary='post_tags', backref='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)
    
    def add_tags(self, tags: List[str]):
        if len(tags) > 5:
            raise ValueError("Cannot add more than 5 tags to a post.")
        
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            
            if tag not in self.tags:
                self.tags.append(tag)
                print(f"Added tag '{tag.name}' to post {self.id}")  # Debug print
            else:
                print(f"Tag '{tag.name}' already linked to post {self.id}")  # Debug print
        
        db.session.flush()
        db.session.commit()



    def time_ago(self):
        now = datetime.now(timezone.utc)  # Use current time in UTC, timezone-aware

        # Ensure post timestamp is in UTC
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)  # Make timestamp UTC-aware if it's naive

        delta = now - self.timestamp

        # Calculate time difference in minutes, hours, days, etc.
        if delta < timedelta(minutes=1):
            return "Just now"
        elif delta < timedelta(hours=1):
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta < timedelta(days=30):
            days = delta.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        elif delta < timedelta(days=365):
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))