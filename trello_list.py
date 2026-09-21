"""
trello_list.py
--------------
Module for managing a specific Trello list.
A `TrelloList` contains multiple `Card` objects and provides methods to
filter cards or print list compositions cleanly.
"""

class TrelloList:
    """Represents a Trello list containing collections of cards.

    Attributes:
        id (str): Unique Trello list ID.
        name (str): Name of the list.
        board (Board): Link to parent Board object.
        cards (list[Card]): List of Card objects inside this list.
    """

    def __init__(self, list_id, name, board=None):
        """Initializes a TrelloList object."""
        self.id = list_id
        self.name = name
        self.board = board  # Parent Board
        self.cards = []     # List of Card instances

    def add_card(self, card):
        """Adds a card to this list and updates the card's internal list reference.

        Args:
            card (Card): Card object to append.
        """
        card.trello_list = self
        self.cards.append(card)

    def filter_by_custom_field(
        self, field_name, expected_value=None, debug=False
    ):
        """Filters cards within this list by a Custom Field value.

        Args:
            field_name (str): Name of the Custom Field.
            expected_value (Any, optional): Expected value. If None, returns all cards
                                            with any set value for this field.
            debug (bool): Enables debug messages.

        Returns:
            list[Card]: List of matching Card objects.
        """
        filtered_cards = []
        for card in self.cards:
            val = card.get_custom_field_value(field_name, debug=debug)
            if val is not None:
                if expected_value is None:
                    filtered_cards.append(card)
                else:
                    val_str = str(val).strip().lower()
                    expected_str = str(expected_value).strip().lower()
                    if val_str == expected_str:
                        filtered_cards.append(card)
        return filtered_cards

    def print_composition(self, show_positions=False, show_comments=False, custom_field_to_show=None):
        """Prints list composition to the console.

        Args:
            show_positions (bool): Display position labels [GKDFMFAT] and sort by position.
            show_comments (bool): Display card comments.
            custom_field_to_show (str|bool): Display an extra custom field on the same line.
        """
        print(f"\n📋 Composition: {self.name}")

        if not self.cards:
            print("   (no cards in this list)")
            return

        # Sort primarily by position priority (if enabled) and secondarily by name
        sorted_cards = sorted(
            self.cards,
            key=lambda c: (
                c.get_position_priority() if show_positions else 0,
                c.name.lower(),
            ),
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

    def print_cards(self, cards_to_print=None):
        """Prints a simple raw representation of cards in the list.

        Args:
            cards_to_print (list[Card], optional): Subset of cards to print. If None,
                                                    prints all cards in the list.
        """
        target_cards = (
            cards_to_print if cards_to_print is not None else self.cards
        )
        print(f"\n📋 List: {self.name} ({len(target_cards)} cards)")
        if not target_cards:
            print("   (no cards)")
        for card in target_cards:
            print(f"   {card}")

    def __repr__(self):
        return f"<TrelloList(name='{self.name}', cards={len(self.cards)})>"