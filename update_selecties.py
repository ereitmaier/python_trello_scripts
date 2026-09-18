#!/usr/bin/env python3

import os
import sys
import yaml
from board import Board
from env_loader import load_env_file


def update_wedstrijdselectie_from_yaml(
    yaml_filepath="selecties.yaml",
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

    # 2. Lees het YAML-bestand in
    if not os.path.exists(yaml_filepath):
        print(f"❌ Fout: Bestand '{yaml_filepath}' niet gevonden.", file=sys.stderr)
        sys.exit(1)

    with open(yaml_filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    selecties = data.get("Selecties", {})
    if not selecties:
        print("⚠️ Geen 'Selecties' gevonden in het YAML-bestand.")
        return

    # 3. Initialiseer Trello Board
    print(f"🔄 Inladen van Trello board '{board_name}'...")
    board = Board(board_name=board_name, key=key, token=token)

    # 4. Loop door alle selecties (bijv. Vr2, Vr1, etc.) en namen
    totaal_bijgewerkt = 0
    niet_gevonden = []

    for selectie_naam, spelers in selecties.items():
        print(f"\n⚙️ Verwerken van selectie '{selectie_naam}' ({len(spelers)} spelers)...")

        for speler_naam in spelers:
            speler_naam_clean = speler_naam.strip()

            # Zoek kaart op het gehele board (hoofdletterongevoelig)
            card = board.find_card(speler_naam_clean)

            if card:
                try:
                    # Update het Custom Field op de gevonden kaart
                    board.update_custom_field(
                        card_id=card.id,
                        field_name=field_name,
                        value=selectie_naam,
                    )
                    print(f"  ✓ Kaart '{card.name}' -> {field_name} = '{selectie_naam}'")
                    totaal_bijgewerkt += 1
                except Exception as e:
                    print(f"  ❌ Fout bij updaten van '{card.name}': {e}")
            else:
                print(f"  ⚠️ Kaart voor '{speler_naam_clean}' niet gevonden op board.")
                niet_gevonden.append(speler_naam_clean)

    # 5. Samenvatting
    print(f"\n✅ Klaar! {totaal_bijgewerkt} kaart(en) succesvol bijgewerkt.")
    if niet_gevonden:
        print(f"⚠️ Niet-gevonden spelers ({len(niet_gevonden)}): {', '.join(niet_gevonden)}")


if __name__ == "__main__":
    update_wedstrijdselectie_from_yaml()