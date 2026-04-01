# Smart Library – Digitales Ausleihsystem

Eine intelligente, webbasierte Bibliothek, die man online und von überall nutzen kann.

## Funktionen

| Funktion | Beschreibung |
|---|---|
| **Medien-Suche** | Katalog mit Filterung nach Buch, Film oder Magazin sowie Volltextsuche |
| **Leihkorb** | Medien vor der endgültigen Ausleihe zusammenstellen und auschecken |
| **Mein Konto** | Übersicht über aktive Ausleihen, Rückgabefristen und Ausleihhistorie |
| **Mahnwesen** | Automatisierte Berechnung von Überziehungsgebühren (0,50 € / Tag) |
| **Login / Registrierung** | Sicherer Zugang mit Passwort-Hashing; zwei Rollen: Kunde & Bibliothekar |
| **Bibliothekares-Dashboard** | Bestand verwalten, Rückgaben erfassen, Mahngebühren verbuchen |

## Rollen

- **Kunde** – Kann Medien suchen, in den Leihkorb legen, ausleihen und sein Konto einsehen.
- **Bibliothekar** – Verwaltet den Bestand (hinzufügen / bearbeiten / löschen), bearbeitet Rückgaben und verbucht Mahngebühren.

## Technologie-Stack

- **Backend**: Python / Flask mit Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Datenbank**: SQLite (leicht auf PostgreSQL umstellbar)
- **Frontend**: Bootstrap 5, Bootstrap Icons

## Schnellstart

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank mit Beispieldaten befüllen
python seed.py

# Anwendung starten
python run.py
```

Die Anwendung ist dann unter **http://127.0.0.1:5000** erreichbar.

### Demo-Konten (nach `python seed.py`)

| Rolle | Benutzername | Passwort |
|---|---|---|
| Bibliothekar | `bibliothekar` | `passwort123` |
| Kunde | `max_mustermann` | `passwort123` |
| Kunde | `anna_müller` | `passwort123` |

## Tests ausführen

```bash
pip install pytest pytest-flask
python -m pytest tests/ -v
```

## Projektstruktur

```
Smart_Library/
├── app/
│   ├── __init__.py          # App-Factory
│   ├── extensions.py        # Flask-Erweiterungen (db, login, csrf)
│   ├── models.py            # Datenbank-Modelle (User, Media, Lending, Fine, CartItem)
│   ├── auth.py              # Authentifizierung (Login, Registrierung, Logout)
│   ├── main.py              # Hauptrouten (Katalog, Leihkorb, Konto)
│   ├── librarian.py         # Bibliothekares-Routen
│   ├── forms.py             # WTForms-Formulare
│   ├── static/css/          # Stylesheet
│   └── templates/           # Jinja2-Templates (Bootstrap 5)
├── tests/test_app.py        # Pytest-Tests (40 Tests)
├── config.py                # Konfiguration
├── seed.py                  # Beispieldaten
└── run.py                   # Einstiegspunkt
```
