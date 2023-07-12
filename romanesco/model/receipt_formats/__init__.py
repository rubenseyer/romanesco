from io import StringIO
import string

from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage


def parse(fp):
    for fmt in _formats:
        # pdfminer/high_level.py L148
        with StringIO() as output_string:
            rsrcmgr = PDFResourceManager(caching=True)
            device = TextConverter(rsrcmgr, output_string, codec='utf-8', laparams=fmt.laparams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.get_pages(
                    fp,
                    pagenos=None,
                    maxpages=0,
                    password='',
                    caching=True,
            ):
                interpreter.process_page(page)
            txt = output_string.getvalue()

            if len(txt) > 0 and txt[0] not in string.printable:
                # Try to recover bugged Willys files. This is a big hack
                try:
                    rsrcmgr._cached_fonts[3].unicode_map.cid2unichr = fmt.CID2UNICHR
                except Exception:
                    # Ignore and continue
                    continue
                output_string.truncate(0)
                output_string.seek(0)
                for page in PDFPage.get_pages(
                        fp,
                        pagenos=None,
                        maxpages=0,
                        password='',
                        caching=True,
                ):
                    interpreter.process_page(page)
                txt = output_string.getvalue()

        if fmt.identify(txt):
            return fmt.parse(txt)
    else:
        raise NotImplementedError


class ReceiptParseWarning(UserWarning):
    pass


from . import ica
from . import willys

_formats = [ica, willys]
