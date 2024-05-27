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

        # Append the assistant's responses to the session state
        for msg in messages.data:
            if msg.role == "assistant":
                st.session_state.conversation_history.append(("assistant", msg.content))  # Append assistant response
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
            # Ensure LaTeX backslashes are double-escaped in markdown text
            part = part.replace('\\', '\\\\')
            st.markdown(part)

# Sample test conversation
test_conversation = [
    ("user", "solve Example 14 [CIE N2011/41/8b] A pure sample of phosphorus (P-33) which has a decay constant of 3.23 × 10-7 s-1 has an initial activity of 3.7 × 10^6 Bq. Calculate the number of P-33 nuclei remaining in the sample after 30 days."),
    ("assistant", "To solve this problem, we can use the formula for radioactive decay: $A = A_0 \cdot e^{-\lambda t}$ where: \n\n- (A) is the activity at time (t), \n- (A_0) is the initial activity, \n- (\lambda) is the decay constant, and \n- (t) is the time."),
    ("assistant", "Given: $A_0 = 3.7 \times 10^6 \text{Bq}$ (initial activity), $\lambda = 3.23 \times 10^{-7} \text{s}^{-1}$ (decay constant), and we need to find the activity after 30 days."),
    ("assistant", "First, we need to convert 30 days to seconds: \n\n$30 \text{days} = 30 \times 24 \times 60 \times 60 \ \text{seconds}$"),
    ("assistant", "Then, we can calculate the activity after 30 days using the given data and the formula above. The number of remaining nuclei can also be calculated by dividing the activity by the decay constant (since activity is proportional to the number of nuclei)."),
    ("assistant", "Let's perform the calculations: \n\nFirst, we calculate the time in seconds for 30 days: \n\n$30 \text{days} = 30 \times 24 \times 60 \times 60 \ \text{seconds} = 2,592,000 \ \text{seconds}$")
]

# Add sample conversation to the session state
for role, message in test_conversation:
    st.session_state.conversation_history.append((role, message))

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
