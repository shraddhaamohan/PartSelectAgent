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
class PartInformation:
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
        self.inventory_id = self.extract_inventory_id(url)
        self.helpful_Repair_url = f"{url}?currentPage=1&inventoryID={self.inventory_id}&handler=RepairStories&pageSize=5&sortColumn=rating&sortOrder=desc&searchTerm"
        self.question_and_answer_url = f"{url}?currentPage=1&inventoryID={self.inventory_id}&handler=QuestionsAndAnswers&pageSize=10&sortColumn=rating&sortOrder=desc&"
        # Initialize placeholders for results
        self.partInfo = None
        self.userStories = None
        self.qnaList = None
        # Launch threads for each function
        self.run_threads()
        self.driver.quit()
    def run_threads(self):
        """
        Run getPartInfo, get_User_Stories, and getQuestionAndAnswers in separate threads.
        """
        threads = []

        # Thread for getPartInfo
        part_info_thread = threading.Thread(target=self.fetch_part_info)
        threads.append(part_info_thread)

        # Thread for get_User_Stories
        user_stories_thread = threading.Thread(target=self.fetch_user_stories)
        threads.append(user_stories_thread)

        # Thread for getQuestionAndAnswers
        qna_thread = threading.Thread(target=self.fetch_qna)
        threads.append(qna_thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def fetch_part_info(self):
        """
        Fetch part information and store it in self.partInfo.
        """
        self.partInfo = self.getPartInfo(self.url)

    def fetch_user_stories(self):
        """
        Fetch user stories and store them in self.userStories.
        """
        self.userStories = self.getUserStories(self.helpful_Repair_url)

    def fetch_qna(self):
        """
        Fetch Q&A and store it in self.qnaList.
        """
        self.qnaList = self.getQuestionAndAnswers(self.question_and_answer_url)

    def extract_inventory_id(self, url):
        parsed_url = urlparse(url)
        
        # Split the path and extract the inventory ID
        path_parts = parsed_url.path.split('-')
        inventory_id = path_parts[1] if len(path_parts) > 1 else None
        
        return inventory_id

    def getPartInfo(self, url, output_file="output.md"):

        # Set up the WebDriver
        driver = self.driver

        try:
            driver.get(url)
            time.sleep(2)  # Wait for JavaScript to load content

            # Get page source after JavaScript execution
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            image_url = None
            main_image_container = soup.find('div', class_='main-image-container')
            if main_image_container:
                image_link = main_image_container.find('a', id='MagicZoom-PartImage-Images')
                if image_link:
                    image_url = image_link.get('href')
            
            if not image_url:
                thumbnails = soup.find('div', class_='pd__img__thumbs')
                if thumbnails:
                    first_thumbnail = thumbnails.find('a', class_='js-part-img-thumb')
                    if first_thumbnail:
                        image_url = first_thumbnail.get('href')
            
            product_description = soup.find('div', {'class': 'pd__description'})
            product_description = product_description.text.strip() if product_description else "No description available."
            
            troubleshooting_section = soup.select_one('.pd__wrap.row')
            symptoms_it_fixes = ""
            appliances_its_for = ""
            compatible_brands = ""

            if troubleshooting_section:
                sections = troubleshooting_section.find_all('div', class_='col-md-6 mt-3')
                
                for section in sections:
                    title = section.find('div', class_='bold mb-1').get_text(strip=True)
                    content = section.find('div', {'data-collapse-container': True})
                    
                    if content:
                        content = content.get_text(strip=True)
                    else:
                        content = section.contents[-1].strip()

                    if "fixes the following symptoms" in title.lower():
                        symptoms_it_fixes = content
                    elif "works with the following products" in title.lower():
                        if not appliances_its_for:
                            appliances_its_for = content
                        else:
                            compatible_brands = content
            
            videos = soup.find_all('div', {'class': 'yt-video'})
            installation_video = next((video for video in videos if "How Buying OEM Parts" not in video.find('img')['title']), None)
            video_link = f"https://www.youtube.com/watch?v={installation_video['data-yt-init']}" if installation_video else "No installation video available"
            
            price_element = soup.find('span', {'class': 'price pd__price'})
            price = price_element.text.strip() if price_element else "Price not available"
            
            availability_element = soup.find('div', {'class': 'js-partAvailability'})
            availability = availability_element.text.strip() if availability_element else "Availability not specified"
            
            ps_number = soup.find(itemprop="productID")
            ps_number = ps_number.text.strip() if ps_number else "PartSelect Number not available"
            
            mfg_number = soup.find(itemprop="mpn")
            mfg_number = mfg_number.text.strip() if mfg_number else "Manufacturer Part Number not available"
            
            repair_rating_section = soup.select_one('.pd__repair-rating')
            installation_difficulty = "Unknown"
            installation_time = "Unknown"

            if repair_rating_section:
                installation_difficulty_element = repair_rating_section.select_one('.d-flex p.bold')
                if installation_difficulty_element:
                    installation_difficulty = installation_difficulty_element.text.strip()

                installation_time_element = repair_rating_section.select('.d-flex p.bold')[1] if len(repair_rating_section.select('.d-flex p.bold')) > 1 else None
                if installation_time_element:
                    installation_time = installation_time_element.text.strip()
            
            review_section = soup.find('a', class_='bold no-underline js-scrollTrigger', href='#CustomerReviews')
            review_count = "No reviews"
            rating = "No rating"
            if review_section:
                review_count_element = review_section.find('span', class_='rating__count')
                if review_count_element:
                    review_count = review_count_element.text.strip()
                
                rating_element = review_section.find('div', class_='rating__stars__upper')
                if rating_element and 'style' in rating_element.attrs:
                    width_str = rating_element['style']
                    width_percentage = float(width_str.split(':')[1].strip().rstrip('%'))
                    rating = round(width_percentage / 20, 1)
            
            part_info = {
                "type": "part",
                "part_number": ps_number,
                "part_url": url,
                "image_url": image_url,
                "product_description": product_description,
                "symptoms_it_fixes": symptoms_it_fixes,
                "appliances_its_for": appliances_its_for,
                "compatible_brands": compatible_brands,
                "installation_video": video_link,
                "price": price,
                "availability": availability,
                "ps_number": ps_number,
                "mfg_number": mfg_number,
                "installation_difficulty": installation_difficulty,
                "installation_time": installation_time,
                "review_count": review_count,
                "rating": rating
            }
            
            print(f"Retrieved information for part:")
            # print(json.dumps(part_info, indent=2))
            print(part_info)
            

        except Exception as e:
            print(f"Error: {e}")
        
        return part_info

    def getUserStories(self, url):
        # Set up the WebDriver
        driver = self.driver
        try:
            driver.get(url)
            time.sleep(2)  # Wait for JavaScript to load content

            # Get page source after JavaScript execution
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

        # Find all repair stories
            repair_stories = soup.find_all("div", class_="repair-story")

        # Extract the required details
            reviews = []
            for story in repair_stories:
                story_title = story.find("div", class_="repair-story__title").get_text(strip=True)
                
                # Extract the repair instruction
                instruction = story.find("div", class_="repair-story__instruction").find("div", class_="js-searchKeys").get_text(strip=True)
                
                # Extract the difficulty level
                difficulty_element = story.find("div", class_="bold", string="Difficulty Level:")
                difficulty = difficulty_element.find_next_sibling(string=True).strip() if difficulty_element else "Unknown"
                
                # Extract the total repair time
                repair_time_element = story.find("div", class_="bold", string="Total Repair Time:")
                repair_time = repair_time_element.find_next_sibling(string=True).strip() if repair_time_element else "Unknown"
                    
                # Append the extracted data as a dictionary
                reviews.append({
                    "story": f"{story_title} - {instruction}",
                    "difficulty_level": difficulty,
                    "total_repair_time": repair_time
                })

            # Print the extracted reviews
            return reviews
        except Exception as e:
            print(f"Error: {e}")

    def getQuestionAndAnswers(self, url):

        driver = self.driver
        try:
            driver.get(url)
            time.sleep(2)  # Wait for JavaScript to load content

            # Get page source after JavaScript execution
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            
            qna_sections = soup.find_all("div", class_="qna__question")

            # Extract the required details
            qna_list = []
            for section in qna_sections:
                # Extract the question
                question = section.find("div", class_="js-searchKeys").get_text(strip=True)
                
                # Extract the answer
                answer_element = section.find("div", class_="qna__ps-answer__msg")
                answer = answer_element.find("div", class_="js-searchKeys").get_text(strip=True) if answer_element else "No answer available"
                
                # Append the extracted data as a dictionary
                qna_list.append({
                    "question": question,
                    "answer": answer
                })
            
        except Exception as e:
            print(f"Error: {e}")

        return qna_list

    def getPartInfoModel(self):
        """
        Convert the part information to a Pydantic model.
        """
        return PartInfoModel(
                part_number=self.partInfo['part_number'],
                part_url=self.partInfo['part_url'],
                image_url=self.partInfo['image_url'],
                product_description=self.partInfo['product_description'],
                installation_video=self.partInfo['installation_video'],
                price=self.partInfo['price'],
                availability=self.partInfo['availability'],
                ps_number=self.partInfo['ps_number'],
                mfg_number=self.partInfo['mfg_number'],
                installation_difficulty=self.partInfo['installation_difficulty'],
                installation_time=self.partInfo['installation_time'],
                review_count=self.partInfo['review_count'],
                rating=str(self.partInfo['rating']),
            )

    # Example usage
    # url = "https://www.partselect.com/PS11746591-Whirlpool-WP8565925-Rack-Track-Stop.htm"
    # helpful_Repair_url = "https://www.partselect.com/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm?currentPage=1&inventoryID=11752778&handler=RepairStories&pageSize=5&sortColumn=rating&sortOrder=desc&searchTerm"
    # question_and_answer_url = "https://www.partselect.com/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm?currentPage=1&inventoryID=11752778&handler=QuestionsAndAnswers&pageSize=10&sortColumn=rating&sortOrder=desc&" 
    # download_markdown_selenium(url, "page.md")
    # print(getPartInfo(helpful_repair_url))
    # print(get_User_Stories(helpful_repair_url))




