"""Site settings that aren't code."""

OPERATOR = "Agile Release Ltd (Birleşik Krallık)"
CONTACT_EMAIL = "info@agilerelease.co.uk"
PRIVACY_UPDATED = "2026-10-13"

# Google Analytics 4 measurement id. It sets cookies, so it is loaded only after the visitor accepts
# in the consent bar (static/cerez.js). Empty = no Google Analytics and no consent bar.
GA_MEASUREMENT_ID = "G-R9L6S65T75"

# Cloudflare Web Analytics (cookieless, no consent banner needed). Paste the token from
# Cloudflare dash → Analytics & Logs → Web Analytics → Add a site → "JS snippet" (the data-cf-beacon token).
# Empty = no analytics script on the site, and the privacy page says so.
CLOUDFLARE_BEACON_TOKEN = ""
