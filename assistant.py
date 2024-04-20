import os
import streamlit as st
from openai import OpenAI
import boto3
from datetime import datetime
import csv

# Initialize OpenAI


client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
assistant = openai_client.beta.assistants.retrieve(
    "asst_iWWEKeASol9qFLldO7LnSW3t"
)
# ASSISTANT_ID = "asst_iWWEKeASol9qFLldO7LnSW3t"

st.title("Practice with AI")
st.text("Which question would you like to discuss?")

user_input = st.chat_input("What is up?")
if user_input:
    thread = client.beta.threads.create(
        message=[
            {
                "role": "user",
                "content": [user_input],
            }
        ]
    )

run = client.beta.threads.runs.retrieve(
    thread_id=thread.id,
    assistant_id=assistant.id,
  )
 
# Wait for run to complete
while run.status != 'completed': 
  run = client.beta.threads.runs.retrieve(
    thread_id=thread.id,
    run_id=run.id
  )
  st.write(run,status)
  time.sleep(1)
else:
  st.write("Run Complete!")

message_response = client.beta.threads.messages.list(thread_id=thread.id)
messages = message_response.data

latest_message = message[0]
st.write(latest_message.content[0].text.value)
