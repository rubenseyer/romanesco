from flask import request, redirect, url_for
from ..model import templates as get_templates, new_template, delete_template
from .. import app


@app.route('/template', methods=['GET', 'POST'])
def templates():
    if request.method == 'GET':
        return get_templates()
    # else POST
    new_template(request.json)
    return redirect(url_for('overview'), code=303)


@app.route('/template/<int:id>', methods=['DELETE'])
def templates_delete(id: int):
    delete_template(id)
    return redirect(url_for('overview'), code=303)
