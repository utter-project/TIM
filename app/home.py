from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

from app.common import get_role, MODELS, parameters, provider, save, upload

if "anthropic" == provider:
    llm = ChatAnthropic(**{
            **{"anthropic_api_url": MODELS[provider]["base_url"], "anthropic_api_key": MODELS[provider]["api_key"]},
            **parameters
        })
else:
    llm = ChatOpenAI(**{
            **{"base_url": MODELS[provider]["base_url"], "api_key": MODELS[provider]["api_key"]},
            **parameters
        })

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

for message in st.session_state.messages[1:]:
    with st.chat_message(get_role(message)):
        st.markdown(message.content)

if utterance := st.chat_input("can I ask you something?"):
    st.session_state.messages.append(HumanMessage(content=utterance))
    with st.chat_message("user"):
        st.markdown(utterance)

    with st.chat_message("assistant"):
        stream = llm.stream(st.session_state.messages)
        response = st.write_stream(stream)
        st.session_state.messages.append(AIMessage(content=response))

save()

with st.sidebar:
    st.image("assets/tim.png")
    st.divider()

    st.subheader(":robot_face: about this agent")
    if "help" in st.session_state:
        st.markdown(st.session_state.help)
    st.divider()

    st.subheader(":information_source: if you need some help")
    st.markdown(help)