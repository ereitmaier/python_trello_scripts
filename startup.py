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

