from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, SelectField,
                     TextAreaField, IntegerField, FloatField, BooleanField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo,
                                ValidationError, NumberRange, Optional)
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired()])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Anmelden')


class RegisterForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(3, 64)])
    email = StringField('E-Mail', validators=[DataRequired(), Email()])
    password = PasswordField('Passwort', validators=[DataRequired(), Length(6, 128)])
    password2 = PasswordField('Passwort bestätigen',
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrieren')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Benutzername bereits vergeben.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('E-Mail-Adresse bereits registriert.')


class MediaForm(FlaskForm):
    title = StringField('Titel', validators=[DataRequired(), Length(1, 200)])
    creator = StringField('Autor / Regisseur', validators=[DataRequired(), Length(1, 150)])
    category = SelectField('Kategorie', choices=[
        ('book', 'Buch'),
        ('film', 'Film'),
        ('magazine', 'Magazin'),
    ], validators=[DataRequired()])
    description = TextAreaField('Beschreibung', validators=[Optional()])
    isbn = StringField('ISBN / Kennung', validators=[Optional(), Length(max=20)])
    published_year = IntegerField('Erscheinungsjahr',
                                  validators=[Optional(), NumberRange(1000, 2100)])
    total_copies = IntegerField('Anzahl Exemplare',
                                validators=[DataRequired(), NumberRange(1, 9999)],
                                default=1)
    cover_url = StringField('Cover-URL', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Speichern')


class SearchForm(FlaskForm):
    query = StringField('Suche', validators=[Optional()])
    category = SelectField('Kategorie', choices=[
        ('', 'Alle'),
        ('book', 'Buch'),
        ('film', 'Film'),
        ('magazine', 'Magazin'),
    ], validators=[Optional()])
    submit = SubmitField('Suchen')
