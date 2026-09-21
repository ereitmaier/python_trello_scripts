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

        search_key = field_name.lower().strip()
        field_def = self.board.custom_fields.get(search_key)

        if not field_def:
            if debug:
                print(
                    f"⚠️ DEBUG: Veld '{field_name}' niet gevonden op board."
                )
            return None

        cf_id = field_def["id"]

        for item in self.custom_field_items:
            if item.get("idCustomField") == cf_id:
                # 1. Dropdown/List (alleen als idValue een string ID is)
                id_val = item.get("idValue")
                if id_val and isinstance(id_val, str):
                    return field_def["options"].get(id_val)

                # 2. Values uit dictionary (number, text, date, checked)
                val_obj = item.get("value")
                if isinstance(val_obj, dict):
                    for key in ["number", "text", "date", "checked"]:
                        if key in val_obj and val_obj[key] is not None:
                            return val_obj[key]

                # 3. Directe 'checked' status
                if "checked" in item and item["checked"] is not None:
                    return item["checked"]

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

    def get_all_custom_field_values(self):
        """Haalt alle gevulde Custom Field waarden op voor deze kaart."""
        if not self.board:
            return {}

        results = {}
        for cf_name in self.board.custom_fields.keys():
            val = self.get_custom_field_value(cf_name)
            if val is not None:
                results[cf_name] = val
        return results 

    def get_formatted_custom_fields(self, custom_field_to_show):
        """Formatteert één specifiek Custom Field of álle Custom Fields voor console-weergave."""
        if not custom_field_to_show:
            return ""

        if custom_field_to_show in (True, "all"):
            all_cfs = self.get_all_custom_field_values()
            if not all_cfs:
                return ""
            formatted = [f"{k}: {v}" for k, v in all_cfs.items()]
            return f" : {' | '.join(formatted)}"

        val = self.get_custom_field_value(custom_field_to_show)
        val_display = val if val is not None else "-"
        return f" : {custom_field_to_show}: {val_display}"

    def __str__(self):
        return f"- [{self.id}] {self.name}"

    def __repr__(self):
        return f"<Card(id='{self.id}', name='{self.name}')>"