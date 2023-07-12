from __future__ import annotations

import traceback
from typing import TYPE_CHECKING
import warnings

from .adapters import get_adapters, save_adapter
from .. import app, db
from ..model.statistics import stats_new_receipt

if TYPE_CHECKING:
    from ..model.receipt import Receipt


def process_all():
    for aid, adapter in get_adapters().items():
        try:
            it = iter(adapter)
        except Exception as e:
            w = UserWarning(f'Exception while processing {type(adapter).__name__};\n' +
                            ''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            w.__cause__, w.__context__, w.__suppress_context__ = e, e, False
            warnings.warn(w)
            continue
        r: Receipt
        with db.transaction():
            for r in it:
                r.save()
                app.logger.debug(r)
                stats_new_receipt(r)
            save_adapter(aid, adapter)
