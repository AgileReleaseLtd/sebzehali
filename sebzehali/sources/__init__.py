"""One module per city. Each exposes CITY (slug), NAME, URL (public source page) and
fetch(date) -> (bulletin_date, rows) or None, where rows are normalize_row() inputs."""

from . import bursa, izmir, konya

ALL = [izmir, bursa, konya]
BY_SLUG = {m.CITY: m for m in ALL}
