import feedparser
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

SOURCES = {
    "HelloWork": "https://www.hellowork.com/fr-fr/rss?jobFunction=7,8,9&location=Paris",
    "Indeed": "https://fr.indeed.com/rss?q=audiovisuel+OR+post-production+OR+m%C3%A9dias&l=Paris&radius=25",
    "MediaKron": "https://www.mediakron.fr/feed/",
    "FranceTravail": "https://www.francetravail.fr/recherche/audiovisuel?lieux=Paris",
    "LinkedIn": "https://rsshub.app/linkedin/jobs/F/4/audiovisuel%20OR%20post-production%20OR%20m%C3%A9dias/1-2-3/91000003",
    "EcranTotal": "https://ecran-total.fr/audiovisuel-job/feed/",
    "Jobintree": "https://www.jobintree.com/emploi/domaine_audiovisuel.html",
}

SCRAPING_SOURCES = {
    "Crews": "https://www.crews-education.com/nos-offres",
    "Artmedia": "https://www.artmedia.co.il/careers",
    "Audiovisuel-Emploi": "https://ecran-total.fr/audiovisuel-job/",
}

def scrape_crews():
    offers = []
    try:
        r = requests.get(SCRAPING_SOURCES["Crews"], timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.job-card, .offre-emploi, article')[:10]:
            title = job.select_one('h2, h3, .title')
            link = job.find('a')
            if title and link:
                offers.append(f"[Crews] {title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"[Crews] Erreur: {e}\n")
    return offers

def scrape_artmedia():
    offers = []
    try:
        r = requests.get(SCRAPING_SOURCES["Artmedia"], timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.job-listing, .career-item, .offre')[:10]:
            title = job.select_one('h2, h3, .job-title')
            link = job.find('a')
            if title and link:
                offers.append(f"[Artmedia] {title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"[Artmedia] Erreur: {e}\n")
    return offers

def scrape_ecran_total():
    offers = []
    try:
        r = requests.get(SCRAPING_SOURCES["Audiovisuel-Emploi"], timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.offre, .job-item, article')[:10]:
            title = job.select_one('h2, h3, .title')
            link = job.find('a')
            if title and link:
                offers.append(f"[Audiovisuel-Emploi] {title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"[Audiovisuel-Emploi] Erreur: {e}\n")
    return offers

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
    offers.extend(scrape_crews())
    offers.extend(scrape_artmedia())
    offers.extend(scrape_ecran_total())
    return "\n".join(offers)

def send_daily_digest():
    body = collect_offers()
    msg = MIMEMultipart()
    msg['Subject'] = f"Offres Audiovisuel/Post-prod/Médias - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = os.environ.get('EMAIL_FROM')
    msg['To'] = os.environ.get('EMAIL_TO')

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP("smtp.mail.icloud.com", 587) as server:
        server.starttls()
        server.login(os.environ.get('EMAIL_FROM'), os.environ.get('EMAIL_PASSWORD'))
        server.send_message(msg)

if __name__ == "__main__":
    send_daily_digest()
