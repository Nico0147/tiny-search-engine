from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.ie.service import Service
from selenium.webdriver.support.wait import WebDriverWait

browser = webdriver.Chrome(service=Service(executable_path='/usr/bin/google-chrome-stable')) # 改为浏览器所在位置

try:
    browser.get('https://www.baidu.com')
    input = browser.find_element_by_id('kw')
    input.send_keys('Python')
    input.send_keys(Keys.ENTER)
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.ID, 'content_left')))
    print(browser.current_url)
    # 输出当前的cookie
    print(browser.get_cookies())
    # 输出网页源代码
    print(browser.page_source)
finally:
    browser.close()