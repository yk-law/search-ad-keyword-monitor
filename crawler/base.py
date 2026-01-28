from selenium import webdriver


class BaseCrawler:
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
