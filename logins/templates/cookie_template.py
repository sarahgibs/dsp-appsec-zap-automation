from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os
from zapv2 import ZAPv2


def set_chrome_options(proxy) -> None:
    """Adds chrome options. 
    Proxy is required for sending the traffic through ZAP.
    """
    chrome_options = Options()
    #When using this in a container, uncomment the lines below
    #chrome_options.add_argument("--headless")
    #chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--proxy-server=" + proxy)
    chrome_options.add_argument("--allow-insecure-localhost")
    return chrome_options

def login(proxy, env):
    """
    Webdriver script for logging into an app with cookie auth. 
    """
    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps["acceptInsecureCerts"] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)

    #There's some flexibility here. env could contain the entire domain of your site.
    #Or env could contain just the part that changes between testing environments.
    #site needs to contain domain:port, such as localhost:3000 
    site = env
    url = "https://"+site
    authtype = "cookie"

    #If your cookie is not in the OWASP ZAP default cookie list, you will need to add it as a default token
    #The below code is only for use when that's needed.

    # zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    # cookieName="Your Session Cookie Name Goes Here"
    # zap.httpsessions.add_default_session_token(cookieName)

    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    logged_in = False

    for attempt in range(max_retries):
        try:
            driver.get(url)
            #Your webdriver code goes here. 
            #It should log into the website.

            


            


        except Exception as err:
            print("Exception occurred: {0}".format(err))
        else:
            print("logged in")
            logged_in = True
            break
    driver.close()
    return site, authtype, logged_in


