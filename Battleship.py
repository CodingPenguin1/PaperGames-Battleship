#!/usr/bin/env python
import contextlib
import logging
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager

from random import randint

global driver


def __click__(element):
    global driver

    while True:
        with contextlib.suppress(Exception):
            WebDriverWait(driver, 1).until(EC.element_to_be_clickable(element))
            element.click()
            break


def __wait_until_exists__(search_by, search_key):
    global driver

    while True:
        sleep(1)
        with contextlib.suppress(Exception):
            elements = driver.find_elements(search_by, search_key)
            if len(elements):
                break


def login():
    global driver

    # Click hamburger menu
    __wait_until_exists__(By.CLASS_NAME, 'md-icon-button.burger-menu.md-button.md-ink-ripple')
    hamburger_menu = driver.find_element(By.CLASS_NAME, 'md-icon-button.burger-menu.md-button.md-ink-ripple')
    __click__(hamburger_menu)

    # Click login button
    login_button = driver.find_element(By.CLASS_NAME, 'md-button.ng-isolate-scope.md-ink-ripple')
    __click__(login_button)

    # Switch to login iframe
    sleep(1)
    __wait_until_exists__(By.XPATH, '//iframe[contains(@src,"https://papergames.io/en/battleship")]')
    forms = driver.find_elements(By.XPATH, '//iframe[contains(@src,"https://papergames.io/en/battleship")]')
    for form in forms:
        if 'position: fixed' in form.get_attribute('style'):
            break
    driver.switch_to.frame(form)

    # Load login credentials from file
    with open('login.txt', 'r') as f:
        lines = f.readlines()
        email = lines[0].strip()
        password = lines[1].strip()

    # Enter email
    email_text_box = driver.find_element(By.CLASS_NAME, 'input-with-mask.css-1m5myf8')
    email_text_box.send_keys(email)

    password_text_box = driver.find_element(By.CLASS_NAME, 'input-password_input-element.css-4b01eg')
    password_text_box.send_keys(password)
    password_text_box.send_keys(Keys.ENTER)

    driver.switch_to.default_content()


def get_board():
    global driver

    board_element = driver.find_element(By.ID, 'opponent_board')
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


def get_powerups():
    global driver

    powerups = {'missile': 0, 'fragment-bomb': 0, 'nuclear-bomb': 0}
    powerups_elements = driver.find_elements(By.CLASS_NAME, 'weapon-button.ng-scope')
    for i in range(1, len(powerups_elements)):
        count_badge_element = powerups_elements[i].find_element(By.CLASS_NAME, 'badge.ng-binding')
        count = int(count_badge_element.text)
        keys = list(powerups.keys())
        powerups[keys[i - 1]] = count
    return powerups


def is_my_turn():
    global driver

    return driver.find_element(By.CLASS_NAME, 'attack-text.ng-binding').is_displayed()


def shoot(row, col, powerup='default'):
    global driver

    # Check if shot is valid
    if get_board()[0][row][col] not in {' ', '?'}:
        return False

    # Powerup selection (is not persistent between turns)
    if powerup != 'default':
        powerups_elements = driver.find_elements(By.CLASS_NAME, 'weapon-button.ng-scope')
        powerups = ['missile', 'fragment-bomb', 'nuclear-bomb']
        powerups_elements[powerups.index(powerup) + 1].click()

    # Shoot
    board_element = driver.find_element(By.ID, 'opponent_board')
    cell = board_element.find_element(By.CLASS_NAME, f'cell-{row}-{col}')
    cell.click()

    sleep(2)
    return True


if __name__ == '__main__':
    # Start driver, load webpage, login
    logging.getLogger('WDM').setLevel(logging.NOTSET)  # disable webdriver manager logging
    driver_service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=driver_service)
    driver.get('https://papergames.io/en/battleship')
    login()

    # Wait for board to load
    __wait_until_exists__(By.ID, 'opponent_board')
    while True:
        # Tips show up and they need to go bye bye
        with contextlib.suppress(NoSuchElementException):
            after_hit_tip_close_button = driver.find_element(By.ID, 'nzTour-close')
            after_hit_tip_close_button.click()

        if is_my_turn():
            print(10 * '\n')
            board, sunk_ships = get_board()
            powerups = get_powerups()
            for row in board:
                print(' '.join(row))
            print(sunk_ships)
            print(powerups)
            shoot(randint(0, 9), randint(0, 9), 'missile')
            sleep(3)
