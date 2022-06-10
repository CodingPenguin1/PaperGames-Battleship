#!/usr/bin/env python
import contextlib
import logging
from time import sleep

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager


class Driver:
    def __init__(self):
        # Start driver, load webpage, login
        logging.getLogger('WDM').setLevel(logging.NOTSET)  # disable webdriver manager logging
        driver_service = Service(GeckoDriverManager().install())
        self.webdriver = Firefox(service=driver_service)
        self.webdriver.get('https://papergames.io/en/battleship')

    def __click__(self, element):
        while True:
            with contextlib.suppress(Exception):
                WebDriverWait(self.webdriver, 1).until(EC.element_to_be_clickable(element))
                element.click()
                break

    def __wait_until_exists__(self, search_by, search_key):
        while True:
            sleep(1)
            with contextlib.suppress(Exception):
                elements = self.webdriver.find_elements(search_by, search_key)
                if len(elements):
                    break

    def login(self):
        # Click hamburger menu
        self.__wait_until_exists__(By.CLASS_NAME, 'md-icon-button.burger-menu.md-button.md-ink-ripple')
        hamburger_menu = self.webdriver.find_element(By.CLASS_NAME, 'md-icon-button.burger-menu.md-button.md-ink-ripple')
        self.__click__(hamburger_menu)

        # Click login button
        login_button = self.webdriver.find_element(By.CLASS_NAME, 'md-button.ng-isolate-scope.md-ink-ripple')
        self.__click__(login_button)

        # Switch to login iframe
        sleep(1)
        self.__wait_until_exists__(By.XPATH, '//iframe[contains(@src,"https://papergames.io/en/battleship")]')
        forms = self.webdriver.find_elements(By.XPATH, '//iframe[contains(@src,"https://papergames.io/en/battleship")]')
        for form in forms:
            if 'position: fixed' in form.get_attribute('style'):
                break
        self.webdriver.switch_to.frame(form)

        # Load login credentials from file
        with open('login.txt', 'r') as f:
            lines = f.readlines()
            email = lines[0].strip()
            password = lines[1].strip()

        # Enter email
        email_text_box = self.webdriver.find_element(By.CLASS_NAME, 'input-with-mask.css-1m5myf8')
        email_text_box.send_keys(email)

        password_text_box = self.webdriver.find_element(By.CLASS_NAME, 'input-password_input-element.css-4b01eg')
        password_text_box.send_keys(password)
        password_text_box.send_keys(Keys.ENTER)

        self.webdriver.switch_to.default_content()

    def get_board(self):
        board_element = self.webdriver.find_element(By.ID, 'opponent_board')
        web_board = []
        for row in range(10):
            row_elements = [board_element.find_element(By.CLASS_NAME, f'cell-{row}-{col}') for col in range(10)]
            web_board.append(row_elements)

        board = [[' '] * 10 for _ in range(10)]
        ships_sunk = {'qw': False,  # 5 long, red, "carrier"
                      'er': False,  # 4 long, purple, "battleship"
                      'tz': False,  # 3 long, dark blue, "cruiser"
                      'ui': False,  # 3 long, light blue, "submarine"
                      'op': False,  # 2 long, green, "destroyer"
                      }

        # Grab cell values
        for row in range(len(web_board)):
            for col in range(len(web_board[row])):
                # Check hit
                if len(web_board[row][col].find_elements(By.CLASS_NAME, 'hit.fire.ng-scope')):
                    board[row][col] = web_board[row][col].get_attribute('class').split(' ')[-1][0]  # lower case first letter of 2 letter code for ship is hit
                # Check sink
                elif len(web_board[row][col].find_elements(By.CLASS_NAME, 'hit.skull.magictime.opacityIn.ng-scope.is-destroyed')):
                    board[row][col] = web_board[row][col].get_attribute('class').split(' ')[-1][0].upper()  # capitalize if sunk
                    for key in ships_sunk:
                        if key.startswith(board[row][col].lower()):
                            ships_sunk[key] = True
                # Check miss
                elif len(web_board[row][col].find_elements(By.CLASS_NAME, 'magictime.opacityIn.intersection.ng-scope')):
                    board[row][col] = '.'
                # Check ?
                elif len(web_board[row][col].find_elements(By.CLASS_NAME, 'fa.fa-question.gift.fa-2x.magictime.tinIn.ng-scope')):
                    board[row][col] = '?'

        return board, ships_sunk

    def get_powerups(self):
        powerups = {'missile': 0, 'fragment-bomb': 0, 'nuclear-bomb': 0}
        powerups_elements = self.webdriver.find_elements(By.CLASS_NAME, 'weapon-button.ng-scope')
        for i in range(1, len(powerups_elements)):
            count_badge_element = powerups_elements[i].find_element(By.CLASS_NAME, 'badge.ng-binding')
            count = int(count_badge_element.text)
            keys = list(powerups.keys())
            powerups[keys[i - 1]] = count
        return powerups

    def is_my_turn(self):
        sleep(2)  # This is important
        # TODO: make this sleep not important
        try:
            self.webdriver.find_element(By.CLASS_NAME, 'header.ng-animate.attack-add.blink-add.attack.blink.attack-add-active.blink-add-active')
            return True
        except NoSuchElementException:
            try:
                self.webdriver.find_element(By.CLASS_NAME, 'header.attack.blink')
                return True
            except NoSuchElementException:
                return False

    def shoot(self, row, col, powerup='default'):
        # Check if shot is valid
        board_element = self.webdriver.find_element(By.ID, 'opponent_board')
        cell = board_element.find_element(By.CLASS_NAME, f'cell-{row}-{col}')
        cell_text = cell.get_attribute('class').strip()
        cell_is_miss = bool(len(cell.find_elements(By.CLASS_NAME, 'magictime.opacityIn.intersection.ng-scope')))
        print(f'{cell_text}')
        print(f'cell-{row}-{col}')
        print(cell_text != f'"cell-{row}-{col}"')
        print(cell_is_miss)
        if cell_text != f'cell-{row}-{col}' or cell_is_miss:
            return False

        # Powerup selection (is not persistent between turns)
        if powerup != 'default':
            powerups_elements = self.webdriver.find_elements(By.CLASS_NAME, 'weapon-button.ng-scope')
            powerups = ['missile', 'fragment-bomb', 'nuclear-bomb']
            powerups_elements[powerups.index(powerup) + 1].click()

        # Shoot
        cell.click()

        sleep(2)  # This is important
        # TODO: make this sleep not important
        return True

    def close_tips(self):
        # Tips show up and they need to go bye bye
        with contextlib.suppress(NoSuchElementException):
            after_hit_tip_close_button = self.webdriver.find_element(By.ID, 'nzTour-close')
            after_hit_tip_close_button.click()

    # def play_with_friend(self):
    #     self.__wait_until_exists__(By.CLASS_NAME, 'btn.btn-success.btn-lg.mb-2.ng-binding.ng-isolate-scope')
    #     buttons = self.webdriver.find_elements(By.CLASS_NAME, 'btn.btn-success.btn-lg.mb-2.ng-binding.ng-isolate-scope')
    #     for button in buttons:
    #         print(button.text.lower())
    #         if button.text.lower() == 'play with a friend':
    #             sleep(5)
    #             print('click')
    #             button.click()
    #             print('clicked')
    #             break

    # def play_online(self):
    #     self.__wait_until_exists__(By.CLASS_NAME, 'btn.btn-success.btn-lg.mb-2.ng-binding.ng-isolate-scope')
    #     buttons = self.webdriver.find_elements(By.CLASS_NAME, 'btn.btn-success.btn-lg.mb-2.ng-binding.ng-isolate-scope')
    #     for button in buttons:
    #         if button.text.lower() == 'find opponent':
    #             self.__click__(button)
    #             break

    def wait_for_game_to_load(self):
        self.__wait_until_exists__(By.ID, 'opponent_board')
