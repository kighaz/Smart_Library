from datetime import date, timedelta
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Media, Lending, CartItem, Fine
from app.forms import SearchForm

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return redirect(url_for('main.catalog'))


@main.route('/catalog')
def catalog():
    form = SearchForm(request.args, meta={'csrf': False})
    query = Media.query
    search_term = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()

    if search_term:
        query = query.filter(
            (Media.title.ilike(f'%{search_term}%')) |
            (Media.creator.ilike(f'%{search_term}%'))
        )
    if category:
        query = query.filter_by(category=category)

    media_list = query.order_by(Media.title).all()
    return render_template('main/catalog.html', media_list=media_list,
                           form=form, search_term=search_term, category=category)


@main.route('/media/<int:media_id>')
def media_detail(media_id):
    media = Media.query.get_or_404(media_id)
    in_cart = False
    if current_user.is_authenticated:
        in_cart = CartItem.query.filter_by(
            user_id=current_user.id, media_id=media_id).first() is not None
    return render_template('main/media_detail.html', media=media, in_cart=in_cart)


# --- Cart ---

@main.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    return render_template('main/cart.html', items=items)


@main.route('/cart/add/<int:media_id>', methods=['POST'])
@login_required
def cart_add(media_id):
    media = Media.query.get_or_404(media_id)
    if not media.is_available:
        flash(f'"{media.title}" ist derzeit nicht verfügbar.', 'warning')
        return redirect(url_for('main.catalog'))

    existing = CartItem.query.filter_by(
        user_id=current_user.id, media_id=media_id).first()
    if existing:
        flash(f'"{media.title}" ist bereits im Leihkorb.', 'info')
    else:
        item = CartItem(user_id=current_user.id, media_id=media_id)
        db.session.add(item)
        db.session.commit()
        flash(f'"{media.title}" zum Leihkorb hinzugefügt.', 'success')
    return redirect(url_for('main.catalog'))


@main.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def cart_remove(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Zugriff verweigert.', 'danger')
        return redirect(url_for('main.cart'))
    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.media.title}" aus dem Leihkorb entfernt.', 'info')
    return redirect(url_for('main.cart'))


@main.route('/cart/checkout', methods=['POST'])
@login_required
def cart_checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Dein Leihkorb ist leer.', 'warning')
        return redirect(url_for('main.cart'))

    lending_period = current_app.config['LENDING_PERIOD_DAYS']
    borrowed = []
    skipped = []

    for item in items:
        media = item.media
        if not media.is_available:
            skipped.append(media.title)
            db.session.delete(item)
            continue

        lending = Lending(
            user_id=current_user.id,
            media_id=media.id,
            borrowed_date=date.today(),
            due_date=date.today() + timedelta(days=lending_period),
        )
        media.available_copies -= 1
        db.session.add(lending)
        db.session.delete(item)
        borrowed.append(media.title)

    db.session.commit()

    if borrowed:
        flash(f'Erfolgreich ausgeliehen: {", ".join(borrowed)}.', 'success')
    if skipped:
        flash(f'Nicht mehr verfügbar (übersprungen): {", ".join(skipped)}.', 'warning')

    return redirect(url_for('main.account'))


# --- Account ---

@main.route('/account')
@login_required
def account():
    _update_fines(current_user)
    active = Lending.query.filter_by(
        user_id=current_user.id, returned_date=None).all()
    history = Lending.query.filter(
        Lending.user_id == current_user.id,
        Lending.returned_date.isnot(None)
    ).order_by(Lending.returned_date.desc()).all()
    unpaid_fines = []
    for lending in current_user.lendings:
        for fine in lending.fines:
            if not fine.paid:
                unpaid_fines.append(fine)
    return render_template('main/account.html', active=active,
                           history=history, unpaid_fines=unpaid_fines)


def _update_fines(user):
    """Create or update fine records for overdue lendings."""
    fine_per_day = current_app.config['FINE_PER_DAY']
    for lending in user.active_lendings:
        if lending.is_overdue:
            overdue_days = lending.overdue_days
            expected_amount = round(overdue_days * fine_per_day, 2)
            existing = lending.fines.filter_by(paid=False).first()
            if existing:
                existing.amount = expected_amount
            else:
                fine = Fine(lending_id=lending.id, amount=expected_amount)
                db.session.add(fine)
    db.session.commit()
