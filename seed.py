"""Seed the database with sample data for demonstration."""
from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Media, Lending


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Users
        librarian = User(username='bibliothekar', email='librarian@library.de', role='librarian')
        librarian.set_password('passwort123')

        customer1 = User(username='max_mustermann', email='max@example.de', role='customer')
        customer1.set_password('passwort123')

        customer2 = User(username='anna_müller', email='anna@example.de', role='customer')
        customer2.set_password('passwort123')

        db.session.add_all([librarian, customer1, customer2])
        db.session.commit()

        # Media
        media_items = [
            Media(title='Der Prozess', creator='Franz Kafka', category='book',
                  description='Ein Mann wird eines Morgens verhaftet, ohne zu erfahren, warum.',
                  isbn='978-3-15-009003-5', published_year=1925, total_copies=3, available_copies=2),
            Media(title='1984', creator='George Orwell', category='book',
                  description='Dystopischer Roman über einen totalitären Überwachungsstaat.',
                  isbn='978-3-548-23410-7', published_year=1949, total_copies=4, available_copies=4),
            Media(title='Die Verwandlung', creator='Franz Kafka', category='book',
                  description='Gregor Samsa erwacht als Ungeziefer.',
                  isbn='978-3-15-009340-1', published_year=1915, total_copies=2, available_copies=2),
            Media(title='Faust I', creator='Johann Wolfgang von Goethe', category='book',
                  description='Das berühmteste Werk der deutschen Literatur.',
                  isbn='978-3-15-000001-2', published_year=1808, total_copies=5, available_copies=5),
            Media(title='Der kleine Prinz', creator='Antoine de Saint-Exupéry', category='book',
                  description='Ein philosophisches Märchen für Groß und Klein.',
                  isbn='978-3-15-012479-9', published_year=1943, total_copies=3, available_copies=3),
            Media(title='Inception', creator='Christopher Nolan', category='film',
                  description='Ein Dieb stiehlt Geheimnisse aus den Träumen seiner Opfer.',
                  published_year=2010, total_copies=2, available_copies=2),
            Media(title='Das Leben der Anderen', creator='Florian Henckel von Donnersmarck',
                  category='film',
                  description='Ein Stasi-Offizier überwacht einen Künstler im DDR-Regime.',
                  published_year=2006, total_copies=1, available_copies=1),
            Media(title='Metropolis', creator='Fritz Lang', category='film',
                  description='Stummfilm-Klassiker über eine dystopische Zukunftsstadt.',
                  published_year=1927, total_copies=2, available_copies=2),
            Media(title='Der Spiegel', creator='Spiegel-Verlag', category='magazine',
                  description='Deutschlands führendes Nachrichtenmagazin.',
                  isbn='0038-7452', published_year=2024, total_copies=5, available_copies=5),
            Media(title='National Geographic Deutschland', creator='National Geographic Society',
                  category='magazine',
                  description='Wissenschaft, Natur und Geographie in beeindruckenden Bildern.',
                  isbn='1433-3090', published_year=2024, total_copies=3, available_copies=3),
            Media(title='c\'t Magazin', creator='Heise Medien', category='magazine',
                  description='Das führende IT-Magazin für professionelle Nutzer.',
                  isbn='0724-8679', published_year=2024, total_copies=4, available_copies=4),
        ]
        db.session.add_all(media_items)
        db.session.commit()

        # Add one overdue lending for demo
        overdue_lending = Lending(
            user_id=customer1.id,
            media_id=media_items[0].id,  # Der Prozess
            borrowed_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=6),
        )
        media_items[0].available_copies -= 1
        db.session.add(overdue_lending)
        db.session.commit()

        print('Datenbank erfolgreich befüllt!')
        print('Konten:')
        print('  Bibliothekar: bibliothekar / passwort123')
        print('  Kunde 1:      max_mustermann / passwort123')
        print('  Kunde 2:      anna_müller / passwort123')


if __name__ == '__main__':
    seed()
