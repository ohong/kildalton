import os
import streamlit as st
from datetime import datetime
import pandas as pd
from database import init_db, ContestStatus
from contest import ContestManager
from ocr import TradeParser

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = init_db()
    st.session_state.contest_manager = ContestManager(st.session_state.db)
    st.session_state.trade_parser = TradeParser()

def create_contest_page():
    st.header("Create New Contest")
    
    with st.form("create_contest"):
        name = st.text_input("Contest Name")
        target_profit = st.selectbox(
            "Target Profit",
            options=[1000, 5000, 10000],
            format_func=lambda x: f"${x:,}"
        )
        
        if st.form_submit_button("Create Contest"):
            if name:
                contest = st.session_state.contest_manager.create_contest(name, target_profit)
                st.success(f"Contest created! Join code: {contest.join_code}")
            else:
                st.error("Please enter a contest name")

def join_contest_page():
    st.header("Join Contest")
    
    with st.form("join_contest"):
        join_code = st.text_input("Join Code").upper()
        player_name = st.text_input("Your Name")
        
        if st.form_submit_button("Join Contest"):
            if join_code and player_name:
                player = st.session_state.contest_manager.join_contest(join_code, player_name)
                if player:
                    st.success("Successfully joined the contest!")
                    st.session_state.current_player = player
                else:
                    st.error("Invalid join code or contest is not active")
            else:
                st.error("Please fill in all fields")

def upload_trade_page():
    st.header("Upload Trade")
    
    if 'current_player' not in st.session_state:
        st.warning("Please join a contest first")
        return
    
    uploaded_file = st.file_uploader("Upload Robinhood Screenshot", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # Convert the uploaded file to bytes
        image_bytes = uploaded_file.getvalue()
        
        # Parse the screenshot
        trade_data = st.session_state.trade_parser.parse_screenshot(image_bytes)
        
        if trade_data["success"]:
            st.subheader("Extracted Trade Details")
            
            # Create a form for verification/editing
            with st.form("verify_trade"):
                trade_type = st.selectbox("Trade Type", ["buy", "sell"], 
                                        index=0 if trade_data.get("trade_type") == "buy" else 1)
                ticker = st.text_input("Ticker Symbol", value=trade_data.get("ticker", ""))
                quantity = st.number_input("Quantity", min_value=0.0, step=0.01, 
                                        value=float(trade_data.get("quantity", 0)))
                price = st.number_input("Price per Share", min_value=0.0, step=0.01, 
                                      value=float(trade_data.get("price", 0)))
                
                if st.form_submit_button("Confirm Trade"):
                    trade_data = {
                        "trade_type": trade_type,
                        "ticker": ticker,
                        "quantity": quantity,
                        "price": price,
                        "date": datetime.now()
                    }
                    trade = st.session_state.contest_manager.record_trade(
                        st.session_state.current_player.id,
                        trade_data
                    )
                    if trade:
                        st.success("Trade recorded successfully!")
        else:
            st.error(f"Failed to parse screenshot: {trade_data.get('error', 'Unknown error')}")
            st.info("Please enter trade details manually")
            
            # Manual entry form
            with st.form("manual_trade"):
                trade_type = st.selectbox("Trade Type", ["buy", "sell"])
                ticker = st.text_input("Ticker Symbol")
                quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
                price = st.number_input("Price per Share", min_value=0.0, step=0.01)
                
                if st.form_submit_button("Submit Trade"):
                    trade_data = {
                        "trade_type": trade_type,
                        "ticker": ticker,
                        "quantity": quantity,
                        "price": price,
                        "date": datetime.now()
                    }
                    trade = st.session_state.contest_manager.record_trade(
                        st.session_state.current_player.id,
                        trade_data
                    )
                    if trade:
                        st.success("Trade recorded successfully!")

def view_leaderboard_page():
    st.header("Leaderboard")
    
    if 'current_player' not in st.session_state:
        st.warning("Please join a contest first")
        return
    
    contest_id = st.session_state.current_player.contest_id
    leaderboard = st.session_state.contest_manager.get_leaderboard(contest_id)
    
    if leaderboard:
        df = pd.DataFrame(leaderboard)
        st.dataframe(df)
        
        # Check if contest is complete
        if st.session_state.contest_manager.check_contest_completion(contest_id):
            st.balloons()
            st.success("Contest completed! Check the leaderboard for final results.")

def main():
    st.title("Trading Contest Platform")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Create Contest", "Join Contest", "Upload Trade", "Leaderboard"]
    )
    
    if page == "Create Contest":
        create_contest_page()
    elif page == "Join Contest":
        join_contest_page()
    elif page == "Upload Trade":
        upload_trade_page()
    elif page == "Leaderboard":
        view_leaderboard_page()

if __name__ == "__main__":
    main()
