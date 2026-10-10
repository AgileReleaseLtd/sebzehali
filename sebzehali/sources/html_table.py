import html
import re


def tables(page):
    """Every <table> in the page as a list of rows, each a list of cell texts."""
    out = []
    for t in re.findall(r"(?is)<table.*?</table>", page):
        rows = []
        for r in re.findall(r"(?is)<tr.*?</tr>", t):
            cells = [text(c) for c in re.findall(r"(?is)<t[hd][^>]*>(.*?)</t[hd]>", r)]
            if cells:
                rows.append(cells)
        out.append(rows)
    return out


def text(fragment):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", fragment)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()
