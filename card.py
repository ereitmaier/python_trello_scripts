"""
card.py
-------
Module representing a Trello card (e.g., a player).
Provides functionalities for moving cards, inspecting/updating Custom Fields,
positions/labels, and fetching card comments.
"""

import requests
from datetime import datetime

class Card:
    """Represents a Trello card as part of a TrelloList.

    Attributes:
        id (str): Trello card ID.
        name (str): Title/name of the card.
        custom_field_items (list[dict]): Raw Custom Field data from Trello.
        labels (list[str]): Names or colors of labels attached to the card.
        auth (dict): Authentication parameters (key & token).
        trello_list (TrelloList): The list this card currently belongs to.
    """

    def __init__(self, card_id, name, custom_field_items, labels, auth, trello_list=None):
        """Initializes a Card object."""
        self.id = card_id
        self.name = name
        self.custom_field_items = custom_field_items
        # Parse labels to readable list of names or colors
        self.labels = [
            label.get("name") or label.get("color") for label in labels
        ]
        self.auth = auth
        self.trello_list = trello_list  # Link to parent TrelloList

    @property
    def board(self):
        """Returns the parent Board object via the associated list.

        Returns:
            Board|None: Parent Board or None.
        """
        return self.trello_list.board if self.trello_list else None

    def get_custom_field_value(self, field_name, debug=False):
        """Retrieves the current, readable value of a Custom Field by name.

        Args:
            field_name (str): Name of the Custom Field.
            debug (bool): If True, prints debug logs when field is missing.

        Returns:
            Any|None: Formatted or raw value of the field, or None if empty.
        """
        if not self.board:
            return None

        search_key = field_name.lower().strip()
        field_def = self.board.custom_fields.get(search_key)

        if not field_def:
            if debug:
                print(
                    f"⚠️ DEBUG: Field '{field_name}' not found on board."
                )
            return None

        cf_id = field_def["id"]

        # Iterate over all custom field values attached to the card
        for item in self.custom_field_items:
            if item.get("idCustomField") == cf_id:
                # 1. Dropdown/List (only if idValue is a string ID)
                id_val = item.get("idValue")
                if id_val and isinstance(id_val, str):
                    return field_def["options"].get(id_val)

                # 2. Values from dictionary (number, text, date, checked)
                val_obj = item.get("value")
                if isinstance(val_obj, dict):
                    for key in ["number", "text", "date", "checked"]:
                        if key in val_obj and val_obj[key] is not None:
                            return val_obj[key]

                # 3. Direct 'checked' status
                if "checked" in item and item["checked"] is not None:
                    return item["checked"]

        return None

    def get_position_code(self):
        """Converts labels to a position code format [GKDFMFAT].
        
        GK = Goalkeeper, DF = Defender, MF = Midfielder, AT = Attacker.
        Missing roles are displayed with dashes.

        Returns:
            str: Formatted position string, e.g., '[GK----]' or '[-DF--]'.
        """
        labels_lower = [l.lower() for l in self.labels if l]
        gk = "GK" if any(x in labels_lower for x in ["keeper", "goalkeeper"]) else "--"
        df = "DF" if any(x in labels_lower for x in ["verdediger", "defender"]) else "--"
        mf = "MF" if any(x in labels_lower for x in ["middenvelder", "midfielder"]) else "--"
        at = "AT" if any(x in labels_lower for x in ["aanvaller", "attacker", "forward"]) else "--"
        return f"[{gk}{df}{mf}{at}]"

    def get_position_priority(self):
        """Determines sorting priority based on player position labels.

        Returns:
            int: Priority for sorting (GK=1, DF=2, MF=3, AT=4, Other=5).
        """
        labels_lower = [l.lower() for l in self.labels if l]
        if any(x in labels_lower for x in ["keeper", "goalkeeper"]):
            return 1
        if any(x in labels_lower for x in ["verdediger", "defender"]):
            return 2
        if any(x in labels_lower for x in ["middenvelder", "midfielder"]):
            return 3
        if any(x in labels_lower for x in ["aanvaller", "attacker", "forward"]):
            return 4
        return 5

    def move_to(self, target_list):
        """Moves card on Trello to another TrelloList and updates internal references.

        Args:
            target_list (TrelloList): Destination list object.
        """
        url = f"https://api.trello.com/1/cards/{self.id}"
        response = requests.put(
            url, params={**self.auth, "idList": target_list.id}
        )
        response.raise_for_status()

        # Update in-memory reference
        if self.trello_list and self in self.trello_list.cards:
            self.trello_list.cards.remove(self)

        target_list.add_card(self)
        print(f"✓ Card '{self.name}' moved to '{target_list.name}'")

    def get_comments(self, newest_first=True):
        """Fetches all card comments via the Trello API.

        Args:
            newest_first (bool): When True, newest comments appear first.

        Returns:
            list[dict]: List of dicts containing 'date', 'author', and 'text'.
        """
        url = f"https://api.trello.com/1/cards/{self.id}/actions"
        params = {**self.auth, "filter": "commentCard"}
        response = requests.get(url, params=params)
        response.raise_for_status()
        actions = response.json()

        comments = []
        for action in actions:
            raw_date = action.get("date")

            # Format ISO date to readable string
            if raw_date:
                dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%d-%m-%Y %H:%M")
            else:
                formatted_date = "Unknown date"

            comments.append(
                {
                    "date": formatted_date,
                    "raw_date": raw_date,
                    "author": action.get("memberCreator", {}).get(
                        "fullName", "Unknown"
                    ),
                    "text": action.get("data", {}).get("text", ""),
                }
            )

        if not newest_first:
            comments.reverse()

        return comments

    def print_comments(self, newest_first=True, indent="   "):
        """Prints formatted comments to the console.

        Args:
            newest_first (bool): Determines sorting order.
            indent (str): Indentation string for output alignment.
        """
        comments = self.get_comments(newest_first=newest_first)
        if not comments:
            print(f"{indent}💬 (No comments)")
            return

        print(f"{indent}💬 Comments:")
        for c in comments:
            print(f"{indent}   [{c['date']}] {c['author']}: {c['text']}")

    def get_all_custom_field_values(self):
        """Retrieves all populated Custom Field values for this card.

        Returns:
            dict: Map of Custom Field names and values { field_name: value }.
        """
        if not self.board:
            return {}

        results = {}
        for cf_name in self.board.custom_fields.keys():
            val = self.get_custom_field_value(cf_name)
            if val is not None:
                results[cf_name] = val
        return results 

    def get_formatted_custom_fields(self, custom_field_to_show):
        """Formats a single or all Custom Fields for console output.

        Args:
            custom_field_to_show (str|bool): Field name, True/"all" for all fields, or None/False.

        Returns:
            str: Formatted suffix string.
        """
        if not custom_field_to_show:
            return ""

        # Show all Custom Fields
        if custom_field_to_show in (True, "all"):
            all_cfs = self.get_all_custom_field_values()
            if not all_cfs:
                return ""
            formatted = [f"{k}: {v}" for k, v in all_cfs.items()]
            return f" : {' | '.join(formatted)}"

        # Show a specific Custom Field
        val = self.get_custom_field_value(custom_field_to_show)
        val_display = val if val is not None else "-"
        return f" : {custom_field_to_show}: {val_display}"

    def __str__(self):
        return f"- [{self.id}] {self.name}"

    def __repr__(self):
        return f"<Card(id='{self.id}', name='{self.name}')>"