from io import BufferedReader
from datetime import datetime
from decimal import Decimal
import warnings
from flask import render_template, request, redirect, url_for, abort
from ..model import users, categories, templates, parse_receipt, Receipt, Item, stats_new_receipt, stats_update_receipt
from .. import app, db


@app.route('/receipt/new', methods=['GET', 'POST'])
def receipt_new():
    if request.method == 'GET':
        return render_template('receipt_edit.html',
                               receipt=None, committed=False,
                               users=users(), categories=categories(), templates=templates(),
                               alerts=[])
    # FUTURE: fix csrf
    d = request.json
    if d['id'] is not None:
        abort(400)  # only new receipts
    if 'deletedItems' in d and d['deletedItems']:
        abort(400)  # can't delete in a new receipt
    with db.transaction():
        r = Receipt.new(datetime.fromtimestamp(d['timestamp']), d['comment'])
        _process_items_json(r, d['items'])
        r.save()
        app.logger.debug(r)
        stats_new_receipt(r)
    return redirect(url_for('overview'), code=303)


@app.route('/receipt/edit/<int:id>', methods=['GET', 'POST', 'DELETE'])
def receipt_edit(id):
    match request.method:
        case 'GET':
            r = Receipt.get(id)
            return render_template('receipt_edit.html',
                                   receipt=r, committed=True,
                                   users=users(), categories=categories(), templates={},
                                   alerts=[])
        case 'POST':
            r = Receipt.get(id)
            # FUTURE: fix csrf
            d = request.json
            if d['id'] is None or d['id'] != id:
                abort(400)  # only old receipts
            r_old = r.copy()
            with db.transaction():
                r.timestamp = datetime.fromtimestamp(d['timestamp'])
                r.comment = d['comment']
                r.automatic = False
                r.items = []
                _process_items_json(r, d['items'])
                for tbd in d['deletedItems']:
                    r.delete_item(tbd)
                app.logger.debug(r)
                r.save()
                stats_update_receipt(r_old, r)
            # fall out to return overview
        case 'DELETE':
            Receipt.delete(id)
            # fall out to return overview
    return redirect(url_for('overview'), code=303)


@app.route('/receipt/upload', methods=['GET', 'POST'])
def receipt_upload():
    if request.method == 'GET':
        return render_template('receipt_upload.html')
    if 'file' not in request.files:
        # no file submitted
        return render_template('receipt_upload.html', error='Fel: ingen fil')
    file = request.files['file']
    if not file.filename:
        # empty part with filename; no file submitted (in some browsers)
        return render_template('receipt_upload.html', error='Fel: ingen fil')
    with warnings.catch_warnings(record=True) as ws:
        receipt = parse_receipt(BufferedReader(file))
        alerts = [w.message for w in ws]
    return render_template('receipt_edit.html',
                           receipt=receipt, committed=False,
                           users=users(), categories=categories(), templates={},
                           alerts=alerts)


@app.route('/receipt/template/<int:id>', methods=['GET'])
def receipt_template(id):
    r = Receipt.get(id)
    r.id = -1  # Not strictly necessary but to be careful
    r.timestamp = datetime.now()
    return render_template('receipt_edit.html',
                           receipt=r, committed=False,
                           users=users(), categories=categories(), templates={},
                           alerts=[])


def _process_items_json(r: Receipt, items_json: list):
    for ix, item in enumerate(items_json):
        if item['id'] is None:
            item_obj = Item.from_data(None, item['name'], Decimal(item['quantity']), Decimal(item['price']), item['ean'], item['splits'], item['category'])
        else:
            item_obj = Item.get(item['id'], Decimal(item['quantity']), Decimal(item['price']))
        r.add_item(item_obj, ix)
