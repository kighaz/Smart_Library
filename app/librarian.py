from datetime import date
from functools import wraps
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, abort)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Media, Lending, Fine, User
from app.forms import MediaForm

librarian = Blueprint('librarian', __name__, url_prefix='/librarian')


def librarian_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_librarian:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@librarian.route('/')
@login_required
@librarian_required
def dashboard():
    total_media = Media.query.count()
    total_users = User.query.filter_by(role='customer').count()
    active_lendings = Lending.query.filter_by(returned_date=None).count()
    overdue = Lending.query.filter(
        Lending.returned_date.is_(None),
        Lending.due_date < date.today()
    ).count()
    unpaid_fines = Fine.query.filter_by(paid=False).count()
    return render_template('librarian/dashboard.html',
                           total_media=total_media,
                           total_users=total_users,
                           active_lendings=active_lendings,
                           overdue=overdue,
                           unpaid_fines=unpaid_fines)


@librarian.route('/media')
@login_required
@librarian_required
def media_list():
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()
    media_query = Media.query
    if query:
        media_query = media_query.filter(
            (Media.title.ilike(f'%{query}%')) |
            (Media.creator.ilike(f'%{query}%'))
        )
    if category:
        media_query = media_query.filter_by(category=category)
    media_items = media_query.order_by(Media.title).all()
    return render_template('librarian/media_list.html', media_items=media_items,
                           query=query, category=category)


@librarian.route('/media/add', methods=['GET', 'POST'])
@login_required
@librarian_required
def add_media():
    form = MediaForm()
    if form.validate_on_submit():
        media = Media(
            title=form.title.data,
            creator=form.creator.data,
            category=form.category.data,
            description=form.description.data or '',
            isbn=form.isbn.data or None,
            published_year=form.published_year.data,
            total_copies=form.total_copies.data,
            available_copies=form.total_copies.data,
            cover_url=form.cover_url.data or None,
        )
        db.session.add(media)
        db.session.commit()
        flash(f'Medium "{media.title}" wurde hinzugefügt.', 'success')
        return redirect(url_for('librarian.media_list'))
    return render_template('librarian/media_form.html', form=form, title='Medium hinzufügen')


@librarian.route('/media/<int:media_id>/edit', methods=['GET', 'POST'])
@login_required
@librarian_required
def edit_media(media_id):
    media = Media.query.get_or_404(media_id)
    form = MediaForm(obj=media)
    if form.validate_on_submit():
        diff = form.total_copies.data - media.total_copies
        media.title = form.title.data
        media.creator = form.creator.data
        media.category = form.category.data
        media.description = form.description.data or ''
        media.isbn = form.isbn.data or None
        media.published_year = form.published_year.data
        media.total_copies = form.total_copies.data
        media.available_copies = max(0, media.available_copies + diff)
        media.cover_url = form.cover_url.data or None
        db.session.commit()
        flash(f'Medium "{media.title}" wurde aktualisiert.', 'success')
        return redirect(url_for('librarian.media_list'))
    return render_template('librarian/media_form.html', form=form,
                           title='Medium bearbeiten', media=media)


@librarian.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
@librarian_required
def delete_media(media_id):
    media = Media.query.get_or_404(media_id)
    db.session.delete(media)
    db.session.commit()
    flash(f'Medium "{media.title}" wurde gelöscht.', 'success')
    return redirect(url_for('librarian.media_list'))


@librarian.route('/returns')
@login_required
@librarian_required
def returns():
    active_lendings = Lending.query.filter_by(returned_date=None).order_by(
        Lending.due_date).all()
    return render_template('librarian/returns.html', lendings=active_lendings)


@librarian.route('/returns/<int:lending_id>/process', methods=['POST'])
@login_required
@librarian_required
def process_return(lending_id):
    lending = Lending.query.get_or_404(lending_id)
    if lending.returned_date:
        flash('Dieses Medium wurde bereits zurückgegeben.', 'warning')
        return redirect(url_for('librarian.returns'))

    lending.returned_date = date.today()
    lending.media.available_copies += 1

    # Mark outstanding fines as finalized (keep unpaid, librarian handles payment)
    db.session.commit()
    flash(f'"{lending.media.title}" wurde zurückgegeben.', 'success')
    return redirect(url_for('librarian.returns'))


@librarian.route('/fines')
@login_required
@librarian_required
def fines():
    unpaid = Fine.query.filter_by(paid=False).all()
    paid = Fine.query.filter_by(paid=True).order_by(Fine.paid_at.desc()).limit(50).all()
    return render_template('librarian/fines.html', unpaid=unpaid, paid=paid)


@librarian.route('/fines/<int:fine_id>/pay', methods=['POST'])
@login_required
@librarian_required
def pay_fine(fine_id):
    from datetime import datetime
    fine = Fine.query.get_or_404(fine_id)
    fine.paid = True
    fine.paid_at = datetime.utcnow()
    db.session.commit()
    flash(f'Gebühr von {fine.amount:.2f} € wurde als bezahlt markiert.', 'success')
    return redirect(url_for('librarian.fines'))
