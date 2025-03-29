from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import html2text
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import threading

from .models.PartInfoModel import PartInfoModel

from urllib.parse import urljoin, quote

from .models.ModelInfoModel import ModelInfoModel
from .models.ModelInfoModel import Manual
from .models.ModelInfoModel import Diagram
from .models.ModelInfoModel import Video

def url_join(base, path):
    return urljoin(base, path)

class ModelInformation:
    def __init__(self, url):
        # Chrome Setup
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Enable headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36")
        chrome_options.add_argument("window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
        self.url = url

        # Initialize placeholders for results
        self.modelInfo = None
        self.fetch_model_info()
        self.driver.quit()


    def fetch_model_info(self):
        """
        Fetch model information using Selenium and BeautifulSoup.
        """
        self.driver.get(self.url)
        time.sleep(2)  # Allow the page to load
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Extract model name
        model_name = soup.find('h1', {'class': 'title-main'})
        model_name = model_name.text.strip() if model_name else "Model name not found"

        # Extract manuals
        manuals = []
        manual_section = soup.find('div', class_='d-flex flex-wrap mt-2 mb-4')
        if manual_section:
            manual_items = manual_section.find_all('a', class_='mega-m__manuals')
            for item in manual_items:
                title = item.find('div', class_='mega-m__manuals__title')
                title = title.text.strip() if title else "Unknown title"
                url = item.get('href', '')
                if url:
                    manuals.append({
                        "title": title,
                        "url": url
                    })

        # Extract diagrams
        diagrams = []
        diagram_section = soup.find('div', class_='row mb-3')
        if diagram_section:
            diagram_items = diagram_section.find_all('a', class_='no-underline d-block')
            for item in diagram_items:
                title = item.find('span')
                title = title.text.strip() if title else "Unknown title"
                url = item.get('href', '')
                if url:
                    diagrams.append({
                        "title": title,
                        "url": url_join(self.url, url)
                    })

        # Extract videos
        videos = []
        videos_url = url_join(self.url, 'Videos/')
        while videos_url:
            videos_response = self.driver.page_source
            videos_soup = BeautifulSoup(videos_response, 'html.parser')
            video_items = videos_soup.find_all('div', class_='yt-video')
            for item in video_items:
                title = item.find('img')
                title = title['title'] if title and 'title' in title.attrs else "Unknown title"
                video_id = item.get('data-yt-init')
                if video_id:
                    videos.append({
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })

            next_page = videos_soup.find('li', class_='next')
            next_link = next_page.find('a') if next_page else None
            if next_link and 'href' in next_link.attrs:
                videos_url = url_join(videos_url.split('?')[0], next_link['href'])
            else:
                videos_url = None

        # Extract parts URL
        parts_url = url_join(self.url, 'Parts/')

        # Compile model information
        model_info = {
            "type": "model",
            "model_name": model_name,
            "model_url": self.url,
            "manuals": manuals,
            "diagrams": diagrams,
            "videos": videos,
            "parts_url": parts_url
        }

        print(f"Retrieved information for model: {model_name}")
        self.modelInfo = model_info
    
    def getmodelInfoModel(self):
        return ModelInfoModel(
            type=self.modelInfo["type"],
            model_name=self.modelInfo["model_name"],
            model_url=self.modelInfo["model_url"],
            manuals=[Manual(**manual) for manual in self.modelInfo["manuals"]],
            diagrams=[Diagram(**diagram) for diagram in self.modelInfo["diagrams"]],
            videos=[Video(**video) for video in self.modelInfo["videos"]],
            parts_url=self.modelInfo["parts_url"]
    )

    
        






