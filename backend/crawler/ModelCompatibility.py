from .models.ModelCompatibilityModel import ModelCompatibilityModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def checkModalCompatibility(model, part):
    model_link = "https://www.partselect.com/Models/"+model+"/"
    searchUrl = "https://www.partselect.com//search/?searchterm="+model+"&SearchMethod=standard"
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
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(searchUrl)
    html = driver.page_source
    searchUrl = "https://www.partselect.com/Models/"+model+"/Parts/?SearchTerm="+part
    driver.get(searchUrl)
    html = driver.page_source
    # with open("test.md", "w") as file:
    #     file.write(html)
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")

    # Find the part information
    part_div = soup.find("div", class_="mega-m__part")
    if part_div:
        # Extract the product link
        product_link = part_div.find("a", class_="mega-m__part__img")["href"]
        product_link = f"https://www.partselect.com{product_link}"

        return ModelCompatibilityModel(
                compatibility = True,
                product_link = product_link,
                model_link = model_link
            )

    # If no part information is found, return False
    return ModelCompatibilityModel(
                compatibility = False,
                product_link = None,
                model_link = model_link
            )
