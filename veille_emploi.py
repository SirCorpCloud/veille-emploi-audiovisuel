import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    return webdriver.Chrome(options=opts)

def scrape_generic(driver, url, wait_time=10):
    offers = []
    try:
        driver.get(url)
        time.sleep(wait_time)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        cards = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/offre"], a[href*="/emploi"], a[href*="/job"], article, .card, .item, .result')
        for card in cards[:20]:
            try:
                title = card.text.strip().split('\n')[0]
                link = card.get_attribute('href') or ''
                if title and len(title) > 10 and 'audiovisuel' in title.lower() or 'monteur' in title.lower() or 'production' in title.lower() or 'média' in title.lower():
                    offers.append(f"{title}\n{link}")
            except:
                continue
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def collect_offers():
    driver = get_driver()
    sections = {
        "LinkedIn": scrape_generic(driver, "https://www.linkedin.com/jobs/search/?keywords=audiovisuel%20post-production&location=Paris", 8),
        "SACEM": scrape_generic(driver, "https://sacem.profils.org/offre-de-emploi/tous-les-flux-rss.aspx", 10),
        "GroupeM6": scrape_generic(driver, "https://www.recrutement.groupem6.fr/offre-de-emploi/tous-les-flux-rss.aspx", 10),
        "HelloWork": scrape_generic(driver, "https://www.hellowork.com/fr-fr/emploi/metier_audiovisuel-ville_paris-75000.html", 10),
    }
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
