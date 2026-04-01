import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'library.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Lending period in days
    LENDING_PERIOD_DAYS = 14
    # Fine per overdue day in EUR
    FINE_PER_DAY = 0.50
