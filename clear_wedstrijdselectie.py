#!/usr/bin/env python3

import os
import sys
from board import Board
from env_loader import load_env_file


def clear_wedstrijdselectie(
    board_name="Voetbal Selectie",
    field_name="Wedstrijdselectie",
):
    # 1. Laad Trello API authenticatie
    load_env_file()
    key = os.getenv("KEY")
    token = os.getenv("TOKEN")

    if not key or not token:
        print("❌ Fout: KEY of TOKEN is niet ingesteld.", file=sys.stderr)
        sys.exit(1)

    # 2. Initialiseer Trello Board
    print(f"🔄 Inladen van Trello board '{board_name}'...")
    board = Board(board_name=board_name, key=key, token=token)

    # 3. Doorloop alle kaarten van het board
    totaal_gecleard = 0

    print(f"\n🧹 Starten met clearen van '{field_name}' op het board...")

    for list_name, trello_list in board.lists.items():
        for card in trello_list.cards:
            huidige_waarde = card.get_custom_field_value(field_name)

            if huidige_waarde is not None:
                try:
                    board.clear_custom_field(card_id=card.id, field_name=field_name)
                    print(f"  ✓ Cleared '{field_name}' voor '{card.name}' (oude waarde: '{huidige_waarde}')")
                    totaal_gecleard += 1
                except Exception as e:
                    print(f"  ❌ Fout bij clearen van '{card.name}': {e}")

    # 4. Samenvatting
    print(f"\n✅ Voltooid! '{field_name}' is succesvol leeggemaakt bij {totaal_gecleard} kaart(en).")


if __name__ == "__main__":
    clear_wedstrijdselectie()