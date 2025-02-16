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
        win_condition = st.text_input(
            "Win Condition",
            placeholder="E.g. When a player reaches $1,000 in profits..."
        )
        starting_balance = st.number_input(
            "Starting balance for each player ($)",
            min_value=1000.0,
            value=1000.0,
            step=1000.0
        )
        
        if st.form_submit_button("Create Contest"):
            if name and win_condition:
                contest = st.session_state.contest_manager.create_contest(
                    name=name,
                    win_condition=win_condition,
                    starting_balance=starting_balance
                )
                st.success(f"Contest created! Join code: {contest.join_code}")
            else:
                st.error("Please enter a contest name and win condition")

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
    
    # Get active contests
    active_contests = st.session_state.contest_manager.get_active_contests()
    if not active_contests:
        st.warning("No active contests found. Please create or join a contest first.")
        return

    # Contest selection
    selected_contest = st.selectbox(
        "Select Contest",
        options=active_contests,
        format_func=lambda x: f"{x.name} (Join Code: {x.join_code})"
    )

    if selected_contest:
        # Get players in the selected contest
        players = st.session_state.contest_manager.get_contest_players(selected_contest.id)
        if not players:
            st.warning("No players found in this contest. Please join the contest first.")
            return

        selected_player = st.selectbox(
            "Select Player",
            options=players,
            format_func=lambda x: x.name
        )

        if selected_player:
            # File uploader for screenshot
            uploaded_file = st.file_uploader("Upload trade screenshot", type=["png", "jpg", "jpeg"])
            
            # Process screenshot if uploaded
            trade_info = None
            if uploaded_file:
                with st.spinner("Processing screenshot..."):
                    trade_info = st.session_state.trade_parser.parse_screenshot(uploaded_file.getvalue())
                    if not trade_info["success"]:
                        st.error(f"Failed to parse screenshot: {trade_info.get('error', 'Unknown error')}")
                        st.info("Please enter trade details manually")
                        trade_info = None
            
            # Manual trade entry form, prefilled if screenshot was processed
            with st.form("trade_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    ticker = st.text_input(
                        "Ticker Symbol",
                        value=trade_info["ticker"].upper() if trade_info and trade_info["success"] else "",
                    ).upper()
                    
                    quantity = st.number_input(
                        "Quantity",
                        min_value=0.0,
                        step=1.0,
                        value=float(trade_info["quantity"]) if trade_info and trade_info["success"] else 0.0
                    )
                    
                
                with col2:
                    trade_type = st.selectbox(
                        "Trade Type",
                        options=["BUY", "SELL"],
                        index=1 if trade_info and trade_info["success"] and trade_info["trade_type"].upper() == "SELL" else 0
                    )
                    
                    price = st.number_input(
                        "Price per Share ($)",
                        min_value=0.0,
                        step=0.01,
                        value=float(trade_info["price"]) if trade_info and trade_info["success"] else 0.0
                    )
                
                # Default to today if no date in trade_info
                default_date = (
                    datetime.strptime(trade_info["date"], "%Y-%m-%d").date()
                    if trade_info and trade_info["success"] and "date" in trade_info
                    else datetime.now().date()
                )
                
                trade_date = st.date_input(
                    "Trade Date",
                    value=default_date
                )
                
                submit_button = st.form_submit_button("Submit Trade")
                
                if submit_button:
                    if not ticker or quantity <= 0 or price <= 0:
                        st.error("Please fill in all fields with valid values")
                    else:
                        st.write("Processing trade with following details:")
                        st.write(f"- Player: {selected_player.name}")
                        st.write(f"- Ticker: {ticker}")
                        st.write(f"- Type: {trade_type}")
                        st.write(f"- Quantity: {quantity}")
                        st.write(f"- Price: ${price:,.2f}")
                        st.write(f"- Date: {trade_date}")
                        
                        # Convert date to datetime for database
                        trade_datetime = datetime.combine(trade_date, datetime.min.time())
                        
                        # Process the trade
                        trade = st.session_state.contest_manager.process_trade(
                            player_id=selected_player.id,
                            ticker=ticker,
                            trade_type=trade_type,
                            quantity=quantity,
                            price=price,
                            trade_date=trade_datetime
                        )
                        if trade:
                            st.success("Trade processed successfully!")
                            st.balloons()
                        else:
                            st.error("Failed to process trade. Check the terminal for detailed error message.")

