from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

class TroubleshootInformation:
    def __init__(self, url):
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
        self.symptom_data = self.get_symptom_list()
        self.driver.quit()


    def get_symptom_list(self):
        """
        It will return an array of  dictionarys. The dictionaries are of the format:
        {
            title: "",
            title_desc: "",
            video_link: ""
            solutions: [{
                ...
            }]
        }
        """
        # Set up the WebDriver
        driver = self.driver
        all_symptoms = []

        try:
            driver.get(self.url)
            time.sleep(2)  # Wait for JavaScript to load content

            # Get page source after JavaScript execution
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            main_symptom_container = soup.find("div", class_="symptom-list")
            # print(main_symptom_container)
            if main_symptom_container:
                symptom_links = main_symptom_container.find_all("a", class_="row")
                # print(symptom_links)
                for link in symptom_links:
                    title = link.find("h3", class_="title-md mb-3").text.strip()
                    description = link.find("p").text.strip()
                    href = link.get('href')
                    symptom = {
                        "title": title,
                        "description": description,
                        "href": href,
                    }
                    symptom_url = self.url + "/" + href.strip().split("/")[-2]
                    video_link, resolutions = self.parse_symptom(symptom_url)
                    symptom["video_link"] = video_link
                    symptom["solutions"] = resolutions
                    all_symptoms.append(symptom)

            return all_symptoms

        except:
            print("Error loading the page.")

    def parse_symptom(self, symptom_url):
        driver = self.driver
        try:
            driver.get(symptom_url)
            time.sleep(2)  # Wait for JavaScript to load content
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            youtube_video = soup.find("img", class_="yt-video__thumb b-lazy b-loaded loaded")
            if youtube_video:
                video_link = youtube_video.get('src')
            
            symptom_details = []
            symptom_resolutions = soup.find("div", class_="symptom-list")
            
            if symptom_resolutions:
                section_titles = symptom_resolutions.find_all("h2", class_="section-title")
                
                for section_title in section_titles:
                    title = section_title.text.strip()
                    section_id = section_title.get('id', '')
                    
                    description_div = section_title.find_next("div", class_="symptom-list__desc row mb-4")
                    
                    if description_div:
                        content_div = description_div.find("div", class_="col-lg-6")
                        if content_div:
                            full_content = ' '.join(text.strip() for text in content_div.stripped_strings)
                            
                            # Store the details
                            symptom_details.append({
                                "part": section_id,
                                "description": full_content
                            })
            return video_link, symptom_details
        except:
            print("Error loading the symptom page.")
