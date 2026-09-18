import os
import streamlit as st
from board import Board
from env_loader import load_env_file

load_env_file()
board = Board(board_name="Voetbal Selectie", key=os.getenv("KEY"), token=os.getenv("TOKEN"))

st.set_page_config(page_title="Presentie Beheer", layout="wide")
st.title("⚽ Presentie Grid View")

LIST_NAME = "Roster Pool"
t_list = board.get_list(LIST_NAME)

PRESENTIE_OPTIES = ["Aanwezig", "Onbekend", "Afwezig", "Vakantie", "Ziek", "Zwanger", "Werk/School", "Geblesseerd"]

if t_list and t_list.cards:
    with st.form("presentie_grid_form"):
        updates = []
        
        # Verdeel de spelers over 2 kolommen naast elkaar
        cols = st.columns(2)
        
        for idx, card in enumerate(t_list.cards):
            col = cols[idx % 2]  # Om en om in linker-/rechterkolom plaatsen
            
            with col:
                st.subheader(card.name)
                
                huidige_status = next((l for l in card.labels if l in PRESENTIE_OPTIES), "Onbekend")
                
                # Direct 1-klik knoppen horizontaal
                status = st.radio(
                    f"Status voor {card.name}",
                    PRESENTIE_OPTIES,
                    index=PRESENTIE_OPTIES.index(huidige_status),
                    horizontal=True,
                    key=f"rad_{card.id}",
                    label_visibility="collapsed"
                )
                
                note = st.text_input(
                    "Opmerking", 
                    key=f"note_{card.id}", 
                    placeholder="Opmerking...", 
                    label_visibility="collapsed"
                )
                
                st.divider()
                updates.append({"card": card, "status": status, "note": note.strip()})

        if st.form_submit_button("✅ Bevestig & Verwerk Presentie", use_container_width=True):
            board.bulk_update_presentie(updates, PRESENTIE_OPTIES)
            board.reload()
            st.success("Succesvol bijgewerkt!")
            st.rerun()