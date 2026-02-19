from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class BaseCrawler:

    def __init__(self):
        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1200,900")

        service = Service()

        self.driver = webdriver.Chrome(
            service=service,
            options=options,
        )

    def open(self, url: str):
        self.driver.get(url)

    def close(self):
        self.driver.quit()


# def create_google_driver():
#     options = webdriver.ChromeOptions()

#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1200,900")
#     options.add_argument("--disable-blink-features=AutomationControlled")

#     return webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=options,
#     )
