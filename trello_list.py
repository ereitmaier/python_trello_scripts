class TrelloList:
    """Representeert een Trello-lijst die kaarten bevat."""

    def __init__(self, list_id, name, board=None):
        self.id = list_id
        self.name = name
        self.board = board  # Onderdeel van Board
        self.cards = []     # Bevat Cards

    def add_card(self, card):
        """Voegt een kaart toe en stelt de relatie direct in."""
        card.trello_list = self
        self.cards.append(card)

    def filter_by_custom_field(
        self, field_name, expected_value=None, debug=False
    ):
        """Filtert kaarten op een Custom Field."""
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

    def print_samenstelling(self, show_positions=True, show_comments=False, custom_field_to_show=None):
        """Print de opstelling/samenstelling van deze specifieke lijst."""
        print(f"\n📋 Samenstelling: {self.name}")

        if not self.cards:
            print("   (geen kaarten in deze lijst)")
            return

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
            
            extra_field_str = ""
            if custom_field_to_show:
                val = card.get_custom_field_value(custom_field_to_show)
                val_display = val if val is not None else "-"
                extra_field_str = f" | {custom_field_to_show}: {val_display}"

            print(f" {num_str}. {pos_str}{card.name}{extra_field_str}")

            if show_comments:
                card.print_comments(indent="      ")

    def print_cards(self, cards_to_print=None):
        target_cards = (
            cards_to_print if cards_to_print is not None else self.cards
        )
        print(f"\n📋 Lijst: {self.name} ({len(target_cards)} kaarten)")
        if not target_cards:
            print("   (geen kaarten)")
        for card in target_cards:
            print(f"   {card}")

    def __repr__(self):
        return f"<TrelloList(name='{self.name}', cards={len(self.cards)})>"