"""Admin dashboard: products & stock, orders, and user roles. Every route requires the admin role."""
import datetime
import re

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from auth import admin_required
from catalog import BUILTIN_IMAGES, PRODUCT_KINDS, get_product, list_products
from i18n import _

bp = Blueprint('admin', __name__, url_prefix='/admin')

LOW_STOCK = 5
MAX_PRICE = 10_000_000
MAX_STOCK = 100_000
ORDER_LIMIT = 200

# Set by init_admin()
_db = None


def init_admin(app, db):
    global _db
    _db = db
    app.register_blueprint(bp)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _all(collection):
    items = []
    for snap in _db.collection(collection).stream():
        item = snap.to_dict()
        item['id'] = snap.id
        items.append(item)
    return items


def _parse_product_form(form):
    """Return (data, errors) from the add/edit product form."""
    errors = []
    data = {
        'name': form.get('name', '').strip()[:80],
        'description': form.get('description', '').strip()[:500],
        'kind': form.get('kind', 'simple'),
        'active': form.get('active') == 'on',
    }
    if not data['name']:
        errors.append(_('Name is required.'))
    if data['kind'] not in PRODUCT_KINDS:
        errors.append(_('Choose a valid product type.'))

    try:
        data['price'] = round(float(form.get('price', '')), 2)
        if not 0 < data['price'] <= MAX_PRICE:
            raise ValueError
    except ValueError:
        errors.append(_('Price must be a number between 1 and {max}.', max=f'{MAX_PRICE:,}'))

    try:
        data['stock'] = int(form.get('stock', ''))
        if not 0 <= data['stock'] <= MAX_STOCK:
            raise ValueError
    except ValueError:
        errors.append(_('Stock must be a whole number between 0 and {max}.', max=f'{MAX_STOCK:,}'))

    try:
        data['sort'] = int(form.get('sort') or 1000)
    except ValueError:
        errors.append(_('Display order must be a whole number.'))

    image_url = form.get('image_url', '').strip()
    builtin = form.get('image_builtin', '')
    if image_url:
        # Only plain web URLs: blocks javascript:/data: tricks in <img src>
        if not re.match(r'^https?://[^\s"\'<>]+$', image_url):
            errors.append(_('Image URL must start with http:// or https://'))
        data['image'] = image_url
    elif builtin in BUILTIN_IMAGES:
        data['image'] = builtin
    else:
        errors.append(_('Paste an image URL or choose one of the built-in images.'))
    return data, errors


@bp.route('/')
@admin_required
def dashboard():
    products = list_products(_db, include_inactive=True)
    orders = sorted(_all('orders'), key=lambda o: o.get('created_at', ''), reverse=True)
    paid = [o for o in orders if o.get('status') == 'paid']
    stats = {
        'products': len(products),
        'low_stock': sum(1 for p in products if int(p.get('stock', 0)) <= LOW_STOCK),
        'pending': sum(1 for o in orders if o.get('status') == 'pending'),
        'paid': len(paid),
        'revenue': sum(float(o.get('amount', 0)) for o in paid),
    }
    low_stock = [p for p in products if int(p.get('stock', 0)) <= LOW_STOCK]
    return render_template('admin/dashboard.html', stats=stats, low_stock=low_stock,
                           recent_orders=orders[:8], LOW_STOCK=LOW_STOCK)


@bp.route('/products')
@admin_required
def products():
    return render_template('admin/products.html', products=list_products(_db, include_inactive=True),
                           kinds=PRODUCT_KINDS, LOW_STOCK=LOW_STOCK)


