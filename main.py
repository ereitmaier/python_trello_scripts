#!/usr/bin/env python3

import sys
import os
import argparse
from board import Board
from env_loader import load_env_file


def main():
    parser = argparse.ArgumentParser(
        description="Beheer Trello Voetbal Selectie via command-line opties."
    )

    parser.add_argument(
        "-t",
        "--training",
        nargs="?",
        const="ALL",
        metavar="GROEP",
        help="Trainingsgroep selecteren (bijv. -t 1 of -t 1,2). Zonder waarde: totaaloverzicht van alle trainingsgroepen.",
    )
    parser.add_argument(
        "-m",
        "--match",
        nargs="?",
        const="ALL",
        metavar="SQUAD",
        help="Match Squad selecteren (bijv. -m 1, -m vr1 of -m 1,2). Zonder waarde: totaaloverzicht van alle match squads.",
    )
    parser.add_argument(
        "-p",
        "--positions",
        action="store_true",
        help="Optie om posities ([KVMA]) te tonen.",
    )
    parser.add_argument(
        "-c",
        "--comments",
        action="store_true",
        help="Optie om comments per kaart te tonen.",
    )
    parser.add_argument(
        "-f",
        "--field",
        metavar="VELDNAAM",
        help="Optie om een extra Custom Field waarde per kaart te tonen.",
    )
    parser.add_argument(
        "-s",
        "--search",
        metavar="SPELER",
        help="Zoek naar een specifieke speler (kaartnaam).",
    )
    parser.add_argument(
        "-l",
        "--list",
        metavar="LIJST",
        help="Toon alle kaarten van een specifieke lijst.",
    )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="Reset alle kaarten terug naar de 'Roster Pool'.",
    )

    args = parser.parse_args()

    # Laad credentials & board
    load_env_file()
    key = os.getenv("KEY")
    token = os.getenv("TOKEN")

    if not key or not token:
        print("❌ Fout: KEY of TOKEN is niet ingesteld in .trello_auth.", file=sys.stderr)
        sys.exit(1)

    board = Board(board_name="Voetbal Selectie", key=key, token=token)

    # --- 1. RESET ---
    if args.reset:
        board.reset_to_roster_pool()
        return

    # --- 2. SPELER ZOEKEN (-s) ---
    if args.search:
        card = board.find_card(args.search)
        if not card:
            print(f"⚠️ Speler/Kaart '{args.search}' niet gevonden op het board.")
        else:
            lijst_naam = card.trello_list.name if card.trello_list else "Onbekend"
            pos_str = f"{card.get_position_code()} " if args.positions else ""
            
            field_str = ""
            if args.field:
                val = card.get_custom_field_value(args.field)
                val_disp = val if val is not None else "-"
                field_str = f" | {args.field}: {val_disp}"

            print(f"\n🔍 Speler gevonden:")
            print(f"   Naam: {pos_str}{card.name}{field_str}")
            print(f"   Lijst: {lijst_naam}")

            if args.comments:
                card.print_comments(indent="   ")
        return

    # --- 3. SPECIFIEKE LIJST TONEN (-l) ---
    if args.list:
        board.print_samenstelling(
            list_name=args.list,
            show_positions=args.positions,
            show_comments=args.comments,
            custom_field_to_show=args.field,
        )
        return

    # --- 4. TRAININGGROEPEN (-t) ---
    if args.training is not None:
        if args.training == "ALL":
            # Totaaloverzicht groeperen op het veld "Trainingsgroep"
            board.print_samenstelling(
                custom_field_name="Trainingsgroep",
                show_positions=args.positions,
                show_comments=args.comments,
                custom_field_to_show=args.field,
            )
        else:
            # Specifieke groepen opgegeven (bijv. "1" of "1,2")
            groepen = [g.strip() for g in args.training.split(",")]
            for g in groepen:
                list_name = f"Trainingsgroep {g}"
                board.print_samenstelling(
                    list_name=list_name,
                    show_positions=args.positions,
                    show_comments=args.comments,
                    custom_field_to_show=args.field,
                )
        return

    # --- 5. MATCH SQUAD (-m) ---
    if args.match is not None:
        if args.match == "ALL":
            # Totaaloverzicht groeperen op het veld "Wedstrijdselectie"
            board.print_samenstelling(
                custom_field_name="Wedstrijdselectie",
                show_positions=args.positions,
                show_comments=args.comments,
                custom_field_to_show=args.field,
            )
        else:
            # Specifieke squads opgegeven (bijv. "1", "2" of "vr1,vr2")
            squads = [s.strip().lower() for s in args.match.split(",")]
            for s in squads:
                # Maak de lijstnaam op (bijv. "1" -> "Match Squad Vr1", "vr1" -> "Match Squad Vr1")
                code = s.replace("vr", "")
                list_name = f"Match Squad Vr{code.upper()}" if code.isdigit() else f"Match Squad {s}"
                
                board.print_samenstelling(
                    list_name=list_name,
                    show_positions=args.positions,
                    show_comments=args.comments,
                    custom_field_to_show=args.field,
                )
        return

    # Als er geen argumenten zijn meegegeven, toon help
    parser.print_help()


if __name__ == "__main__":
    main()