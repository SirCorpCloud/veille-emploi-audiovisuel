import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

RSS_SOURCES = {
    "SACEM": "https://sacem.profils.org/handlers/offerRss.ashx?LCID=1036",
    "GroupeM6": "https://www.recrutement.groupem6.fr/handlers/offerRss.ashx?LCID=1036",
}

def get_driver():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    return webdriver.Chrome(options=opts)

def scrape_linkedin(driver):
    offers = []
    try:
        driver.get("https://www.linkedin.com/jobs/search/?keywords=audiovisuel%20post-production&location=Paris")
        time.sleep(8)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        cards = driver.find_elements(By.CSS_SELECTOR, '.base-card, .jobs-search-results__list-item')
        for card in cards[:15]:
            try:
                title = card.find_element(By.CSS_SELECTOR, '.base-search-card__title, .job-card-list__title, h3').text.strip()
                link = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') or ''
                if title:
                    offers.append(f"{title}\n{link}")
            except:
                continue
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def scrape_hellowork(driver):
    offers = []
    try:
        driver.get("https://www.hellowork.com/fr-fr/emploi/metier_audiovisuel-ville_paris-75000.html")
        time.sleep(10)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(5)
        cards = driver.find_elements(By.CSS_SELECTOR, '.job-card, [data-testid="job-card"], .offer-card')
        for card in cards[:15]:
            try:
                title = card.find_element(By.CSS_SELECTOR, 'h2, h3, .job-title').text.strip()
                link = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') or ''
                if title:
                    offers.append(f"{title}\n{link}")
            except:
                continue
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def collect_offers():
    sections = {}
    for name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            offers = []
            for entry in feed.entries[:15]:
                title = getattr(entry, 'title', 'Sans titre')
                link = getattr(entry, 'link', '')
                offers.append(f"{title}\n{link}")
            sections[name] = offers
        except Exception as e:
            sections[name] = [f"Erreur: {e}"]
    driver = get_driver()
    sections["LinkedIn"] = scrape_linkedin(driver)
    sections["HelloWork"] = scrape_hellowork(driver)
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
