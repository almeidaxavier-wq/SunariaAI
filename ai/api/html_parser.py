from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime
from urllib.parse import urlencode
from rich.pretty import pprint
import os, time, rispy, json
import PyPDF2



EXPORT = "/html/body/section/div/div/div[1]/div[2]/div[2]/div[1]/div/a[3]"
SELECT_ALL = "/html/body/section/div/div/div[5]/div/div/form/div[1]/div[2]/div/div[3]/label"
DOWNLOAD = "/html/body/section/div/div/div[5]/div/div/form/div[2]/input"

current_year = datetime.today().year
download_dir = os.path.join(os.path.abspath(os.getcwd()), 'data')

def init_driver():
    chrome_options = Options()

    chrome_options.add_experimental_option('prefs', {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def parse_html_and_send(*keys):
    base_url = "https://search.scielo.org/"

    params = {
        "q": " AND ".join(keys),
        "lang": "pt",
        "count": "30",
        "output":'site',
        "from": "0",
        "sort": '',
        "filter[open_acess]" : "true",
        "format": 'summary'
    }

    driver = init_driver()
    url_search = urlencode(params)

    wait = WebDriverWait(driver, timeout=30)
    driver.get(base_url + '?' + url_search)

    export_link = driver.find_element(By.XPATH, EXPORT)
    wait.until(lambda _ : export_link.is_displayed())
    time.sleep(1)

    export_link.click()    
    export_button = driver.find_element(By.XPATH, SELECT_ALL)
    
    wait.until(lambda _ : export_button.is_displayed())
    time.sleep(1)  

    download_button = driver.find_element(By.XPATH, DOWNLOAD)
    download_button.click()
    time.sleep(3)

    risfile = wait_for_download_complete(download_dir)
    anterior_json = {key:[] for key in keys}
    driver.quit()

    if os.path.exists(os.path.join("data", 'raw.json')):
        try:
            with open(os.path.join(download_dir, 'raw.json'), 'r') as file:
                anterior_json = json.load(file)

            for key in keys:
                anterior_json[key] = []

        except json.decoder.JSONDecodeError as err:
            print(f"An JSON codification error: {err}")

    with open(os.path.join(download_dir, 'raw.json'), 'w') as json_to_write:
        data = None
        with open(os.path.join(download_dir, risfile), 'r', encoding='utf-8') as ris_to_read:
            data = rispy.load(ris_to_read)

        for key in keys:
            anterior_json[key].extend(data)

        pprint(anterior_json)
        time.sleep(10)
        json.dump(anterior_json, json_to_write)

def parse_article(url):
    driver = init_driver()
    wait = WebDriverWait(driver, timeout=30)    
    driver.get(url)

    article = driver.find_element(By.XPATH, '//*[@id="standalonearticle"]/section/div/div') 
    wait.until(lambda _ : article.is_displayed())
    txt = article.text   
    
    driver.quit()
    return txt
    

def wait_for_download_complete(directory, timeout=100, check_interval=1):
    """Aguarda até que o arquivo mais recente termine de baixar"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        files = [f for f in os.listdir(directory) if not f.endswith('.crdownload')]
        if files and not any(f.endswith('.crdownload') for f in os.listdir(directory)):
            return max(
                [os.path.join(directory, f) for f in files],
                key=os.path.getmtime
            )
        print(end_time - time.time())
        time.sleep(check_interval)
    raise TimeoutError("O download não foi concluído no tempo esperado")



if __name__ == '__main__':
    parse_html_and_send('Inteligência Artificial', 'Medicina', 'Cromossomos')
