import openai
import streamlit as st

from app.common import save, upload, get_stamp
from app.common import PARAMETERS, parameters, provider

client = openai.Client(base_url=PARAMETERS[provider]["base_url"], api_key=PARAMETERS[provider]["api_key"])

help = """`speak` sends your utterance to the agent. Its answer is then streams back to you.

Note that the conversation is saved to a log file after each turn of utterance and response.
"""

if "scenario" not in st.session_state:
    params = st.query_params
    if "scenario" in params:
        upload(params["scenario"][0])
    else:
        upload("default")

st.subheader(st.session_state.scenario)

if "messages" not in st.session_state:
    st.session_state.messages = [{
            "role": "system",
            "content": '\n'.join([st.session_state.background, st.session_state.setup])
        }]

for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("can I ask you something?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(**{
                **parameters,
                **{
                    "model": parameters["model"],
                    "messages": [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    "stream": True,
                }
            }
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})

save()

with st.sidebar:
    st.subheader(":robot_face: about this agent")
    if "help" in st.session_state:
        st.markdown(st.session_state.help)
    st.image("assets/tim.jpeg")
    st.divider()

    st.subheader(":information_source: if you need some help")
    st.markdown(help)