import os
from time import sleep

import cv2
import numpy as np
import requests
from selenium import webdriver

from beauty_predict import scores
from secrets import username, password

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


class TinderBot:
    def __init__(self, threshold=6.5):
        self.driver = webdriver.Chrome()
        self.threshold = threshold
        self.beginning = True

    def login(self):
        self.driver.get("https://tinder.com")
        sleep(5)

        fb_button = self.driver.find_element_by_xpath(
            '//*[@id="modal-manager"]/div/div/div/div/div[3]/span/div[2]/button')
        fb_button.click()

        # switch to login popup
        base_window = self.driver.window_handles[0]
        self.driver.switch_to.window(self.driver.window_handles[1])

        email_in = self.driver.find_element_by_xpath('//*[@id="email"]')
        email_in.send_keys(username)

        input_password = self.driver.find_element_by_xpath('//*[@id="pass"]')
        input_password.send_keys(password)

        login_button = self.driver.find_element_by_xpath('//*[@id="u_0_0"]')
        login_button.click()

        self.driver.switch_to.window(base_window)

        sleep(2)
        popup_1 = self.driver.find_element_by_xpath('//*[@id="modal-manager"]/div/div/div/div/div[3]/button[1]')
        popup_1.click()

        sleep(2)
        popup_2 = self.driver.find_element_by_xpath('//*[@id="modal-manager"]/div/div/div/div/div[3]/button[1]')
        popup_2.click()
        sleep(3)

    def like(self, image, name_age_str):
        like_path = os.path.join(APP_ROOT, 'liked_images', f"{name_age_str}.jpg")
        like_btn = self.driver.find_element_by_xpath(
            '//*[@id="content"]/div/div[1]/div/main/div[1]/div/div/div[1]/div/div[2]/div[4]/button')
        like_btn.click()
        cv2.imwrite(like_path, image)

    def dislike(self, image, name_age_str):
        dislike_path = os.path.join(APP_ROOT, 'disliked_images', f"{name_age_str}.jpg")
        dislike_btn = self.driver.find_element_by_xpath(
            '//*[@id="content"]/div/div[1]/div/main/div[1]/div/div/div[1]/div/div[2]/div[2]/button')
        dislike_btn.click()
        cv2.imwrite(dislike_path, image)

    def auto_swipe(self):
        while True:
            try:
                self.like()
            except Exception:
                try:
                    self.close_popup()
                except Exception:
                    self.close_match()

    def choose(self):
        scores, image, name_age_str = self.current_scores()
        choice = "DISLIKE"
        if len(scores) == 0:
            self.dislike(image, name_age_str)
        elif [scr > self.threshold for scr in scores] == len(scores) * [True]:
            self.like(image, name_age_str)  # if there are several faces, they must all have
            choice = "LIKE"  # better score than threshold to be liked
        else:
            self.dislike(image, name_age_str)
        print(f"Scores :{scores, choice} ", self.threshold)

    def ai_swipe(self):
        while True:
            sleep(0.5)
            try:
                self.choose()
            except Exception as err:
                try:
                    self.close_popup()
                except Exception:
                    try:
                        self.close_match()
                    except Exception:
                        print(f"Error: {err}")

    def close_popup(self):
        popup_3 = self.driver.find_element_by_xpath('//*[@id="modal-manager"]/div/div/div[2]/button[2]')
        popup_3.click()

    def close_match(self):
        match_popup = self.driver.find_element_by_xpath('//*[@id="modal-manager-canvas"]/div/div/div[1]/div/div[3]/a')
        match_popup.click()

    def get_image_path(self):
        body = self.driver.find_element_by_xpath('//*[@id="Tinder"]/body')
        body_html = body.get_attribute('innerHTML')
        start_marker = '<div class="Bdrs(8px) Bgz(cv) Bgp(c) StretchedBox" style="background-image: url(&quot;'
        end_marker = '&'

        if not self.beginning:
            url_start = body_html.rfind(start_marker)
            url_start = body_html[:url_start].rfind(start_marker) + len(start_marker)
        else:
            url_start = body_html.rfind(start_marker) + len(start_marker)

        self.beginning = False
        url_end = body_html.find(end_marker, url_start)
        return body_html[url_start:url_end]

    def current_scores(self):
        url = self.get_image_path()
        name_age = self.driver.find_element_by_xpath(
            '// *[@ id="content"]/div/div[1]/div/main/div[1]/div/div/div[1]/div/div[1]/div[3]/div[6]/div/div[1]/div')
        name_age_str = name_age.text.replace('\n', "")
        byte_array = requests.get(url).content
        decoded = cv2.imdecode(np.frombuffer(byte_array, np.uint8), -1)
        score, image = scores(decoded)
        return score, image, name_age_str


if __name__ == "__main__":
    bot = TinderBot()
    bot.login()
    bot.ai_swipe()
