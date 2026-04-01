"""Tests for the Smart Library application."""
import pytest
from datetime import date, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import User, Media, Lending, Fine, CartItem
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret'


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


@pytest.fixture
def librarian_user(db):
    u = User(username='bibliothekar', email='lib@test.de', role='librarian')
    u.set_password('passwort123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def customer_user(db):
    u = User(username='max', email='max@test.de', role='customer')
    u.set_password('passwort123')
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def sample_media(db):
    book = Media(title='Testbuch', creator='Test Autor', category='book',
                 total_copies=3, available_copies=3)
    film = Media(title='Testfilm', creator='Test Regisseur', category='film',
                 total_copies=1, available_copies=1)
    magazine = Media(title='Testmagazin', creator='Test Verlag', category='magazine',
                     total_copies=2, available_copies=2)
    db.session.add_all([book, film, magazine])
    db.session.commit()
    return book, film, magazine


# --- Helper ---

def login(client, username, password):
    return client.post('/auth/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


def logout(client):
    return client.get('/auth/logout', follow_redirects=True)


# =============================================================================
# Authentication tests
# =============================================================================

class TestAuth:
    def test_register_new_user(self, client):
        rv = client.post('/auth/register', data={
            'username': 'neuernutzer',
            'email': 'neuer@test.de',
            'password': 'geheim123',
            'password2': 'geheim123',
        }, follow_redirects=True)
        assert rv.status_code == 200
        assert 'Registrierung erfolgreich' in rv.data.decode()

    def test_register_duplicate_username(self, client, customer_user):
        rv = client.post('/auth/register', data={
            'username': 'max',
            'email': 'andere@test.de',
            'password': 'geheim123',
            'password2': 'geheim123',
        }, follow_redirects=True)
        assert 'Benutzername bereits vergeben' in rv.data.decode()

    def test_login_valid(self, client, customer_user):
        rv = login(client, 'max', 'passwort123')
        assert 'Willkommen' in rv.data.decode()

    def test_login_invalid_password(self, client, customer_user):
        rv = login(client, 'max', 'falsch')
        assert 'Ungültiger Benutzername oder Passwort' in rv.data.decode()

    def test_login_unknown_user(self, client):
        rv = login(client, 'unbekannt', 'whatever')
        assert 'Ungültiger Benutzername oder Passwort' in rv.data.decode()

    def test_logout(self, client, customer_user):
        login(client, 'max', 'passwort123')
        rv = logout(client)
        assert 'abgemeldet' in rv.data.decode()

    def test_protected_route_redirects_to_login(self, client):
        rv = client.get('/cart', follow_redirects=True)
        assert 'Anmelden' in rv.data.decode()


# =============================================================================
# Media / Catalog tests
# =============================================================================

class TestCatalog:
    def test_catalog_accessible_without_login(self, client, sample_media):
        rv = client.get('/catalog')
        assert rv.status_code == 200
        assert 'Testbuch' in rv.data.decode()

    def test_search_by_title(self, client, sample_media):
        rv = client.get('/catalog?query=Testbuch')
        assert 'Testbuch' in rv.data.decode()
        assert 'Testfilm' not in rv.data.decode()

    def test_filter_by_category_book(self, client, sample_media):
        rv = client.get('/catalog?category=book')
        assert 'Testbuch' in rv.data.decode()
        assert 'Testfilm' not in rv.data.decode()

    def test_filter_by_category_film(self, client, sample_media):
        rv = client.get('/catalog?category=film')
        assert 'Testfilm' in rv.data.decode()
        assert 'Testbuch' not in rv.data.decode()

    def test_filter_by_category_magazine(self, client, sample_media):
        rv = client.get('/catalog?category=magazine')
        assert 'Testmagazin' in rv.data.decode()

    def test_media_detail(self, client, sample_media):
        book = sample_media[0]
        rv = client.get(f'/media/{book.id}')
        assert rv.status_code == 200
        assert 'Testbuch' in rv.data.decode()

    def test_media_not_found(self, client):
        rv = client.get('/media/9999')
        assert rv.status_code == 404


# =============================================================================
# Cart tests
# =============================================================================

class TestCart:
    def test_add_to_cart(self, client, customer_user, sample_media):
        login(client, 'max', 'passwort123')
        book = sample_media[0]
        rv = client.post(f'/cart/add/{book.id}', follow_redirects=True)
        assert rv.status_code == 200
        assert 'Leihkorb hinzugefügt' in rv.data.decode()

    def test_add_unavailable_to_cart(self, client, customer_user, db):
        media = Media(title='Kein Exemplar', creator='Autor', category='book',
                      total_copies=1, available_copies=0)
        db.session.add(media)
        db.session.commit()
        login(client, 'max', 'passwort123')
        rv = client.post(f'/cart/add/{media.id}', follow_redirects=True)
        assert 'nicht verfügbar' in rv.data.decode()

    def test_add_duplicate_to_cart(self, client, customer_user, sample_media):
        login(client, 'max', 'passwort123')
        book = sample_media[0]
        client.post(f'/cart/add/{book.id}', follow_redirects=True)
        rv = client.post(f'/cart/add/{book.id}', follow_redirects=True)
        assert 'bereits im Leihkorb' in rv.data.decode()

    def test_view_cart(self, client, customer_user, sample_media):
        login(client, 'max', 'passwort123')
        book = sample_media[0]
        client.post(f'/cart/add/{book.id}', follow_redirects=True)
        rv = client.get('/cart')
        assert 'Testbuch' in rv.data.decode()

    def test_remove_from_cart(self, client, customer_user, sample_media, db):
        login(client, 'max', 'passwort123')
        book = sample_media[0]
        item = CartItem(user_id=customer_user.id, media_id=book.id)
        db.session.add(item)
        db.session.commit()
        rv = client.post(f'/cart/remove/{item.id}', follow_redirects=True)
        assert 'entfernt' in rv.data.decode()

    def test_checkout_creates_lendings(self, client, customer_user, sample_media, db):
        login(client, 'max', 'passwort123')
        book = sample_media[0]
        client.post(f'/cart/add/{book.id}', follow_redirects=True)
        rv = client.post('/cart/checkout', follow_redirects=True)
        assert 'Erfolgreich ausgeliehen' in rv.data.decode()
        lending = Lending.query.filter_by(
            user_id=customer_user.id, media_id=book.id).first()
        assert lending is not None
        assert lending.returned_date is None

    def test_checkout_reduces_available_copies(self, client, customer_user, sample_media, db):
        login(client, 'max', 'passwort123')
        book = sample_media[0]
        original_available = book.available_copies
        client.post(f'/cart/add/{book.id}', follow_redirects=True)
        client.post('/cart/checkout', follow_redirects=True)
        db.session.refresh(book)
        assert book.available_copies == original_available - 1

    def test_empty_cart_checkout(self, client, customer_user):
        login(client, 'max', 'passwort123')
        rv = client.post('/cart/checkout', follow_redirects=True)
        assert 'leer' in rv.data.decode()


# =============================================================================
# Account tests
# =============================================================================

class TestAccount:
    def test_account_shows_active_lendings(self, client, customer_user, sample_media, db):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )
        db.session.add(lending)
        db.session.commit()
        login(client, 'max', 'passwort123')
        rv = client.get('/account')
        assert 'Testbuch' in rv.data.decode()

    def test_account_shows_overdue_status(self, client, customer_user, sample_media, db):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
        )
        db.session.add(lending)
        db.session.commit()
        login(client, 'max', 'passwort123')
        rv = client.get('/account')
        assert 'Überfällig' in rv.data.decode()