def view_leaderboard_page():
    st.header("Leaderboard")
    
    # Get active contests
    active_contests = st.session_state.contest_manager.get_active_contests()
    if not active_contests:
        st.warning("No active contests found. Create or join a contest to view leaderboards.")
        return

    # Contest selection
    selected_contest = st.selectbox(
        "Select Contest",
        options=active_contests,
        format_func=lambda x: f"{x.name} (Join Code: {x.join_code})"
    )

    if selected_contest:
        # Show contest details
        st.subheader(f"📊 {selected_contest.name}")
        st.markdown(f"""
        **Win Condition:**  
        {selected_contest.win_condition}

        **Starting Balance:**
        ${selected_contest.starting_balance:,.2f}

        **Join Code:**  
        `{selected_contest.join_code}`
        """)
        
        # Get and display leaderboard
        leaderboard = st.session_state.contest_manager.get_leaderboard(selected_contest.id)
        if leaderboard:
            st.subheader("Rankings")
            # Create a formatted table
            data = []
            for rank, player in enumerate(leaderboard, 1):
                data.append({
                    "Rank": rank,
                    "Player": player["name"],
                    "Portfolio Value": f"${player['portfolio_value']:,.2f}",
                    "Cash Balance": f"${player['cash_balance']:,.2f}",
                    "Total Profit/Loss": f"${player['total_profit']:,.2f}",
                    "Return": f"{(player['total_profit'] / selected_contest.starting_balance * 100):.1f}%"
                })
            
            st.dataframe(
                data,
                column_config={
                    "Rank": st.column_config.NumberColumn(format="%d"),
                    "Portfolio Value": st.column_config.TextColumn(),
                    "Cash Balance": st.column_config.TextColumn(),
                    "Total Profit/Loss": st.column_config.TextColumn(),
                    "Return": st.column_config.TextColumn(),
                },
                hide_index=True
            )
            
            # End Contest Section
            st.subheader("End Contest")
            if st.button("🏆 End Contest"):
                st.info("Please review the contest details before selecting a winner:")
                
                # Show win condition again
                st.markdown(f"""
                **Win Condition:**  
                {selected_contest.win_condition}
                """)
                
                # Show current rankings again
                st.dataframe(
                    data,
                    column_config={
                        "Rank": st.column_config.NumberColumn(format="%d"),
                        "Player": st.column_config.TextColumn(),
                        "Portfolio Value": st.column_config.TextColumn(),
                        "Cash Balance": st.column_config.TextColumn(),
                        "Total Profit/Loss": st.column_config.TextColumn(),
                        "Return": st.column_config.TextColumn(),
                    },
                    hide_index=True
                )
                
                # Winner selection
                winner = st.selectbox(
                    "Select Winner",
                    options=[player for player in st.session_state.contest_manager.get_contest_players(selected_contest.id)],
                    format_func=lambda x: f"{x.name}"
                )
                
                if winner:
                    if st.button("💰 Payout with Payman"):
                        if st.session_state.contest_manager.end_contest(selected_contest.id, winner.id):
                            if st.session_state.contest_manager.payout_winner(selected_contest.id, winner.id):
                                st.success(f"🎉 Contest ended! Winner {winner.name} has been paid!")
                                st.balloons()
                            else:
                                st.error("Contest ended but payment failed. Please try payment again.")
                        else:
                            st.error("Failed to end contest. Please try again.")
            
            # Show trade history
            st.subheader("Trade History")
            trades = st.session_state.contest_manager.get_contest_trades(selected_contest.id)
            if trades:
                trade_data = [{
                    "Date": trade["date"].strftime("%Y-%m-%d %H:%M"),
                    "Player": trade["player"],
                    "Action": f"{'🔴 SELL' if trade['type'] == 'SELL' else '🟢 BUY'}",
                    "Ticker": trade["ticker"],
                    "Quantity": f"{trade['quantity']:,.0f}",
                    "Price": f"${trade['price']:,.2f}",
                    "Total": f"${abs(trade['total']):,.2f}"
                } for trade in trades]
                
                st.dataframe(
                    trade_data,
                    column_config={
                        "Date": st.column_config.DatetimeColumn(
                            "Date & Time",
                            format="MMM D, YYYY h:mm A",
                            width="medium"
                        ),
                        "Player": st.column_config.TextColumn(
                            "Player",
                            width="small"
                        ),
                        "Action": st.column_config.TextColumn(
                            "Action",
                            width="small"
                        ),
                        "Ticker": st.column_config.TextColumn(
                            "Symbol",
                            width="small"
                        ),
                        "Quantity": st.column_config.NumberColumn(
                            "Quantity",
                            format="%d",
                            width="small"
                        ),
                        "Price": st.column_config.TextColumn(
                            "Price/Share",
                            width="small"
                        ),
                        "Total": st.column_config.TextColumn(
                            "Total Amount",
                            width="medium",
                            help="Total amount of the trade (price × quantity)"
                        ),
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No trades recorded yet in this contest.")
        else:
            st.info("No trades recorded yet in this contest.")

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
