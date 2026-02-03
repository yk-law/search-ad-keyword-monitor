from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class BaseCrawler:
    """
    NAVER 전용 크롤러
    (snap chromium 사용)
    """

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.binary_location = "/snap/bin/chromium"
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-software-rasterizer")

        self.driver = webdriver.Chrome(options=options)

    def open(self, url: str):
        self.driver.get(url)

    def close(self):
        self.driver.quit()


def create_google_driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,900")
    options.add_argument("--disable-blink-features=AutomationControlled")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