# =============================================================================
# Fine (Mahnwesen) tests
# =============================================================================

class TestFines:
    def test_overdue_lending_creates_fine(self, client, customer_user, sample_media, db, app):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
        )
        db.session.add(lending)
        db.session.commit()
        login(client, 'max', 'passwort123')
        client.get('/account')  # triggers _update_fines
        with app.app_context():
            fine = Fine.query.filter_by(lending_id=lending.id).first()
            assert fine is not None
            assert fine.amount == pytest.approx(6 * app.config['FINE_PER_DAY'])

    def test_fine_amount_is_days_times_rate(self, app):
        with app.app_context():
            fine_per_day = app.config['FINE_PER_DAY']
            assert fine_per_day > 0
            assert fine_per_day == pytest.approx(0.50)

    def test_no_fine_for_active_non_overdue(self, client, customer_user, sample_media, db, app):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )
        db.session.add(lending)
        db.session.commit()
        login(client, 'max', 'passwort123')
        client.get('/account')
        with app.app_context():
            assert Fine.query.filter_by(lending_id=lending.id).count() == 0


# =============================================================================
# Librarian tests
# =============================================================================

class TestLibrarian:
    def test_librarian_dashboard_accessible(self, client, librarian_user):
        login(client, 'bibliothekar', 'passwort123')
        rv = client.get('/librarian/')
        assert rv.status_code == 200
        assert 'Dashboard' in rv.data.decode()

    def test_customer_cannot_access_librarian(self, client, customer_user):
        login(client, 'max', 'passwort123')
        rv = client.get('/librarian/')
        assert rv.status_code == 403

    def test_add_media(self, client, librarian_user):
        login(client, 'bibliothekar', 'passwort123')
        rv = client.post('/librarian/media/add', data={
            'title': 'Neues Buch',
            'creator': 'Neuer Autor',
            'category': 'book',
            'total_copies': 2,
        }, follow_redirects=True)
        assert 'hinzugefügt' in rv.data.decode()
        assert Media.query.filter_by(title='Neues Buch').first() is not None

    def test_edit_media(self, client, librarian_user, sample_media):
        login(client, 'bibliothekar', 'passwort123')
        book = sample_media[0]
        rv = client.post(f'/librarian/media/{book.id}/edit', data={
            'title': 'Geänderter Titel',
            'creator': 'Test Autor',
            'category': 'book',
            'total_copies': 3,
        }, follow_redirects=True)
        assert 'aktualisiert' in rv.data.decode()

    def test_delete_media(self, client, librarian_user, sample_media):
        login(client, 'bibliothekar', 'passwort123')
        book = sample_media[0]
        rv = client.post(f'/librarian/media/{book.id}/delete', follow_redirects=True)
        assert 'gelöscht' in rv.data.decode()
        assert Media.query.get(book.id) is None

    def test_process_return(self, client, librarian_user, customer_user, sample_media, db):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today() - timedelta(days=5),
            due_date=date.today() + timedelta(days=9),
        )
        sample_media[0].available_copies -= 1
        db.session.add(lending)
        db.session.commit()
        login(client, 'bibliothekar', 'passwort123')
        rv = client.post(f'/librarian/returns/{lending.id}/process', follow_redirects=True)
        assert 'zurückgegeben' in rv.data.decode()
        db.session.refresh(lending)
        assert lending.returned_date == date.today()

    def test_pay_fine(self, client, librarian_user, customer_user, sample_media, db):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
        )
        db.session.add(lending)
        db.session.commit()
        fine = Fine(lending_id=lending.id, amount=3.0)
        db.session.add(fine)
        db.session.commit()
        login(client, 'bibliothekar', 'passwort123')
        rv = client.post(f'/librarian/fines/{fine.id}/pay', follow_redirects=True)
        assert 'bezahlt markiert' in rv.data.decode()
        db.session.refresh(fine)
        assert fine.paid is True


