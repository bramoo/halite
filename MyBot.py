#!/usr/bin/env python3
# Python 3.6
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import random
import logging

game = hlt.Game()
game.ready("MyPythonBot")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

ship_targets = {}
ship_returning = {}

def sample(items):
    l = list(items)
    return random.sample(l, len(l))

def set_new_target(ship):
    pos = Position(random.randint(0, game_map.width), random.randint(0, game_map.height))
    ship_targets[ship.id] = pos
    return pos 
    
    
def get_jiggle_dirs(moves):
    all = {Direction.North, Direction.South, Direction.East, Direction.West}

    if len(moves) == 0:
        return set()

    elif len(moves) == 1:
        return all - {moves[0], Direction.invert(moves[0])}
        
    else:
        return all - set(moves)
    
def jiggle(moves):
    for ship_id in moves:
        for move in sample(get_jiggle_dirs(moves[ship_id])):
            ship = me.get_ship(ship_id)
            target = ship.position.directional_offset(move)
            if not game_map[target].is_occupied:
                game_map[target].mark_unsafe(ship)
                return True, ship, move
                
    return False, None, None
            
def find_move(moves):
    for ship_id in moves:
        for move in sample(moves[ship_id]):
            ship = me.get_ship(ship_id)
            target = ship.position.directional_offset(move)
            if not game_map[target].is_occupied:
                game_map[target].mark_unsafe(ship)
                return True, ship, move
                
    return False, None, None
    
def find_swap(moves):
    for ship_id in moves:
        for move in sample(moves[ship_id]):
            ship = me.get_ship(ship_id)
            target = ship.position.directional_offset(move)
            if game_map[target].is_occupied:
                partner = game_map[target].ship
                if partner.id in moves:
                    for p_move in moves[partner.id]:
                        if partner.position.directional_offset(p_move) == ship.position:
                            return True, ship, move, partner, p_move
                            
    return False, None, None, None, None
    
    
def resolve_moves(moves, command_queue):
    # find swaps
    while True:
        swap = find_swap(moves)
        if not swap[0]: break
        
        command_queue.append(swap[1].move(swap[2]))
        command_queue.append(swap[3].move(swap[4]))
        del moves[swap[1].id]
        del moves[swap[3].id]
            
                
    # find simple moves
    while True:
        move = find_move(moves)
        if not move[0]: break
        
        command_queue.append(move[1].move(move[2]))
        del moves[move[1].id]
        
    # jiggle unresolved moves
    while True:
        move = jiggle(moves)
        if not move[0]: break
        
        command_queue.append(move[1].move(move[2]))
        del moves[move[1].id]
        

    
while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    ship_moves = {}
    command_queue = []
    
    # mark shipyard as unoccupied if blocked by opponent
    if game_map[me.shipyard.position].is_occupied:
        shipyard_ship = game_map[me.shipyard.position].ship
        if shipyard_ship.owner != me.id:
            game_map[me.shipyard.position].ship = None
            

    for ship in me.get_ships():
        if not ship.id in ship_targets or ship_targets[ship.id] is None:
            set_new_target(ship)
            
        if not ship.id in ship_returning:
            ship_returning[ship.id] = False
    
        target = ship_targets[ship.id]
                
        if ship.position == target:
            set_new_target(ship)
        
        if game_map.calculate_distance(ship.position, me.shipyard.position) >= constants.MAX_TURNS - game.turn_number - 5:
            ship_returning[ship.id] = True            
        
        if ship_returning[ship.id] and game_map[ship.position].has_structure:
            ship_returning[ship.id] = False
            target = set_new_target(ship)
            ship_moves[ship.id] = game_map.get_unsafe_moves(ship.position, target)
            
        elif ship_returning[ship.id] and game_map[ship.position].halite_amount > 0 and game_map[ship.position].halite_amount / 4 <= 1000 - ship.halite_amount:
            command_queue.append(ship.stay_still())
  
        elif ship.is_full or ship_returning[ship.id]:
            ship_returning[ship.id] = True
            ship_moves[ship.id] = game_map.get_unsafe_moves(ship.position, me.shipyard.position)
        
        elif game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 and game_map[ship.position].halite_amount / 10 <= ship.halite_amount:
            ship_moves[ship.id] = game_map.get_unsafe_moves(ship.position, target)
        else:
            command_queue.append(ship.stay_still())
            
    resolve_moves(ship_moves, command_queue)

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

