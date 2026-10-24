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

# Google AdSense, switched on in two steps; both empty = no ads and nothing from AdSense on the site.
# 1. ADSENSE_CLIENT: the publisher id ("ca-pub-" and digits) from AdSense → Account → Account information.
#    Adds the google-adsense-account meta tag and ads.txt so Google can review the site. Shows no ads.
# 2. ADSENSE_SLOT, after approval: the id of a responsive display ad unit (Ads → By ad unit → Display ads).
#    Adds ad slots to the price pages and an ads choice to the consent bar; cerez.js loads AdSense only
#    for visitors who accept ads. Set PRIVACY_UPDATED to that day, as the privacy page changes.
ADSENSE_CLIENT = ""
ADSENSE_SLOT = ""

# WhatsApp number shown to advertisers on /reklam/: digits only, with the country code (90… or 44…).
# Empty = e-mail only.
ADVERTISING_WHATSAPP = ""
