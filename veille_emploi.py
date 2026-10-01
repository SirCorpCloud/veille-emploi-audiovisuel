import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

SOURCES = {
    "HelloWork": "https://www.hellowork.com/fr-fr/rss?jobFunction=7,8,9&location=Paris",
    "Indeed": "https://fr.indeed.com/rss?q=audiovisuel+OR+post-production+OR+m%C3%A9dias&l=Paris&radius=25",
    "MediaKron": "https://www.mediakron.fr/feed/",
    "FranceTravail": "https://www.francetravail.fr/recherche/audiovisuel?lieux=Paris",
}

def collect_offers():
    offers = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                title = getattr(entry, 'title', 'Sans titre')
                link = getattr(entry, 'link', '')
                published = getattr(entry, 'published', '')
                offers.append(f"[{name}] {title}\n{link}\n{published}\n")
        except Exception as e:
            offers.append(f"[{name}] Erreur: {e}\n")
    return "\n".join(offers)

def send_daily_digest():
    body = collect_offers()
    msg = MIMEMultipart()
    msg['Subject'] = f"Offres Audiovisuel/Post-prod/Médias - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = os.environ.get('EMAIL_FROM')
    msg['To'] = os.environ.get('EMAIL_TO')

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(os.environ.get('EMAIL_FROM'), os.environ.get('EMAIL_PASSWORD'))
        server.send_message(msg)

if __name__ == "__main__":
    send_daily_digest()
