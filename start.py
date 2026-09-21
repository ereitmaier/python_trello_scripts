import os
from board import Board
from env_loader import load_env_file

# Laad omgevingsvariabelen
load_env_file()

# Initialiseer het Board object
board = Board(
    board_name="Voetbal Selectie", 
    key=os.getenv("KEY"), 
    token=os.getenv("TOKEN")
)

# --- AANROEPEN VAN INSTANTIEMETHODES ---

# 1. Bekijk alle lijsten op het board (-L)
#board.print_list_names()

# 2. Toon specifieke lijst met opties (-l "Roster Pool")
#board.print_samenstelling(list_name="Roster Pool", show_positions=True)

# 3. Toon alle trainingsgroepen of specifieke groep (-t 1)
#board.show_training_groups(groups=1, show_comments=True)

# 4. Toon alle match squads (-m)
#board.show_match_squads()

# 5. Zoek een specifieke speler (-s "Pietje")
#board.search_card("Pietje", show_positions=True, show_comments=True)

# 6. Reset uitvoeren (-r)
#board.reset_to_roster_pool()