# =============================================================================
# Model unit tests
# =============================================================================

class TestModels:
    def test_user_password_hashing(self, db):
        u = User(username='tester', email='t@test.de', role='customer')
        u.set_password('geheim')
        db.session.add(u)
        db.session.commit()
        assert u.check_password('geheim')
        assert not u.check_password('falsch')

    def test_media_availability(self, db):
        m = Media(title='Test', creator='Autor', category='book',
                  total_copies=2, available_copies=0)
        db.session.add(m)
        db.session.commit()
        assert not m.is_available
        m.available_copies = 1
        assert m.is_available

    def test_lending_overdue(self, db, customer_user, sample_media):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
        )
        db.session.add(lending)
        db.session.commit()
        assert lending.is_overdue
        assert lending.overdue_days == 6

    def test_lending_not_overdue(self, db, customer_user, sample_media):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today(),
            due_date=date.today() + timedelta(days=14),
        )
        db.session.add(lending)
        db.session.commit()
        assert not lending.is_overdue
        assert lending.overdue_days == 0

    def test_returned_lending_not_overdue(self, db, customer_user, sample_media):
        lending = Lending(
            user_id=customer_user.id,
            media_id=sample_media[0].id,
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
            returned_date=date.today() - timedelta(days=1),
        )
        db.session.add(lending)
        db.session.commit()
        assert not lending.is_overdue
        assert lending.overdue_days == 0
        assert lending.is_returned

    def test_category_labels(self, db):
        book = Media(title='B', creator='A', category='book',
                     total_copies=1, available_copies=1)
        film = Media(title='F', creator='A', category='film',
                     total_copies=1, available_copies=1)
        magazine = Media(title='M', creator='A', category='magazine',
                         total_copies=1, available_copies=1)
        db.session.add_all([book, film, magazine])
        db.session.commit()
        assert book.category_label == 'Buch'
        assert film.category_label == 'Film'
        assert magazine.category_label == 'Magazin'
