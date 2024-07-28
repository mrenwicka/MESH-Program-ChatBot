import os
import random
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv, find_dotenv

# Importing data
from data4 import teams23
from data1 import players23
from prompt import prompt1

# Assuming `from sidebar_player import player_stats` brings in the player_stats string as shown above
from sidebar_player import player_stats

from sidebar_teams import team_stats

# Load environment variables
load_dotenv(find_dotenv())
os.environ["SSL_CERT_FILE"] = os.getenv("REQUESTS_CA_BUNDLE")
OPEN_API_KEY = os.getenv("OPENAI_API_KEY")

# Parsing data from strings into useable formats
player_data = [line.split(',') for line in player_stats.split('\n')]
players_list = {data[4]: {"name": data[0], "ppg": data[1], "rpg": data[2], "apg": data[3]} for data in player_data}
team_data = [line.split(',') for line in team_stats.split('\n')]
teams_list = {data[4]: {"team": data[0], "wins": data[1], "losses": data[2], "ORtg": data[3], "DRtg": data[4]} for data in team_data}


# Adding custom CSS for beautiful display
st.set_page_config(layout="wide")

st.markdown("""
    <style>
        /* Overall body adjustments */
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            color: #fff; 
        }

        /* Dynamic gradient animation */
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* Sidebar adjustments */
        .css-18e3th9 {
            background-color: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(8px);
        }

        /* Table styling */
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #6c5ce7;
            color: #ffffff;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f1f1f1;
            cursor: pointer;
        }

        /* Button styling */
        .stButton>button {
            border: none;
            border-radius: 4px;
            padding: 10px 24px;
            background-image: linear-gradient(to right, #ff416c, #ff4b2b);
            font-size: 16px;
            font-weight: bold;
            color: white;
            box-shadow: 0 4px 14px 0 rgba(0, 0, 0, 0.11);
            transition: transform 0.2s;
            width: 140px;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            background-image: linear-gradient(to right, #ff4b2b, #ff416c);
        }

        /* Input and Text area styling */
        .stTextInput>div>div>input,
        .stTextArea>textarea {
            border-radius: 4px;
            border: none;
            padding: 10px;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

# Title with custom style
st.markdown('<h1 style="color:DodgerBlue; text-align: center;">Basket Bot 🏀</h1>', unsafe_allow_html=True)

st.sidebar.title("LeRandomizer")

# option = st.sidebar.selectbox('Choose what to randomize:', ['Players', 'Teams'])
def display_results(option, selection):
    if option == 'Players':
        title = ["Name", "RPG", "APG", "PPG"]
        table_html = f"<table><thead><tr>{''.join([f'<th>{t}</th>' for t in title])}</tr></thead><tbody>"
        for player_id in selection:
            player_stats = players_list[player_id]
            row = f"<tr><td>{player_stats['name']}</td><td>{player_stats['ppg']}</td><td>{player_stats['rpg']}</td><td>{player_stats['apg']}</td></tr>"
            table_html += row
    else:
        title = ["Team", "Wins", "Losses", "Offensive Rating", "Defensive Rating"]
        table_html = f"<table><thead><tr>{''.join([f'<th>{t}</th>' for t in title])}</tr></thead><tbody>"
        for team_id in selection:
            team_stats = teams_list[team_id]
            row = (f"<tr><td>{team_stats['team']}</td><td>{team_stats['wins']}</td><td>{team_stats['losses']}"
                   f"</td><td>{team_stats['ORtg']}</td><td>{team_stats['DRtg']}</td></tr>")
            table_html += row
            
    table_html += "</tbody></table>"
    st.sidebar.markdown(table_html, unsafe_allow_html=True)

option = st.sidebar.selectbox('Choose what to randomize:', ['Players', 'Teams'])
if st.sidebar.button('Randomize'):
    if option == 'Players':
        random_selection = random.sample(list(players_list.keys()), 2)
    elif option == 'Teams':
        random_selection = random.sample(list(teams_list.keys()), 2)
    display_results(option, random_selection)

# Configuration for Azure OpenAI
client = AzureOpenAI(
    api_version="2024-02-01",
    azure_endpoint=os.getenv("OPENAI_API_BASE_URL"),
    api_key=OPEN_API_KEY,
)

# Session states for model and messages
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-0513"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Reserve space for sidebar content
for _ in range(1): 
    st.sidebar.text("")

# Function to clear session state
def clear_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# Refresh button to clear state and rerun
if st.sidebar.button('Refresh Page'):
    clear_state()
    st.experimental_rerun()

# Display main message area
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Inputs
if prompt := st.chat_input("Ask any basketball-related question"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Include selected players or teams in the context if they exist
    if 'random_selection' in locals():
        context = f" (Related to: {random_selection[0]} and {random_selection[1]})"
    else:
        context = ""
    
    full_prompt = f"{prompt}{context}"
    
    with st.chat_message("assistant"):
        with st.spinner('Getting response...'):
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[{"role": "system", "content": prompt1 + players23 + teams23 + player_stats}] +
                             [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages] +
                             [{"role": "user", "content": full_prompt}],
                    stream=True,
                )
                response = st.write_stream(stream)

                
    st.session_state.messages.append({"role": "assistant", "content": response})
