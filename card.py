import requests
from datetime import datetime

class Card:
    """Representeert een Trello-kaart als onderdeel van een TrelloList."""

    def __init__(self, card_id, name, custom_field_items, labels, auth, trello_list=None):
        self.id = card_id
        self.name = name
        self.custom_field_items = custom_field_items
        self.labels = [
            label.get("name") or label.get("color") for label in labels
        ]
        self.auth = auth
        self.trello_list = trello_list  # Onderdeel van TrelloList

    @property
    def board(self):
        """Geeft het bovenliggende board terug via de lijst waartoe de kaart behoort."""
        return self.trello_list.board if self.trello_list else None

    def get_custom_field_value(self, field_name, debug=False):
        """Haalt de actuele waarde op van een Custom Field op basis van de veldnaam."""
        if not self.board:
            return None

        field_def = self.board.custom_fields.get(field_name.lower().strip())

        if not field_def:
            if debug:
                print(
                    f"   ⚠️ DEBUG: Veld '{field_name}' niet gevonden op board."
                )
            return None

        cf_id = field_def["id"]
        for item in self.custom_field_items:
            if item.get("idCustomField") == cf_id:
                if "idValue" in item:
                    return field_def["options"].get(item["idValue"])
                val_obj = item.get("value", {})
                for key in ["number", "text", "checked", "date"]:
                    if key in val_obj:
                        return val_obj[key]

        return None

    def get_position_code(self):
        """Zet de labels van de kaart om naar de opmaak [KVMA]."""
        labels_lower = [l.lower() for l in self.labels if l]
        k = "K" if "keeper" in labels_lower else "-"
        v = "V" if "verdediger" in labels_lower else "-"
        m = "M" if "middenvelder" in labels_lower else "-"
        a = "A" if "aanvaller" in labels_lower else "-"
        return f"[{k}{v}{m}{a}]"

    def get_position_priority(self):
        """Bepaalt de sorteerprioriteit van de speler (K=1, V=2, M=3, A=4, Overig=5)."""
        labels_lower = [l.lower() for l in self.labels if l]
        if "keeper" in labels_lower:
            return 1
        if "verdediger" in labels_lower:
            return 2
        if "middenvelder" in labels_lower:
            return 3
        if "aanvaller" in labels_lower:
            return 4
        return 5

    def move_to(self, target_list):
        """Verplaatst de kaart naar een andere TrelloList en update de referentie."""
        url = f"https://api.trello.com/1/cards/{self.id}"
        response = requests.put(
            url, params={**self.auth, "idList": target_list.id}
        )
        response.raise_for_status()

        # Update in-memory referentie en lijsten
        if self.trello_list and self in self.trello_list.cards:
            self.trello_list.cards.remove(self)

        target_list.add_card(self)
        print(f"✓ Kaart '{self.name}' verplaatst naar '{target_list.name}'")

    def get_comments(self, newest_first=True):
        """Haalt alle comments van de kaart op via de Trello API."""
        url = f"https://api.trello.com/1/cards/{self.id}/actions"
        params = {**self.auth, "filter": "commentCard"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        actions = response.json()

        comments = []
        for action in actions:
            raw_date = action.get("date")

            if raw_date:
                dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%d-%m-%Y %H:%M")
            else:
                formatted_date = "Onbekende datum"

            comments.append(
                {
                    "date": formatted_date,
                    "raw_date": raw_date,
                    "author": action.get("memberCreator", {}).get(
                        "fullName", "Onbekend"
                    ),
                    "text": action.get("data", {}).get("text", ""),
                }
            )

        if not newest_first:
            comments.reverse()

        return comments

    def print_comments(self, newest_first=True, indent="   "):
        """Print de comments netjes geformatteerd naar de console."""
        comments = self.get_comments(newest_first=newest_first)
        if not comments:
            print(f"{indent}💬 (Geen comments)")
            return

        print(f"{indent}💬 Comments:")
        for c in comments:
            print(f"{indent}   [{c['date']}] {c['author']}: {c['text']}")

    def __str__(self):
        return f"- [{self.id}] {self.name}"

    def __repr__(self):
        return f"<Card(id='{self.id}', name='{self.name}')>"