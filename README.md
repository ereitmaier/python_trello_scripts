# Handleiding: Trello Voetbal Selectie CLI

Met het Python-script main.py beheer je de teamindelingen, trainingsgroepen, match squads en spelerinformatie op het Trello-board via de command-line interface (CLI).

## Vereisten & Installatie

Zorg dat de volgende onderdelen in dezelfde map staan:

Python bestanden: main.py, board.py, trello_list.py, card.py, env_loader.py

Configuratie: .trello_auth (bevat je KEY en TOKEN)

Afhankelijkheden: requests en pyyaml (installeren via pip install requests pyyaml)

## Basis Syntaxis

```Bash
python main.py [OPTIES]
```

## Overzicht van Commando's & Opties

⚽ Match Squads (-m, --match)

Totaaloverzicht van alle Match Squads:

```Bash
python main.py -m
```

Specifieke Match Squad bekijken (bijv. Vr1 of Vr2):

```Bash
python main.py -m 1
python main.py -m 1,2
```

🏃 Trainingsgroepen (-t, --training)
Totaaloverzicht van alle Trainingsgroepen:

```Bash
python main.py -t
```

Specifieke Trainingsgroep bekijken (bijv. Groep 1 of Groep 1 en 2):

```Bash
python main.py -t 1
python main.py -t 1,2
```

🔍 Speler Zoeken & Lijsten Inzien (-s, -l)
Zoek een specifieke speler op het board:

```Bash
python main.py -s "Britt"
```

Toon alle kaarten uit een specifieke Trello-lijst:

```Bash
python main.py -l "Roster Pool"
python main.py -l "Admin / Onboarding"
```

➕ Extra Informatie Tonen (-p, -c, -f)
Deze vlaggen kunnen gecombineerd worden met overzichten, zoekopdrachten of lijstweergaven:

Posities tonen (-p): Toont de posities van de speler via [KVMA] (Keeper, Verdediger, Middenvelder, Aanvaller).

```Bash
python main.py -m 1 -p
```

Comments tonen (-c): Print de geplaatste opmerkingen op de spelerskaart.

```Bash
python main.py -s "John" -c
```

Extra Custom Field tonen (-f \<veldnaam\>): Print de waarde van een specifiek Trello Custom Field (bijv. "Wedstrijdselectie" of "Trainingsgroep").

```Bash
python main.py -l "Roster Pool" -f "Wedstrijdselectie"
```

🔄 Board Resetten (-r, --reset)

Kaarten terugzetten naar de Roster Pool:
Verplaatst alle spelers uit de trainings- en wedstrijdlijsten terug naar de lijst "Roster Pool".

```Bash
python main.py -r
```

## Praktische Voorbeelden

Volledig overzicht van Match Squad 1 met spelerposities en comments:

```Bash
python main.py -m 1 -p -c
```

Zoek speler "Fenna" met positie en eventuele comments:

```Bash
python main.py -s "Jane" -p -c
```

Bekijk Trainingsgroep 1 met weergave van het veld "Wedstrijdselectie":

```Bash
python main.py -t 1 -p -f "Wedstrijdselectie"
```
# python_trello_scripts
