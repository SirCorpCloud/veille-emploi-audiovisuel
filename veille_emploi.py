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

ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.environ.get('ADZUNA_APP_KEY')

FRANCE_TRAVAIL_CLIENT_ID = os.environ.get('FT_CLIENT_ID')
FRANCE_TRAVAIL_CLIENT_SECRET = os.environ.get('FT_CLIENT_SECRET')

def get_france_travail_token():
    import requests
    r = requests.post(
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
        data={"grant_type": "client_credentials", "client_id": FRANCE_TRAVAIL_CLIENT_ID, "client_secret": FRANCE_TRAVAIL_CLIENT_SECRET, "scope": "api_offresdemploiv2 o2dsoffre"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15
    )
    print(f"France Travail token response: {r.status_code} {r.text[:200]}")
    return r.json().get('access_token', '')

def get_france_travail_offers():
    offers = []
    try:
        import requests
        token = get_france_travail_token()
        if not token:
            offers.append("Erreur: token France Travail non obtenu")
            return offers
        url = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
        params = {"motsCles": "audiovisuel", "lieux": "Paris", "range": "0-14"}
        r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        data = r.json()
        for offre in data.get('resultats', []):
            title = offre.get('intitule', '')
            link = f"https://www.francetravail.fr/recherche/detail-offre/{offre.get('id', '')}"
            offers.append(f"{title}\n{link}")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def get_adzuna_offers():
    offers = []
    try:
        import requests
        url = f"https://api.adzuna.com/v1/api/jobs/fr/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&what=audiovisuel&where=Paris&results_per_page=15"
        r = requests.get(url, timeout=15)
        print(f"Adzuna response: {r.status_code} {r.text[:200]}")
        data = r.json()
        for result in data.get('results', []):
            title = result.get('title', '')
            link = result.get('redirect_url', '')
            offers.append(f"{title}\n{link}")
    except Exception as e:
        offers.append(f"Erreur: {e}")
    return offers

def get_driver():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(options=opts)

def login_linkedin(driver):
    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(8)
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='email'], input[autocomplete='username']")
        email_field = next((i for i in inputs if i.is_displayed()), None)
        if not email_field:
            raise Exception("LinkedIn email field not visible")
        email_field.click()
        time.sleep(1)
        email_field.send_keys(os.environ.get('LINKEDIN_EMAIL'))
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password'], input[autocomplete='current-password']")
        password_field = next((i for i in inputs if i.is_displayed()), None)
        if not password_field:
            raise Exception("LinkedIn password field not visible")
        password_field.click()
        time.sleep(1)
        password_field.send_keys(os.environ.get('LINKEDIN_PASSWORD'))
        driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button.sign-in-form__submit-btn").click()
        time.sleep(5)
    except Exception as e:
        print(f"LinkedIn login error: {e}")

def login_hellowork(driver):
    try:
        driver.get("https://www.hellowork.com/fr-fr/candidat/connexion-inscription.html#connexion")
        time.sleep(15)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(5)
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        email_field = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email'], input[name='email'], input[autocomplete='email']")))
        email_field.click()
        time.sleep(1)
        email_field.send_keys(os.environ.get('HELLOWORK_EMAIL'))
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password'], input[autocomplete='current-password']")
        password_field.click()
        time.sleep(1)
        password_field.send_keys(os.environ.get('HELLOWORK_PASSWORD'))
        driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button[data-cy='login-submit'], button.login-btn").click()
        time.sleep(5)
    except Exception as e:
        print(f"HelloWork login error: {e}")

def scrape_linkedin(driver):
    offers = []
    try:
        login_linkedin(driver)
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
        login_hellowork(driver)
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
    sections["Indeed"] = get_adzuna_offers()
    sections["FranceTravail"] = get_france_travail_offers()
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
