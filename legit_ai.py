#!/usr/bin/env python3

from time import sleep

import numpy as np

from Battleship import Driver


def check_valid_ship_placement(board, ship, row, col, direction):
    for i in range(ship):
        if direction == 'horizontal':
            if col + i >= len(board[0]) or col + i < 0:
                return False
            if board[row][col + i] not in {' ', '?'}:
                return False
        elif direction == 'vertical':
            if row + i >= len(board) or row + i < 0:
                return False
            if board[row + i][col] not in {' ', '?'}:
                return False
    return True


def get_potential_ship_count(board, row, col, ship_lengths):
    count = 0
    for ship in ship_lengths:
        for i in range(ship):
            # Horizontal
            if check_valid_ship_placement(board, ship, row, col + i - ship + 1, 'horizontal'):
                count += 1
            # Vertical
            if check_valid_ship_placement(board, ship, row + i - ship + 1, col, 'vertical'):
                count += 1
    return count


def shoot():
    # Choose search or attack mode
    board, sunk_ships = driver.get_board()
    mode = 'search'
    for row in board:
        for cell in row:
            if cell.islower():
                mode = 'attack'
                break

    # Figure out what lengths of ships are not sunk
    ship_lengths = []
    for ship_id in sunk_ships:
        if not sunk_ships[ship_id]:
            if ship_id == 'qw':
                ship_lengths.append(5)
            elif ship_id == 'er':
                ship_lengths.append(4)
            elif ship_id in {'tz', 'ui'}:
                ship_lengths.append(3)
            elif ship_id == 'op':
                ship_lengths.append(2)

    # Create heatmap
    heatmap = np.zeros((len(board), len(board[0])), dtype=int)

    # === Search mode ===
    if mode == 'search':
        # TODO: Shoot ? if one exists

        # Populate heatmap
        for row in range(len(board)):
            for col in range(len(board[0])):
                # If space is empty, test all ship locations on it
                if board[row][col] in {' ', '?'}:
                    heatmap[row][col] += get_potential_ship_count(board, row, col, ship_lengths)

        # TODO: Mark all spaces adjacent to sunk ships as invalid

    # === Attack mode ===
    # TODO: this whole thing is garbo and probably needs a rework
    else:
        heatmap = np.zeros((len(board), len(board[0])), dtype=int)
        _break = False
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col].islower():
                    # If none of the adjaced spaces are hits, try to place all ships in adjacent spaces to figure out most likely direction
                    has_adjacent_hit = False
                    if row - 1 >= 0 and board[row - 1][col].islower():
                        has_adjacent_hit = True
                    if row + 1 < len(board) and board[row + 1][col].islower():
                        has_adjacent_hit = True
                    if col - 1 >= 0 and board[row][col - 1].islower():
                        has_adjacent_hit = True
                    if col + 1 < len(board[0]) and board[row][col + 1].islower():
                        has_adjacent_hit = True

                    if not has_adjacent_hit:
                        if row > 1 and board[row - 1][col] in {' ', '?'}:
                            heatmap[row - 1][col] += 1
                            # TODO: using get_potential_ship_count instead of 1 here doesn't work
                        if row + 1 < len(board) and board[row + 1][col] in {' ', '?'}:
                            heatmap[row + 1][col] += 1
                        if col > 1 and board[row][col - 1] in {' ', '?'}:
                            heatmap[row][col - 1] += 1
                        if col + 1 < len(board[0]) and board[row][col + 1] in {' ', '?'}:
                            heatmap[row][col + 1] += 1
                        print('NO ADJACENT HITS')
                        for r in heatmap:
                            print(r)
                        print()

                    # If there is an adjacent hit and a parallel adjaced empty space, shoot there
                    else:
                        print('ADJACENT HIT FOUND')
                        if row - 1 > 0 and board[row - 1][col].islower() and row + 1 < len(board) and board[row + 1][col] in {' ', '?'}:
                            heatmap[row + 1][col] += 1
                        if row + 1 < len(board) and board[row + 1][col].islower() and row - 1 > 0 and board[row - 1][col] in {' ', '?'}:
                            heatmap[row - 1][col] += 1
                        if col - 1 > 0 and board[row][col - 1].islower() and col + 1 < len(board[0]) and board[row][col + 1] in {' ', '?'}:
                            heatmap[row][col + 1] += 1
                        if col + 1 < len(board[0]) and board[row][col + 1].islower and col - 1 > 0 and board[row][col - 1] in {' ', '?'}:
                            heatmap[row][col - 1] += 1

                    # Regardless, break out so it doesn't get overwritten
                    _break = True
                    break
            if _break:
                break

    # === Shoot at most likely space ===
    print(f'{mode} mode')
    for row in heatmap:
        print(row)
    print(ship_lengths)

    max_probability = np.amax(heatmap)
    shot, shotr, shotc = False, 0, 0
    for row in range(len(heatmap)):
        for col in range(len(heatmap[0])):
            if heatmap[row][col] == max_probability:
                driver.shoot(row, col)
                print(row, col, heatmap[row][col])
                shot = True
                shotr = row
                shotc = col
                break
        if shot:
            break

    # === Return response ===
    while board[shotr][shotc] in {' ', '?'}:
        board = driver.get_board()[0]
    if board[shotr][shotc].islower():
        return 'hit'
    if board[shotr][shotc].isupper():
        return board[shotr][shotc]
    if board[shotr][shotc] == '.':
        return 'miss'


if __name__ == '__main__':
    driver = Driver()
    driver.login()

    # Wait for board to load
    driver.wait_for_game_to_load()
    while True:
        driver.close_tips()

        print('My turn:', driver.is_my_turn())
        if driver.is_my_turn():
            result = shoot()
            print(result)
        sleep(5)
