#!/usr/bin/env python3

import contextlib
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


def get_potential_ship_count_intersecting(board, tar_row, tar_col, hit_row, hit_col, ship_lengths):
    count = 0
    # Horizontal
    if tar_row == hit_row:
        for ship in ship_lengths:
            ship_col_coords = list(range(ship))
            while ship_col_coords[-1] < len(board[0]):
                if tar_col in ship_col_coords and hit_col in ship_col_coords:
                    count += 1
                for i in range(len(ship_col_coords)):
                    ship_col_coords[i] += 1

    # Vertical
    if tar_col == hit_col:
        for ship in ship_lengths:
            ship_row_coords = list(range(ship))
            while ship_row_coords[-1] < len(board):
                if tar_row in ship_row_coords and hit_row in ship_row_coords:
                    count += 1
                for i in range(len(ship_row_coords)):
                    ship_row_coords[i] += 1
    return count


def generate_attack_mode_heatmap(board, ship_lengths):
    # Array of numbers is easier to work with than a board, so translate the board to ints
    int_board = np.zeros((len(board), len(board[0])), dtype=int)
    for row in range(len(board)):
        for col in range(len(board[0])):
            # Make hits 1
            if board[row][col].islower():
                int_board[row][col] = 1
            # Misses -1
            elif board[row][col] == '.':
                int_board[row][col] = -1
            # And all sunk ships -1 with misses adjacent to them
            elif board[row][col].isupper():
                int_board[row][col] = -1
                if row > 0:
                    int_board[row - 1][col] = -1
                if row < len(int_board) - 1:
                    int_board[row + 1][col] = -1
                if col > 0:
                    int_board[row][col - 1] = -1
                if col < len(int_board[0]) - 1:
                    int_board[row][col + 1] = -1

    # If there's a lone hit, update the heatmap on adjacent cells with probabilities for ships
    heatmap = np.zeros((len(board), len(board[0])), dtype=int)
    for row in range(len(int_board)):
        for col in range(len(int_board[0])):
            if int_board[row][col] == 1:
                adjacent_hit = False
                if row > 0 and int_board[row - 1][col] == 1:
                    adjacent_hit = True
                if row < len(int_board) - 1 and int_board[row + 1][col] == 1:
                    adjacent_hit = True
                if col > 0 and int_board[row][col - 1] == 1:
                    adjacent_hit = True
                if col < len(int_board[0]) - 1 and int_board[row][col + 1] == 1:
                    adjacent_hit = True

                if not adjacent_hit:
                    if row > 0 and int_board[row - 1][col] == 0:
                        heatmap[row - 1][col] = get_potential_ship_count_intersecting(board, row - 1, col, row, col, ship_lengths)
                    if row < len(int_board) - 1 and int_board[row + 1][col] == 0:
                        heatmap[row + 1][col] = get_potential_ship_count_intersecting(board, row + 1, col, row, col, ship_lengths)
                    if col > 0 and int_board[row][col - 1] == 0:
                        heatmap[row][col - 1] = get_potential_ship_count_intersecting(board, row, col - 1, row, col, ship_lengths)
                    if col < len(int_board[0]) - 1 and int_board[row][col + 1] == 0:
                        heatmap[row][col + 1] = get_potential_ship_count_intersecting(board, row, col + 1, row, col, ship_lengths)
                    print('lone hit')
                    return heatmap

    # If there's no lone hit, find hits with adjacent hits and predict direction
    # Check all 4 directions for an adjacent hit and mark the nearest empty spaces adjacent to the hit block along that axis
    print('multiple hits')
    for row in range(len(int_board)):
        for col in range(len(int_board[0])):
            if int_board[row][col] == 1:
                # If hit to the left or right
                if (row > 0 and int_board[row - 1][col] == 1) or (row < len(int_board) and int_board[row + 1][col] == 1):
                    # Check for and mark potential left hit
                    with contextlib.suppress(IndexError):
                        for i in range(max(ship_lengths)):
                            if int_board[row - i][col] == -1:
                                break
                            elif int_board[row - i][col] == 0:
                                heatmap[row - i][col] = 1
                                break

                    # Check for and mark potential right hit
                    with contextlib.suppress(IndexError):
                        for i in range(max(ship_lengths)):
                            if int_board[row + i][col] == -1:
                                break
                            elif int_board[row + i][col] == 0:
                                heatmap[row + i][col] = 1
                                break

                # If hit to the top or bottom
                if (col > 0 and int_board[row][col - 1] == 1) or (col < len(int_board[0]) and int_board[row][col + 1] == 1):
                    # Check for and mark potential top hit
                    with contextlib.suppress(IndexError):
                        for i in range(max(ship_lengths)):
                            if int_board[row][col - i] == -1:
                                break
                            elif int_board[row][col - i] == 0:
                                heatmap[row][col - i] = 1
                                break

                    # Check for and mark potential bottom hit
                    with contextlib.suppress(IndexError):
                        for i in range(max(ship_lengths)):
                            if int_board[row][col + i] == -1:
                                break
                            elif int_board[row][col + i] == 0:
                                heatmap[row][col + i] = 1
                                break
    for row in int_board:
        print(' '.join([str(r) for r in row]))
    return heatmap


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

        # Mark all spaces adjacent to sunk ships as invalid
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col].isupper():
                    if row > 0 and board[row - 1][col] == ' ':
                        board[row - 1][col] = '.'
                    if row < len(board) - 1 and board[row + 1][col] == ' ':
                        board[row + 1][col] = '.'
                    if col > 0 and board[row][col - 1] == ' ':
                        board[row][col - 1] = '.'
                    if col < len(board[0]) - 1 and board[row][col + 1] == ' ':
                        board[row][col + 1] = '.'

        # Populate heatmap
        for row in range(len(board)):
            for col in range(len(board[0])):
                # If space is empty, test all ship locations on it
                if board[row][col] in {' ', '?'}:
                    heatmap[row][col] += get_potential_ship_count(board, row, col, ship_lengths)

    # === Attack mode ===
    else:
        heatmap = generate_attack_mode_heatmap(board, ship_lengths)

    # === Shoot at most likely space ===
    print(f'{mode} mode')
    # for row in board:
    #     print(' '.join(row))
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

        # print('My turn:', driver.is_my_turn())
        if driver.is_my_turn():
            result = shoot()
            print(result)
        # sleep(5)
        # input()
