from collections import defaultdict
import requests
from card import Card
from trello_list import TrelloList


class Board:
    """Representeert een Trello Board ingeladen op basis van de boardnaam."""

    def __init__(self, board_name, key, token):
        self.key = key
        self.token = token
        self.auth = {"key": key, "token": token}
        self.name = board_name
        self.id = None
        self.lists = {}  # Map: list_name.lower() -> TrelloList object
        self.custom_fields = (
            {}
        )  # Map: cf_name.lower() -> CF definities & opties map

        # Laad alle data direct in bij initialisatie
        self.reload()

    def reload(self):
        """Herlaadt alle data (lijsten, kaarten, custom fields en labels) opnieuw vanaf Trello."""
        self.lists = {}
        self.custom_fields = {}

        if not self.id:
            self._resolve_board_id()

        self._fetch_custom_fields()
        self._fetch_lists_and_cards()

    def _resolve_board_id(self):
        """Zoekt het board-ID op bij Trello aan de hand van de boardnaam."""
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
            raise ValueError(f"Board met naam '{self.name}' niet gevonden.")

        self.id = board["id"]
        self.name = board["name"]

    def _fetch_custom_fields(self):
        """Haalt Custom Field definities op van het board."""
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
        """Haalt eerst alle lijsten op, en daarna alle kaarten inclusief Custom Fields en Labels."""
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
        """Haalt een TrelloList-object op basis van de naam."""
        return self.lists.get(name.lower())

    def get_list_names(self):
        """Geeft een lijst van alle lijstnamen terug."""
        return [t_list.name for t_list in self.lists.values()]

    def print_list_names(self):
        """Print alle beschikbare lijsten op het board."""
        print("\n📋 Beschikbare lijsten op het board:")
        for name in self.get_list_names():
            print(f" - {name}")

    def reset_to_roster_pool(
        self, target_list_name="Roster Pool", source_lists=None
    ):
        """Verplaatst alle kaarten uit de trainings- en wedstrijdlijsten terug naar de 'Roster Pool'."""
        if source_lists is None:
            source_lists = [
                "Trainingsgroep 1",
                "Trainingsgroep 2",
                "Match Squad Vr1",
                "Match Squad Vr2",
            ]

        print(
            f"\n🔄 Start reset: Kaarten terugverplaatsen naar '{target_list_name}'..."
        )

        target_list = self.get_list(target_list_name)
        if not target_list:
            print(
                f"⚠️ Doellijst '{target_list_name}' niet gevonden op het board!"
            )
            return

        totaal_verplaatst = 0

        for list_name in source_lists:
            source_list = self.get_list(list_name)
            if not source_list:
                continue

            kaarten_om_te_verplaatsen = list(source_list.cards)

            for card in kaarten_om_te_verplaatsen:
                card.move_to(target_list)
                totaal_verplaatst += 1

        print(
            f"✅ Reset voltooid: {totaal_verplaatst} kaart(en) teruggezet naar '{target_list.name}'."
        )

    def print_samenstelling(
        self, list_name=None, custom_field_name=None, show_positions=False, show_comments=False, custom_field_to_show=None
    ):
        """Prints de samenstelling van een specifieke lijst OF groepeert op Custom Field."""
        if list_name and not custom_field_name:
            t_list = self.get_list(list_name)
            if t_list:
                t_list.print_samenstelling(
                    show_positions=show_positions,
                    show_comments=show_comments,
                    custom_field_to_show=custom_field_to_show
                )
            else:
                print(f"⚠️ Lijst '{list_name}' niet gevonden.")
            return

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
            val = (
                card.get_custom_field_value(custom_field_name)
                if custom_field_name
                else "Geen optie gekozen"
            )
            val_str = str(val) if val is not None else "Geen optie gekozen"
            grouped[val_str].append(card)

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

    def show_training_groups(self, groups=None, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Toont de samenstelling van trainingsgroepen.
        
        Param 'groups': None voor alle groepen, of bijv. 1, "1", of ["1", "2"].
        """
        if groups is None:
            self.print_samenstelling(
                custom_field_name="Trainingsgroep",
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
                list_name = f"Trainingsgroep {g.strip()}"
                self.print_samenstelling(
                    list_name=list_name,
                    show_positions=show_positions,
                    show_comments=show_comments,
                    custom_field_to_show=custom_field_to_show,
                )

    def show_match_squads(self, squads=None, show_positions=True, show_comments=False, custom_field_to_show=None):
        """Toont de samenstelling van match squads.
        
        Param 'squads': None voor alle squads, of bijv. "1", "vr1", of ["1", "2"].
        """
        if squads is None:
            self.print_samenstelling(
                custom_field_name="Wedstrijdselectie",
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
                
                self.print_samenstelling(
                    list_name=list_name,
                    show_positions=show_positions,
                    show_comments=show_comments,
                    custom_field_to_show=custom_field_to_show,
                )

    def find_card(self, card_name):
        """Zoekt hoofdletterongevoelig naar een kaart op het gehele board."""
        search_name = card_name.strip().lower()
        for t_list in self.lists.values():
            for card in t_list.cards:
                if card.name.strip().lower() == search_name:
                    return card
        return None

    def search_card(self, card_name, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Zoekt naar een speler/kaart en print de details direct naar de console."""
        card = self.find_card(card_name)
        if not card:
            print(f"⚠️ Speler/Kaart '{card_name}' niet gevonden op het board.")
            return None

        lijst_naam = card.trello_list.name if card.trello_list else "Onbekend"
        field_str = card.get_formatted_custom_fields(custom_field_to_show)

        print(f"\n🔍 Speler gevonden:")
        print(f"   Naam: {card.name}{field_str}")
        print(f"   Lijst: {lijst_naam}")
        
        if show_positions:
            print(f"   - Positie: {card.get_position_code()}")

        if show_comments:
            card.print_comments(indent="   ")

        return card

    def update_custom_field(self, card_id, field_name, value):
        """Update een Custom Field op een specifieke kaart via de Trello API."""
        field_def = self.custom_fields.get(field_name.lower().strip())
        if not field_def:
            print(f"⚠️ Veld '{field_name}' niet gevonden op het board.")
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
                print(f"⚠️ Optie '{value}' niet gevonden voor veld '{field_name}'.")
                return
            
            payload = {"idValue": option_id}
        else:
            payload = {"value": {"text": str(value)}}

        response = requests.put(url, json=payload, params=self.auth)
        response.raise_for_status()

    def clear_custom_field(self, card_id, field_name):
        """Maakt de waarde van een Custom Field leeg op een specifieke kaart via de Trello API."""
        field_def = self.custom_fields.get(field_name.lower().strip())
        if not field_def:
            print(f"⚠️ Veld '{field_name}' niet gevonden op het board.")
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
        """Geeft een lijst terug van alle beschikbare Custom Fields op het board."""
        return list(self.custom_fields.keys())

    def print_custom_fields(self):
        """Print een overzicht van alle Custom Fields en hun eventuele keuzemogelijkheden."""
        print(f"\n🏷️ Custom Fields op board '{self.name}':")
        if not self.custom_fields:
            print("   (Geen Custom Fields gevonden)")
            return

        for name, info in self.custom_fields.items():
            field_type = info.get("type", "onbekend")
            options = info.get("options", {})

            if options:
                opt_str = ", ".join(options.values())
                print(f" - {name} ({field_type}): [{opt_str}]")
            else:
                print(f" - {name} ({field_type})")

    def __repr__(self):
        return f"<Board(name='{self.name}', lists={list(self.lists.keys())})>"