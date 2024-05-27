import os
import time
import streamlit as st
from openai import OpenAI
from datetime import datetime
import re

# Set OpenAI client, assistant AI, and assistant AI thread
@st.cache_resource
def load_openai_client_and_assistant():
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    my_assistant = client.beta.assistants.retrieve(st.secrets['assistant_id'])
    thread = client.beta.threads.create()
    return client, my_assistant, thread

client, my_assistant, assistant_thread = load_openai_client_and_assistant()

# Check in loop if assistant AI parses our request
def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(0.5)
    return run

# Preprocess response to correctly render LaTeX
def preprocess_response(response):
    if isinstance(response, list):
        response = response[0]  # Assuming the first element is the text content
    response = response.replace('\\n', '\n')
    response = response.replace('\\', '\\\\')
    return response

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

        # Debug: print the type and content of the messages
        for msg in messages.data:
            if msg.role == "assistant":
                st.write(f"Debug: msg.content type: {type(msg.content)}")
                st.write(f"Debug: msg.content: {msg.content}")
                
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

# Function to render message parts
def render_message(message):
    # Ensure the message is a string
    message = str(message)
    # Split the message into parts using a regex to detect LaTeX expressions
    parts = re.split(r'(\$.*?\$)', message)
    for part in parts:
        if part.startswith('$') and part.endswith('$'):
            latex_code = part[1:-1].strip()  # Remove the dollar signs and strip whitespace
            try:
                st.latex(latex_code)
            except Exception as e:
                st.error(f"Error rendering LaTeX: {e}\nLaTeX code: {latex_code}")
        else:
            st.markdown(part)

# Comment out the test conversation
# test_conversation = [
#     ("user", "solve another problem: A sample of carbon-14 has a half-life of 5730 years and an initial activity of $2.5 \\times 10^3$ Bq. Calculate the remaining activity after 11460 years."),
#     ("assistant", """To solve this problem, we can use the formula for radioactive decay: $A = A_0 \\cdot e^{-\\lambda t}$ where:
# - (A) is the activity at time (t),
# - ($A_0$) is the initial activity,
# - ($\\lambda$) is the decay constant, and
# - (t) is the time.
#
# The decay constant ($\\lambda$) can be calculated using the half-life formula: $\\lambda = \\frac{\\ln(2)}{T_{1/2}}$ where $T_{1/2}$ is the half-life.
#
# Given:
# $A_0 = 2.5 \\times 10^3$ Bq (initial activity),
# $T_{1/2} = 5730$ years (half-life), and
# $t = 11460$ years (time),
#
# First, we calculate the decay constant $\\lambda$:
#
# $\\lambda = \\frac{\\ln(2)}{5730} \\approx 1.21 \\times 10^{-4}$ years$^{-1}$
#
# Next, we calculate the remaining activity after 11460 years:
#
# $A = 2.5 \\times 10^3 \\cdot e^{-1.21 \\times 10^{-4} \\times 11460}$
#
# $A \\approx 2.5 \\times 10^3 \\cdot e^{-1.38}$
#
# $A \\approx 2.5 \\times 10^3 \\cdot 0.25$
#
# $A \\approx 625$ Bq
#
# So, the remaining activity after 11460 years is approximately 625 Bq.""")
# ]

# # Add sample conversation to the session state
# for role, message in test_conversation:
#     st.session_state.conversation_history.append((role, message))

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
