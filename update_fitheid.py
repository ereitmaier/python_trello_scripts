#!/usr/bin/env python3

import os
import sys
import yaml
import requests
from board import Board
from env_loader import load_env_file


def update_fitheid_from_yaml(
    yaml_filepath="trainingen.yaml",
    board_name="Voetbal Selectie",
    field_name="Fitindex",
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

    groepen = data.get("Groep", {})
    if not groepen:
        print("⚠️ Geen 'Groep' gevonden in het YAML-bestand.")
        return

    # 3. Initialiseer Trello Board (gebruikt om kaarten te zoeken)
    print(f"🔄 Inladen van Trello board '{board_name}'...")
    board = Board(board_name=board_name, key=key, token=token)
    
    # Custom Field ID gehaald uit je foutmelding
    custom_field_id = "6aad7994c755dbc7d476382f"

    # 4. Loop door alle groepen (bijv. 1, 2, Overig) en spelers
    totaal_bijgewerkt = 0
    niet_gevonden = []

    for groep_naam, spelers in groepen.items():
        print(f"\n⚙️ Verwerken van groep '{groep_naam}' ({len(spelers)} spelers)...")

        for speler in spelers:
            speler_naam = speler.get("naam", "").strip()
            fitindex = speler.get("fitindex")

            if not speler_naam:
                continue

            # Zoek kaart op het gehele board
            card = board.find_card(speler_naam)

            if card:
                try:
                    # Payload specifiek voor Trello Number Custom Fields
                    payload = {"value": {"number": str(fitindex)}}
                    
                    # Directe API call om board.py te passeren
                    url = f"https://api.trello.com/1/cards/{card.id}/customField/{custom_field_id}/item"
                    response = requests.put(url, json=payload, params={"key": key, "token": token})
                    
                    response.raise_for_status() # Werpt een fout als Trello het weigert

                    print(f"  ✓ Kaart '{card.name}' -> {field_name} = {fitindex}")
                    totaal_bijgewerkt += 1
                except requests.exceptions.HTTPError as e:
                    # Print exact wat Trello niet leuk vindt (de API response body)
                    print(f"  ❌ API Fout bij '{card.name}': {e.response.text}")
                except Exception as e:
                    print(f"  ❌ Algemene fout bij '{card.name}': {e}")
            else:
                print(f"  ⚠️ Kaart voor '{speler_naam}' niet gevonden op board.")
                niet_gevonden.append(speler_naam)

    # 5. Samenvatting
    print(f"\n✅ Klaar! {totaal_bijgewerkt} kaart(en) succesvol bijgewerkt.")
    if niet_gevonden:
        print(f"⚠️ Niet-gevonden spelers ({len(niet_gevonden)}): {', '.join(niet_gevonden)}")


if __name__ == "__main__":
    update_fitheid_from_yaml()