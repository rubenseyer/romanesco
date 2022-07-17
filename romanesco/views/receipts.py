from io import BufferedReader
from datetime import datetime
from decimal import Decimal
from flask import render_template, request, redirect, url_for, abort
from ..model import users, categories, parse_receipt, Receipt, Item, stats_new_receipt, stats_update_receipt
from .. import app, db


@app.route('/receipt/new', methods=['GET', 'POST'])
def receipt_new():
    if request.method == 'GET':
        return render_template('receipt_edit.html', receipt=None, committed=False, users=users(), categories=categories())
    # FUTURE: fix csrf
    d = request.json
    print(d)
    if d['id'] is not None:
        abort(400)  # only new receipts
    if 'deletedItems' in d and d['deletedItems']:
        abort(400)  # can't delete in a new receipt
    with db:
        r = Receipt.new(datetime.fromtimestamp(d['timestamp']), d['comment'])
        _process_items_json(r, d['items'])
        r.save()
        print(r)
        stats_new_receipt(r)
    return redirect(url_for('overview'))


@app.route('/receipt/edit/<int:id>', methods=['GET', 'POST'])
def receipt_edit(id):
    r = Receipt.get(id)
    if request.method == 'GET':
        return render_template('receipt_edit.html', receipt=r, committed=True, users=users(), categories=categories())
    # FUTURE: fix csrf
    # POST update to working receipt:
    d = request.json
    if d['id'] is None or d['id'] != id:
        abort(400)  # only old receipts
    r_old = r.copy()
    with db:
        r.timestamp = datetime.fromtimestamp(d['timestamp'])
        r.comment = d['comment']
        r.automatic = False
        r.items = []
        _process_items_json(r, d['items'])
        for tbd in d['deletedItems']:
            r.delete_item(tbd)
        print(r)
        r.save()
        stats_update_receipt(r_old, r)
    return redirect(url_for('overview'))


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
    receipt = parse_receipt(BufferedReader(file))
    return render_template('receipt_edit.html', receipt=receipt, committed=False, users=users(), categories=categories())


def _process_items_json(r: Receipt, items_json: list):
    for ix, item in enumerate(items_json):
        if item['id'] is None:
            item_obj = Item.from_data(None, item['name'], item['quantity'], item['price'], item['ean'], item['splits'], item['category'])
        else:
            item_obj = Item.get(item['id'], item['quantity'], item['price'])
        r.add_item(item_obj, ix)