@bp.route('/products/new', methods=['GET', 'POST'])
@admin_required
def new_product():
    product = {'name': '', 'description': '', 'kind': 'vehicle', 'price': '', 'stock': 0, 'sort': '',
               'image': BUILTIN_IMAGES[0], 'active': True}
    if request.method == 'POST':
        data, errors = _parse_product_form(request.form)
        if not errors:
            data['created_at'] = _now()
            ref = _db.collection('products').document()
            ref.set(data)
            flash(_('Added "{name}".', name=data['name']), 'success')
            return redirect(url_for('admin.products'))
        for error in errors:
            flash(error, 'error')
        product.update(data)
    return render_template('admin/product_form.html', product=product, is_new=True,
                           kinds=PRODUCT_KINDS, builtin_images=BUILTIN_IMAGES)


@bp.route('/products/<product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = get_product(_db, product_id) or abort(404)
    if request.method == 'POST':
        data, errors = _parse_product_form(request.form)
        if not errors:
            data['updated_at'] = _now()
            _db.collection('products').document(product_id).update(data)
            flash(_('Saved "{name}".', name=data['name']), 'success')
            return redirect(url_for('admin.products'))
        for error in errors:
            flash(error, 'error')
        product.update(data)
    return render_template('admin/product_form.html', product=product, is_new=False,
                           kinds=PRODUCT_KINDS, builtin_images=BUILTIN_IMAGES)


@bp.route('/products/<product_id>/stock', methods=['POST'])
@admin_required
def set_stock(product_id):
    product = get_product(_db, product_id) or abort(404)
    try:
        stock = int(request.form.get('stock', ''))
        if not 0 <= stock <= MAX_STOCK:
            raise ValueError
    except ValueError:
        flash(_('Stock must be a whole number between 0 and {max}.', max=f'{MAX_STOCK:,}'), 'error')
        return redirect(url_for('admin.products'))
    _db.collection('products').document(product_id).update({'stock': stock, 'updated_at': _now()})
    flash(_('{name}: stock set to {stock}.', name=product['name'], stock=stock), 'success')
    if request.form.get('back') == 'dashboard':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.products'))


@bp.route('/products/<product_id>/toggle', methods=['POST'])
@admin_required
def toggle_product(product_id):
    product = get_product(_db, product_id) or abort(404)
    active = not product.get('active', True)
    _db.collection('products').document(product_id).update({'active': active, 'updated_at': _now()})
    message = '{name} is now visible in the shop.' if active else '{name} is now hidden from the shop.'
    flash(_(message, name=product['name']), 'success')
    return redirect(url_for('admin.products'))


@bp.route('/products/<product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = get_product(_db, product_id) or abort(404)
    _db.collection('products').document(product_id).delete()
    flash(_('Deleted "{name}". Past orders keep their item names.', name=product['name']), 'success')
    return redirect(url_for('admin.products'))


@bp.route('/orders')
@admin_required
def orders():
    status = request.args.get('status', '')
    orders = sorted(_all('orders'), key=lambda o: o.get('created_at', ''), reverse=True)
    if status:
        orders = [o for o in orders if o.get('status') == status]
    return render_template('admin/orders.html', orders=orders[:ORDER_LIMIT], status=status,
                           statuses=['pending', 'paid', 'cancelled', 'failed', 'amount_mismatch'])


@bp.route('/users')
@admin_required
def users():
    users = sorted(_all('users'), key=lambda u: (u.get('role') != 'admin', u.get('email', '')))
    return render_template('admin/users.html', users=users)


@bp.route('/users/<user_id>/role', methods=['POST'])
@admin_required
def set_role(user_id):
    role = request.form.get('role')
    if role not in ('admin', 'shopper'):
        abort(400)
    if user_id == g.user['id'] and role != 'admin':
        flash(_("You can't remove your own admin role."), 'error')
        return redirect(url_for('admin.users'))
    snap = _db.collection('users').document(user_id).get()
    if not snap.exists:
        abort(404)
    _db.collection('users').document(user_id).update({'role': role})
    message = '{email} is now an admin.' if role == 'admin' else '{email} is now a shopper.'
    flash(_(message, email=snap.to_dict().get('email', user_id)), 'success')
    return redirect(url_for('admin.users'))
