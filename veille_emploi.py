import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

SOURCES = {
    "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords=audiovisuel%20post-production&location=Paris",
    "SACEM": "https://sacem.profils.org/offre-de-emploi/tous-les-flux-rss.aspx",
    "GroupeM6": "https://www.recrutement.groupem6.fr/offre-de-emploi/tous-les-flux-rss.aspx",
    "HelloWork": "https://www.hellowork.com/fr-fr/emploi/metier_audiovisuel-ville_paris-75000.html",
}

def collect_offers():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=opts)
    sections = {}
    for name, url in SOURCES.items():
        offers = []
        try:
            driver.get(url)
            driver.implicitly_wait(5)
            from selenium.webdriver.common.by import By
            cards = driver.find_elements(By.CSS_SELECTOR, '.base-card, .job-card, article, .offre')
            for card in cards[:15]:
                try:
                    title = card.find_element(By.CSS_SELECTOR, 'h2, h3, .title, a').text.strip()
                    link = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') or ''
                    if title:
                        offers.append(f"{title}\n{link}")
                except:
                    continue
        except Exception as e:
            offers.append(f"Erreur: {e}")
        sections[name] = offers
    driver.quit()
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
