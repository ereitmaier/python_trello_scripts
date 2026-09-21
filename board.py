"""
board.py
--------
Module for managing and controlling a Trello Board.
Through the `Board` class, lists, cards, custom fields, and board actions
can be initialized, queried, and synchronized via the Trello API.
"""

from collections import defaultdict
import requests
from card import Card
from trello_list import TrelloList


class Board:
    """Represents a Trello Board loaded based on the board name.

    Attributes:
        key (str): Trello API key.
        token (str): Trello API token.
        auth (dict): Combined authentication dictionary for API requests.
        name (str): Name of the Trello board.
        id (str): Unique ID of the Trello board.
        lists (dict): Map of list names (lowercase) to TrelloList objects.
        custom_fields (dict): Map of custom field names (lowercase) to definitions and options.
    """

    def __init__(self, board_name, key, token):
        """Initializes the Board object and immediately loads all data from Trello.

        Args:
            board_name (str): Exact or case-insensitive name of the Trello board.
            key (str): Your Trello API Key.
            token (str): Your Trello API Token.
        """
        self.key = key
        self.token = token
        self.auth = {"key": key, "token": token}
        self.name = board_name
        self.id = None
        self.lists = {}  # Structure: { "list_name_lower": TrelloList_object }
        self.custom_fields = {}  # Structure: { "cf_name_lower": { "id": ..., "type": ..., "options": ... } }

        # Load all data directly upon initialization
        self.reload()

    def reload(self):
        """Reloads all data (lists, cards, custom fields, and labels) from Trello.

        Useful when external changes have been made directly on Trello.
        """
        self.lists = {}
        self.custom_fields = {}

        # If the Board ID is not yet known, resolve it first
        if not self.id:
            self._resolve_board_id()

        # Fetch custom field definitions and the lists/cards
        self._fetch_custom_fields()
        self._fetch_lists_and_cards()

    def _resolve_board_id(self):
        """Resolves the unique board ID from Trello using the board name.

        Raises:
            ValueError: If a board with the provided name cannot be found.
        """
        res = requests.get(
            "https://api.trello.com/1/members/me/boards",
            params={**self.auth, "fields": "name,id"},
        )
        res.raise_for_status()
        boards = res.json()

        board = next(
            (b for b in boards if b["name"].lower() == self.name.lower()), None
        )
        if not board:
            raise ValueError(f"Board with name '{self.name}' not found.")

        self.id = board["id"]
        self.name = board["name"]

    def _fetch_custom_fields(self):
        """Fetches Custom Field definitions from the board and builds an internal map."""
        res = requests.get(
            f"https://api.trello.com/1/boards/{self.id}/customFields",
            params=self.auth,
        )
        res.raise_for_status()

        for cf in res.json():
            cf_name = cf.get("name", "").lower()
            options_map = {}
            if cf.get("type") == "list":
                for opt in cf.get("options", []):
                    options_map[opt["id"]] = opt.get("value", {}).get(
                        "text", ""
                    )

            self.custom_fields[cf_name] = {
                "id": cf["id"],
                "type": cf.get("type"),
                "options": options_map,
            }

    def _fetch_lists_and_cards(self):
        """Fetches all lists first, then all cards including Custom Fields and Labels."""
        res_lists = requests.get(
            f"https://api.trello.com/1/boards/{self.id}/lists",
            params={**self.auth, "fields": "name,id"},
        )
        res_lists.raise_for_status()

        lists_by_id = {}
        for l in res_lists.json():
            t_list = TrelloList(l["id"], l["name"], board=self)
            self.lists[t_list.name.lower()] = t_list
            lists_by_id[l["id"]] = t_list

        res_cards = requests.get(
            f"https://api.trello.com/1/boards/{self.id}/cards",
            params={
                **self.auth,
                "fields": "name,id,idList,labels",
                "customFieldItems": "true",
            },
        )
        res_cards.raise_for_status()

        for c in res_cards.json():
            label_ids_map = {
                lbl["id"]: (lbl.get("name") or lbl.get("color", "")) 
                for lbl in c.get("labels", [])
            }

            card_obj = Card(
                card_id=c["id"],
                name=c["name"],
                custom_field_items=c.get("customFieldItems", []),
                labels=c.get("labels", []),
                auth=self.auth,
                trello_list=lists_by_id.get(c["idList"])
            )
            card_obj.label_ids_map = label_ids_map
            
            if card_obj.trello_list:
                card_obj.trello_list.cards.append(card_obj)

    def get_list(self, name):
        """Retrieves a TrelloList object by name (case-insensitive).

        Args:
            name (str): The name of the list.

        Returns:
            TrelloList|None: The TrelloList object or None if not found.
        """
        return self.lists.get(name.lower())

    def get_list_names(self):
        """Returns a list of all available list names on the board.

        Returns:
            list[str]: List of list names.
        """
        return [t_list.name for t_list in self.lists.values()]

    def print_list_names(self):
        """Prints all available lists on the board to the console."""
        print("\n📋 Available lists on the board:")
        for name in self.get_list_names():
            print(f" - {name}")

    def reset_to_roster_pool(
        self, target_list_name="Roster Pool", source_lists=None
    ):
        """Moves all cards from source lists back to the target list (e.g., 'Roster Pool').

        Args:
            target_list_name (str): Name of the destination list.
            source_lists (list[str], optional): List of source list names.
        """
        if source_lists is None:
            source_lists = [
                "Training Group 1",
                "Training Group 2",
                "Match Squad Vr1",
                "Match Squad Vr2",
            ]

        print(
            f"\n🔄 Resetting: Moving cards back to '{target_list_name}'..."
        )

        target_list = self.get_list(target_list_name)
        if not target_list:
            print(
                f"⚠️ Target list '{target_list_name}' not found on the board!"
            )
            return

        total_moved = 0

        for list_name in source_lists:
            source_list = self.get_list(list_name)
            if not source_list:
                continue

            cards_to_move = list(source_list.cards)

            for card in cards_to_move:
                card.move_to(target_list)
                total_moved += 1

        print(
            f"✅ Reset complete: {total_moved} card(s) returned to '{target_list.name}'."
        )

    def get_cards_grouped_by_custom_field(self, custom_field_name, list_name=None):
        """Groups cards by the value of a specific Custom Field.

        Args:
            custom_field_name (str): Custom field name to group by.
            list_name (str, optional): Restrict grouping to cards inside a specific list.

        Returns:
            dict[str, list[Card]]: Dictionary mapping field option values to lists of Card objects.
        """
        target_cards = []
        if list_name:
            t_list = self.get_list(list_name)
            if t_list:
                target_cards = t_list.cards
        else:
            for l in self.lists.values():
                target_cards.extend(l.cards)

        grouped = defaultdict(list)
        for card in target_cards:
            val = card.get_custom_field_value(custom_field_name) if custom_field_name else None
            val_str = str(val) if val is not None else "No option selected"
            grouped[val_str].append(card)

        return grouped

    def print_composition(
        self, list_name=None, custom_field_name=None, show_positions=False, show_comments=False, custom_field_to_show=None
    ):
        """Prints the composition of a specific list OR groups cards by a Custom Field.

        Args:
            list_name (str, optional): Name of the specific list to print.
            custom_field_name (str, optional): Custom Field to group cards by.
            show_positions (bool): Whether to display position codes [GKDFMFAT].
            show_comments (bool): Whether to display card comments.
            custom_field_to_show (str|bool, optional): Specific Custom Field to display next to the card name.
        """
        if list_name and not custom_field_name:
            t_list = self.get_list(list_name)
            if t_list:
                t_list.print_composition(
                    show_positions=show_positions,
                    show_comments=show_comments,
                    custom_field_to_show=custom_field_to_show
                )
            else:
                print(f"⚠️ List '{list_name}' not found.")
            return

        grouped = self.get_cards_grouped_by_custom_field(
            custom_field_name=custom_field_name, list_name=list_name
        )

        for group_name in sorted(grouped.keys(), key=str.lower):
            print(f"\n📋 {group_name}:")
            cards_in_group = grouped[group_name]

            if show_positions:
                sorted_cards = sorted(
                    cards_in_group,
                    key=lambda c: (c.get_position_priority(), c.name.lower()),
                )
            else:
                sorted_cards = sorted(
                    cards_in_group, key=lambda c: c.name.lower()
                )

            max_width = len(str(len(sorted_cards)))
            for index, card in enumerate(sorted_cards, 1):
                num_str = str(index).rjust(max_width)
                pos_str = (
                    f"{card.get_position_code()} " if show_positions else ""
                )

                extra_field_str = card.get_formatted_custom_fields(custom_field_to_show)

                print(f" {num_str}. {pos_str}{card.name}{extra_field_str}")

                if show_comments:
                    card.print_comments(indent="      ")

    def print_roster_pool(self, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Prints the composition of the Roster Pool to the console.

        Args:
            show_positions (bool): Show position codes.
            show_comments (bool): Show comments.
            custom_field_to_show (str|bool): Show additional custom field.
        """
    
        list_name = f"Roster Pool"
        self.print_composition(
            list_name=list_name,
            show_positions=show_positions,
            show_comments=show_comments,
            custom_field_to_show=custom_field_to_show,
        )

    def print_unavailable(self, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Prints the composition of the Unavailable to the console.

        Args:
            show_positions (bool): Show position codes.
            show_comments (bool): Show comments.
            custom_field_to_show (str|bool): Show additional custom field.
        """
    
        list_name = f"Unavailable"
        self.print_composition(
            list_name=list_name,
            show_positions=show_positions,
            show_comments=show_comments,
            custom_field_to_show=custom_field_to_show,
        )

    def print_training_groups(self, groups=None, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Prints the composition of training groups to the console.

        Args:
            groups (int|str|list, optional): None for all groups, or e.g. 1, "1", or ["1", "2"].
            show_positions (bool): Show position codes.
            show_comments (bool): Show comments.
            custom_field_to_show (str|bool): Show additional custom field.
        """
        if groups is None:
            self.print_composition(
                custom_field_name="Training Group",
                show_positions=show_positions,
                show_comments=show_comments,
                custom_field_to_show=custom_field_to_show,
            )
        else:
            if isinstance(groups, (int, str)):
                group_list = [str(groups)]
            else:
                group_list = [str(g) for g in groups]

            for g in group_list:
                list_name = f"Training Group {g.strip()}"
                self.print_composition(
                    list_name=list_name,
                    show_positions=show_positions,
                    show_comments=show_comments,
                    custom_field_to_show=custom_field_to_show,
                )

    def print_match_squads(self, squads=None, show_positions=True, show_comments=False, custom_field_to_show=None):
        """Prints the composition of match squads to the console.

        Args:
            squads (int|str|list, optional): None for all squads, or e.g. "1", "vr1", or ["1", "2"].
            show_positions (bool): Show position codes.
            show_comments (bool): Show comments.
            custom_field_to_show (str|bool): Show additional custom field.
        """
        if squads is None:
            self.print_composition(
                custom_field_name="Match Selection",
                show_positions=show_positions,
                show_comments=show_comments,
                custom_field_to_show=custom_field_to_show,
            )
        else:
            if isinstance(squads, (int, str)):
                squad_list = [str(squads)]
            else:
                squad_list = [str(s) for s in squads]

            for s in squad_list:
                s_str = s.strip().lower()
                code = s_str.replace("vr", "")
                list_name = f"Match Squad Vr{code.upper()}" if code.isdigit() else f"Match Squad {s_str}"
                
                self.print_composition(
                    list_name=list_name,
                    show_positions=show_positions,
                    show_comments=show_comments,
                    custom_field_to_show=custom_field_to_show,
                )

    def find_card(self, card_name):
        """Searches for a card across the entire board (case-insensitive).

        Args:
            card_name (str): Name of the card/player.

        Returns:
            Card|None: Card object if found, otherwise None.
        """
        search_name = card_name.strip().lower()
        for t_list in self.lists.values():
            for card in t_list.cards:
                if card.name.strip().lower() == search_name:
                    return card
        return None

    def print_card_details(self, card_name, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Searches for a card/player and prints its details to the console.

        Args:
            card_name (str): Name of the card/player to search for.
            show_positions (bool): Show position code.
            show_comments (bool): Show comments.
            custom_field_to_show (str|bool): Show additional custom field.

        Returns:
            Card|None: The found Card object or None.
        """
        card = self.find_card(card_name)
        if not card:
            print(f"⚠️ Player/Card '{card_name}' not found on the board.")
            return None

        list_name = card.trello_list.name if card.trello_list else "Unknown"
        field_str = card.get_formatted_custom_fields(custom_field_to_show)

        print(f"\n🔍 Player found:")
        print(f"   Name: {card.name}{field_str}")
        print(f"   List: {list_name}")
        
        if show_positions:
            print(f"   - Position: {card.get_position_code()}")

        if show_comments:
            card.print_comments(indent="   ")

        return card

    def update_custom_field(self, card_id, field_name, value):
        """Updates a Custom Field value on a specific card via the Trello API."""
        field_def = self.custom_fields.get(field_name.lower().strip())
        if not field_def:
            print(f"⚠️ Field '{field_name}' not found on board.")
            return

        cf_id = field_def["id"]
        url = f"https://api.trello.com/1/cards/{card_id}/customField/{cf_id}/item"

        if field_def.get("type") == "list":
            option_id = next(
                (opt_id for opt_id, opt_text in field_def["options"].items() 
                 if opt_text.lower().strip() == str(value).lower().strip()), 
                None
            )
            if not option_id:
                print(f"⚠️ Option '{value}' not found for field '{field_name}'.")
                return
            
            payload = {"idValue": option_id}
        else:
            payload = {"value": {"text": str(value)}}

        response = requests.put(url, json=payload, params=self.auth)
        response.raise_for_status()

    def clear_custom_field(self, card_id, field_name):
        """Clears the value of a Custom Field on a specific card via the Trello API."""
        field_def = self.custom_fields.get(field_name.lower().strip())
        if not field_def:
            print(f"⚠️ Field '{field_name}' not found on board.")
            return

        cf_id = field_def["id"]
        url = f"https://api.trello.com/1/cards/{card_id}/customField/{cf_id}/item"

        if field_def.get("type") == "list":
            payload = {"idValue": ""}
        else:
            payload = {"value": {}}

        response = requests.put(url, json=payload, params=self.auth)
        response.raise_for_status()

    def get_custom_fields(self):
        """Returns a list of all available Custom Field names on the board."""
        return list(self.custom_fields.keys())

    def print_custom_fields(self):
        """Prints an overview of all Custom Fields and their available options."""
        print(f"\n🏷️ Custom Fields on board '{self.name}':")
        if not self.custom_fields:
            print("   (No Custom Fields found)")
            return

        for name, info in self.custom_fields.items():
            field_type = info.get("type", "unknown")
            options = info.get("options", {})

            if options:
                opt_str = ", ".join(options.values())
                print(f" - {name} ({field_type}): [{opt_str}]")
            else:
                print(f" - {name} ({field_type})")

    def __repr__(self):
        return f"<Board(name='{self.name}', lists={list(self.lists.keys())})>"