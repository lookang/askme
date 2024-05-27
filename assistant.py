import os
import time
import streamlit as st
from openai import OpenAI
from datetime import datetime
import re

# Read the OpenAI API key from Streamlit's secrets management
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Set OpenAI client, assistant AI, and assistant AI thread
@st.cache_resource
def load_openai_client_and_assistant():
    client = OpenAI(api_key=OPENAI_API_KEY)
    assistant_id = 'asst_PiOQMpZUvHq07hqakNFuKEBS'
    my_assistant = client.beta.assistants.retrieve(assistant_id)
    thread = client.beta.threads.create()
    return client, my_assistant, thread

client, my_assistant, assistant_thread = load_openai_client_and_assistant()

# Display the bot ID being used
st.write(f"Using Bot ID: {my_assistant.id}")

# Check in loop if assistant AI parses our request
def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(0.5)
    return run

# Preprocess response to correctly render LaTeX and handle text content blocks
def preprocess_response(response):
    if isinstance(response, list) and len(response) > 0:
        response = response[0].text.value  # Assuming the first element is the TextContentBlock
    response = response.replace('\\n', '\n')
    response = response.replace('\\', '\\\\')
    return response

# Function to render message parts
def render_message(message):
    # Ensure the message is a string
    message = str(message)
    # Split the message into parts using a regex to detect LaTeX expressions
    parts = re.split(r'(\[.*?\])', message)
    for part in parts:
        if part.startswith('[') and part.endswith(']'):
            latex_code = part[1:-1].strip()  # Remove the square brackets and strip whitespace
            try:
                st.latex(latex_code)
            except Exception as e:
                st.error(f"Error rendering LaTeX: {e}\nLaTeX code: {latex_code}")
        else:
            st.markdown(part)

# Function to render bullet points with LaTeX
def render_bullet_points_with_latex(points):
    for point in points:
        st.markdown(f"- {point}")

# Initiate assistant AI response
def get_assistant_response(user_input=""):
    try:
        message = client.beta.threads.messages.create(
            thread_id=assistant_thread.id,
            role="user",
            content=user_input
        )
        run = client.beta.threads.runs.create(
            thread_id=assistant_thread.id,
            assistant_id=my_assistant.id
        )
        run = wait_on_run(run, assistant_thread)

        # Retrieve all the messages added after our last user message
        messages = client.beta.threads.messages.list(
            thread_id=assistant_thread.id, order="asc", after=message.id
        )

        for msg in messages.data:
            if msg.role == "assistant":
                preprocessed_content = preprocess_response(msg.content)
                st.session_state.conversation_history.append(("assistant", preprocessed_content))  # Append assistant response
    except Exception as e:
        st.error(f"Error in getting assistant response: {e}")

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def submit():
    user_input = st.session_state.query
    if user_input:  # Check if the user has entered any text
        # Append user input to conversation history before processing
        st.session_state.conversation_history.append(("user", user_input))
        # Get assistant's response
        get_assistant_response(user_input)
        # Clear the input field
        st.session_state.query = ''

st.title("Physics Topic 20: Nuclear Physics Assistant")
st.header('Conversation', divider='rainbow')

# Render the conversation history
for role, message in st.session_state.conversation_history:
    if role == 'user':
        st.markdown(f"<b style='color: yellow;'>{message}</b>", unsafe_allow_html=True)
    else:
        render_message(message)

st.text_input("How may I help you?", key='query', on_change=submit)

# Add a button to clear the conversation history
if st.button('Clear Conversation'):
    st.session_state.conversation_history = []
    st.experimental_rerun()
