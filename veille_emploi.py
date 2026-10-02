import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
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

def scrape_site(driver, url, selectors, wait_selector=None, timeout=15):
    offers = []
    try:
        driver.get(url)
        if wait_selector:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
        else:
            driver.implicitly_wait(5)
        cards = driver.find_elements(By.CSS_SELECTOR, selectors[0])
        for card in cards[:15]:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, selectors[1])
                link_el = card.find_element(By.CSS_SELECTOR, 'a')
                title = title_el.text.strip()
                link = link_el.get_attribute('href') or ''
                if title:
                    offers.append(f"{title}\n{link}")
            except:
                continue
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def collect_offers():
    driver = get_driver()
    sections = {
        "HelloWork": scrape_site(driver,
            "https://www.hellowork.com/fr-fr/emploi/metier_audiovisuel-ville_paris-75000.html",
            ['.job-card', 'h2, h3'], '.job-card'),
        "Indeed": scrape_site(driver,
            "https://fr.indeed.com/jobs?q=audiovisuel+post-production&l=Paris&radius=25",
            ['.job_seen_beacon', 'h2, h3'], '.job_seen_beacon'),
        "FranceTravail": scrape_site(driver,
            "https://www.francetravail.fr/recherche/audiovisuel?lieux=Paris",
            ['.result-item', 'h2, h3'], '.result-item'),
        "LinkedIn": scrape_site(driver,
            "https://www.linkedin.com/jobs/search/?keywords=audiovisuel%20post-production&location=Paris",
            ['.base-card', '.base-search-card__title'], '.base-card'),
        "EcranTotal": scrape_site(driver,
            "https://ecran-total.fr/audiovisuel-job/",
            ['article', 'h2, h3'], 'article'),
        "Crews": scrape_site(driver,
            "https://www.crews-education.com/nos-offres",
            ['article', 'h2, h3'], 'article'),
        "Artmedia": scrape_site(driver,
            "https://www.artmedia.co.il/careers",
            ['article', 'h2, h3'], 'article'),
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
