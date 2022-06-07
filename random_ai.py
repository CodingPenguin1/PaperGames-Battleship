#!/usr/bin/env python3

from random import randint

from Battleship import Driver
from time import sleep


if __name__ == '__main__':
    driver = Driver()
    driver.login()

    # Wait for board to load
    driver.wait_for_game_to_load()
    while True:
        driver.close_tips()

        if driver.is_my_turn():
            board, sunk_ships = driver.get_board()
            powerups = driver.get_powerups()

            selected_powerup = 'default'
            for powerup in powerups:
                if powerups[powerup] > 0:
                    selected_powerup = powerup

            while True:
                row, col = randint(0, 9), randint(0, 9)
                if board[row][col] in {' ', '?'}:
                    driver.shoot(row, col, powerup=selected_powerup)
                    break
