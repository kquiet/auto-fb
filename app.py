# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Kimberly
# Author Email: mrkid863@gmail.com
# Copyright (C) 2024 Kimberly. All rights reserved.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from dotenv import load_dotenv
import time
import os
import sys
import logging
import logging.config
import yaml


# prepare for logging environment
log_directory = os.path.join(os.getcwd(), 'log')
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
with open('logging.yaml', 'r') as file:
    config = yaml.safe_load(file)
    logging.config.dictConfig(config)
logger = logging.getLogger()

# load environment config file
load_dotenv()
mode = os.getenv('MODE', "test").lower()  # running mode
logger.info('MODE: ' + mode)
hide_browser = os.getenv('HIDE_BROWSER', 'false').lower() in ('true', 'yes')  # headless browser
logger.info('HIDE_BROWSER: ' + str(hide_browser))
user_email = os.getenv('USER_EMAIL')  # facebook login account
user_password = os.getenv('USER_PASSWORD')  # facebook login password
login_switch_account = os.getenv('LOGIN_SWITCH_ACCOUNT')  # the account to switch to after login
logger.info('LOGIN_SWITCH_ACCOUNT: ' + login_switch_account)
club_ignore_list = [str.strip() for str in os.getenv('CLUB_IGNORE_LIST').split(',')]  # black list of club
logger.info('CLUB_IGNORE_LIST: ' + str(club_ignore_list))
post_message = os.getenv('POST_MESSAGE')  # message when publish a post
logger.info('POST_MESSAGE: ' + post_message)
post_url_list = [str.strip() for str in os.getenv('POST_URL_LIST').split(',')]  # the url list of posts
logger.info('POST_URLS: ' + str(post_url_list))


# automatically download ChromeDriver
# determine if running in a PyInstaller bundle
def is_frozen():
    return getattr(sys, 'frozen', False)

driver = None
def open_browser():
    global driver

    # set the path for webdriver
    if is_frozen():
        # if running in a PyInstaller bundle
        wdm_driver_root_path = sys._MEIPASS
    else:
        # if running in a regular Python environment
        wdm_driver_root_path = os.getcwd()
    service = ChromeService(executable_path=ChromeDriverManager(cache_manager=DriverCacheManager(root_dir=wdm_driver_root_path)).install())

    # disable notification
    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    if hide_browser:
        chrome_options.add_argument("--headless")

    logger.info('開啟瀏覽器')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    time.sleep(5)

def login():
    logger.info('開啟臉書首頁')
    driver.get("http://www.facebook.com")
    time.sleep(5)
    assert "Facebook" in driver.title

    logger.info('輸入帳號')
    driver.find_element(by=By.ID, value='email').send_keys(user_email)
    time.sleep(3)

    logger.info('輸入密碼')
    driver.find_element(by=By.ID, value='pass').send_keys(user_password)
    time.sleep(1)

    logger.info('按下登入')
    driver.find_element(by=By.NAME, value='login').click()
    time.sleep(10)

    logger.info('切換帳號')
    driver.find_element(by=By.XPATH, value='//div[@aria-label="你的個人檔案"]').click()
    time.sleep(8)

    logger.info('選擇要切換的帳號: ' + login_switch_account)
    driver.find_element(by=By.XPATH, value='//div[@aria-label="切換為' + login_switch_account + '"]').click()
    time.sleep(8)


# show club for post
def show_club_for_post(post_url: str, club_index: int):
    logger.info('切換到想發的文章: ' + post_url)
    driver.get(post_url)
    time.sleep(10)
    
    logger.info('點選分享')
    driver.find_element(by=By.XPATH, value='//div[@aria-label="傳送給朋友或在個人檔案上發佈。"]').click()
    time.sleep(10)

    logger.info('點選社團')
    #driver.find_element(by=By.XPATH, value="//*[contains(text(), '分享到社團')]").click()
    driver.find_element(by=By.XPATH, value="//span[contains(text(), '社團')]/parent::span/parent::div/parent::div/parent::div/parent::div").click()
    time.sleep(8)

    # starting to move down to have all clubs shown up
    actions = ActionChains(driver)
    while True:
        logger.info('尋找目標社團index: ' + str(club_index))
        club_list = driver.find_elements(By.XPATH, '//div[@role="listitem"]')
        before_moveto_count = len(club_list)
        if (before_moveto_count == 0):
            logger.info('找不到任何社團')
            return False
        elif before_moveto_count > club_index:
            logger.info('已顯示目標社團index: ' + str(club_index) +'，不需再往下移動')
            return True
        else:
            logger.info('往下移之前有 ' + str(before_moveto_count) + " 個社團")
            logger.info('移至最下面的社團以取得更多社團清單')
            actions.move_to_element(club_list[before_moveto_count-1]).perform()
            time.sleep(3)
            new_count = len(driver.find_elements(By.XPATH, '//div[@role="listitem"]'))
            logger.info('往下移之後有 ' + str(new_count) + " 個社團")
            if new_count == before_moveto_count:
                logger.info('不需再往下移')
                return False
            else:
                continue


