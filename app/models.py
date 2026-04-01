from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'customer' or 'librarian'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lendings = db.relationship('Lending', back_populates='user', lazy='dynamic')
    cart_items = db.relationship('CartItem', back_populates='user', lazy='dynamic',
                                 cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_librarian(self):
        return self.role == 'librarian'

    @property
    def active_lendings(self):
        return self.lendings.filter_by(returned_date=None).all()

    @property
    def total_fines(self):
        total = 0.0
        for lending in self.lendings:
            for fine in lending.fines:
                if not fine.paid:
                    total += fine.amount
        return total

    def __repr__(self):
        return f'<User {self.username}>'


class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    creator = db.Column(db.String(150), nullable=False)  # author / director
    category = db.Column(db.String(20), nullable=False)  # 'book', 'film', 'magazine'
    description = db.Column(db.Text, default='')
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    published_year = db.Column(db.Integer, nullable=True)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    cover_url = db.Column(db.String(500), nullable=True)

    lendings = db.relationship('Lending', back_populates='media', lazy='dynamic')
    cart_items = db.relationship('CartItem', back_populates='media', lazy='dynamic',
                                 cascade='all, delete-orphan')

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def category_label(self):
        labels = {'book': 'Buch', 'film': 'Film', 'magazine': 'Magazin'}
        return labels.get(self.category, self.category)

    @property
    def category_icon(self):
        icons = {'book': 'bi-book', 'film': 'bi-film', 'magazine': 'bi-journal-text'}
        return icons.get(self.category, 'bi-collection')

    def __repr__(self):
        return f'<Media {self.title}>'


class Lending(db.Model):
    __tablename__ = 'lendings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False, index=True)
    borrowed_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date, nullable=True)

    user = db.relationship('User', back_populates='lendings')
    media = db.relationship('Media', back_populates='lendings')
    fines = db.relationship('Fine', back_populates='lending', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def is_returned(self):
        return self.returned_date is not None

    @property
    def is_overdue(self):
        if self.is_returned:
            return False
        return date.today() > self.due_date

    @property
    def overdue_days(self):
        if self.is_returned:
            return 0
        delta = date.today() - self.due_date
        return max(0, delta.days)

    @property
    def status_label(self):
        if self.is_returned:
            return 'Zurückgegeben'
        if self.is_overdue:
            return 'Überfällig'
        return 'Ausgeliehen'

    @property
    def status_class(self):
        if self.is_returned:
            return 'success'
        if self.is_overdue:
            return 'danger'
        return 'primary'

    def __repr__(self):
        return f'<Lending user={self.user_id} media={self.media_id}>'


class Fine(db.Model):
    __tablename__ = 'fines'

    id = db.Column(db.Integer, primary_key=True)
    lending_id = db.Column(db.Integer, db.ForeignKey('lendings.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    lending = db.relationship('Lending', back_populates='fines')

    def __repr__(self):
        return f'<Fine lending={self.lending_id} amount={self.amount:.2f}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='cart_items')
    media = db.relationship('Media', back_populates='cart_items')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'media_id', name='uq_cart_user_media'),
    )

    def __repr__(self):
        return f'<CartItem user={self.user_id} media={self.media_id}>'
