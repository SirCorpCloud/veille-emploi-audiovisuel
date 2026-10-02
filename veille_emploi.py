import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

def scrape_hellowork():
    offers = []
    try:
        url = "https://www.hellowork.com/fr-fr/emploi/metier_audiovisuel-ville_paris-75000.html"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.job-card, .offer-card, [data-testid="job-card"]')[:15]:
            title = job.select_one('h2, h3, .job-title, .offer-title')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_indeed():
    offers = []
    try:
        url = "https://fr.indeed.com/jobs?q=audiovisuel+post-production&l=Paris&radius=25"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.job_seen_beacon, .jobsearch-ResultsList > div, [data-testid="jobTitle"]')[:15]:
            title = job.select_one('h2, h3, .jobTitle, a')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_france_travail():
    offers = []
    try:
        url = "https://www.francetravail.fr/recherche/audiovisuel?lieux=Paris"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.result-item, .offre, article')[:15]:
            title = job.select_one('h2, h3, .title, a')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_linkedin():
    offers = []
    try:
        url = "https://www.linkedin.com/jobs/search/?keywords=audiovisuel%20post-production&location=Paris"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.base-card, .jobs-search-results__list-item, .job-card-container')[:15]:
            title = job.select_one('.base-search-card__title, .job-card-list__title, h3')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_mediakron():
    offers = []
    try:
        url = "https://www.mediakron.fr"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.offre, .job, article')[:15]:
            title = job.select_one('h2, h3, .title')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_ecran_total():
    offers = []
    try:
        url = "https://ecran-total.fr/audiovisuel-job/"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.offre, .job-item, article')[:15]:
            title = job.select_one('h2, h3, .title')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_crews():
    offers = []
    try:
        url = "https://www.crews-education.com/nos-offres"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.job-card, .offre-emploi, article')[:15]:
            title = job.select_one('h2, h3, .title')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_artmedia():
    offers = []
    try:
        url = "https://www.artmedia.co.il/careers"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for job in soup.select('.job-listing, .career-item, .offre')[:15]:
            title = job.select_one('h2, h3, .job-title')
            link = job.find('a')
            if title and link:
                offers.append(f"{title.text.strip()}\n{link.get('href', '')}\n")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def collect_offers():
    sections = {
        "HelloWork": scrape_hellowork(),
        "Indeed": scrape_indeed(),
        "FranceTravail": scrape_france_travail(),
        "LinkedIn": scrape_linkedin(),
        "MediaKron": scrape_mediakron(),
        "EcranTotal": scrape_ecran_total(),
        "Crews": scrape_crews(),
        "Artmedia": scrape_artmedia(),
    }
    body = ""
    for name, offers in sections.items():
        print(f"[{name}] {len(offers)} offres trouvées")
        body += f"\n{'='*40}\n{name}\n{'='*40}\n\n"
        body += "\n\n".join(offers) + "\n\n"
    return body

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
