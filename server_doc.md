# Messages:
## Sent from the server to assign a player their ID
type: player_id
    player: int
    
# Sent to the server to update the game state of the sender
type: game_state
    state: string (GAME_STATE)
    sender: int (player_id)
    
# Sent from the server to both players to set the ship count
type: set_ship_count
    count: int
    
# Sent from the server once both players have placed and locked in their ships
type: all_ships_locked
    --No Attributes--
    
# When sent to the server, it forwards it to the other player to represent a bomb being shot
type: bomb
    row: int
    col: int
    
# Received after sending the "bomb" message. Lets user know if their bomb hit/miss, sunk a ship and/or ended the game
type: hit_status
    row: int
    col: int
    status: bool
    sunk: bool
    all_sunk: bool
