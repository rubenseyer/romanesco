from pdfminer.high_level import extract_text


def parse(fp):
    for fmt in _formats:
        txt = extract_text(fp, laparams=fmt.laparams())
        if fmt.identify(txt):
            return fmt.parse(txt)
    else:
        raise NotImplementedError


class ReceiptParseWarning(UserWarning):
    pass


from . import ica
from . import willys

_formats = [ica, willys]