# perform post
def perform_post(club_element, club_text: str, post_url: str):
    actions = ActionChains(driver)
    logger.info('移至社團: ' + club_text)
    actions.move_to_element(club_element).perform()
    time.sleep(2)
    
    logger.info('點擊社團: ' + club_text)
    club_element.click()
    time.sleep(8)

    logger.info('輸入留言: ' + post_message)
    driver.find_element(by=By.XPATH, value='//div[contains(@class,"notranslate") and @aria-describedby]').send_keys(post_message)
    time.sleep(5)

    # only in normal mode will publish actually
    if mode == "normal":
        driver.find_element(by=By.XPATH, value='//div[@aria-label="發佈"]').click()
        logger.info('社團: ' + club_text + ", 已發佈: " + post_url)
    else:
        logger.info('社團: ' + club_text + ", 以此測試訊息替代發佈: " + post_url)


def start_to_post():
    for post_url in post_url_list:
        club_count = 0
        club_text_list = None
        posted_club_list = []
        failed_club_list = []
        club_index_to_show = 0
        no_club_found = False
        no_more_club_to_post = False
        while True:
            try:
                show_club_for_post(post_url, club_index_to_show)
                club_elements = driver.find_elements(by=By.XPATH, value='//div[@role="listitem"]')
                club_count = len(club_elements)
                club_text_list = [element.text.split('\n', 1)[0].strip() for element in club_elements]
                logger.info('共找到 ' + str(club_count) + ' 個社團')

                # found no club: check it again before breaking while loop
                if club_count == 0:
                    no_more_club_to_post = False
                    if no_club_found:
                        logger.info('連續2次空社團清單')
                        break
                    else:
                        no_club_found = True
                        continue
                else:
                    no_club_found = False
                    if all((element in club_ignore_list or element in posted_club_list) for element in club_text_list if element):
                        if no_more_club_to_post:
                            logger.info('連續2次沒有找到需發佈文章的社團')
                            break
                        elif club_index_to_show < club_count:
                            club_index_to_show = club_count
                            logger.info('當前頁面社團已全發佈過，跳至index: ' + str(club_index_to_show))
                            no_more_club_to_post = False
                            continue
                        else:
                            no_more_club_to_post = True
                            logger.info('當前頁面社團已全發佈過，且index: ' + str(club_index_to_show) + ' 已大於等於當前頁面社團總數')

                for index, element in enumerate(club_text_list):
                    if element and element not in club_ignore_list and element not in posted_club_list:
                        no_more_club_to_post = False
                        club_index_to_show = index
                        club_element = club_elements[index]
                        club_text = club_text_list[index]
                        try:
                            perform_post(club_element, club_text, post_url)
                            posted_club_list.append(club_text)
                            club_index_to_show += 1
                            time.sleep(10)
                        except Exception as e:
                            logger.warning(f"捕捉到錯誤: {e}")
                            # mark club as posted if already in failed list
                            if club_text in failed_club_list:
                                posted_club_list.append(club_text)
                                logger.warning('社團: ' + club_text + ', 最終未能成功發佈: ' + post_url)
                            else:
                                failed_club_list.append(club_text)
                                logger.warning('社團: ' + club_text + ', 此次未能成功發佈: ' + post_url)
                        break
            except Exception as e:
                logger.warning(f"捕捉到錯誤: {e}")
                time.sleep(3)

        logger.info("結束發佈: " + post_url)
        logger.info("需手動發佈: " + ", ".join(set(failed_club_list) & set(posted_club_list)))
        logger.info("已自動發佈: " + ", ".join(set(posted_club_list) - set(failed_club_list)))

open_browser()
login()
start_to_post()