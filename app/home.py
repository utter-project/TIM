from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

from app.common import get_role, MODELS, parameters, save, upload

if "scenario" not in st.session_state:
    params = st.query_params
    if "scenario" in params:
        upload(params["scenario"])
    else:
        upload("default")

utterer = st.session_state.utterer
parameters["model"] = MODELS[utterer]["model"]

if utterer.startswith("anthropic"):
    llm = ChatAnthropic(**{
            **{"anthropic_api_url": MODELS[utterer]["base_url"], "anthropic_api_key": MODELS[utterer]["api_key"]},
            **parameters
        })
else:
    llm = ChatOpenAI(**{
            **{"base_url": MODELS[utterer]["base_url"], "api_key": MODELS[utterer]["api_key"]},
            **parameters
        })
    
parser = StrOutputParser()

help = """Note that the conversation is saved to a log file after each turn of utterance and response."""
extract = lambda ms: [m for _, m in ms]

def check(llm=llm, parser=parser):

    system = """You act as a filter in front of a specialized agent.
Respond GO to the utterance if it respects all the following guidelines, otherwise explain politely that you cannot answer that request, with a short, to the point, justification, in English, if you decide to reject it.\n
A valid utterance should:
{}""".format("- " + "\n- ".join(st.session_state.filters))

    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
         MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | llm | parser

    return chain.invoke({"messages": extract(st.session_state.messages[1::])})

st.subheader(st.session_state.welcome)

for (source, message) in st.session_state.messages[1:]:
    with st.chat_message(get_role(message)):
        st.markdown(((st.session_state.filter_emoji + " ") if "filter" == source else "") + message.content)

if utterance := st.chat_input("try me!"):
    st.session_state.messages.append(("chat_input", HumanMessage(content=utterance)))
    with st.chat_message("user"):
        st.markdown(utterance)

    # all inputs are first checked by a filtering LLM
    pre_check = check()
    if pre_check.startswith("GO"):
        # answer from the main model, streamed
        with st.chat_message("assistant"):
            stream = llm.stream(extract(st.session_state.messages))
            response = st.write_stream(stream)
            st.session_state.messages.append(("main", AIMessage(content=response)))
    else:
        # answer from the filtering model
        with st.chat_message("assistant"):
            st.markdown(st.session_state.filter_emoji + " " + pre_check)
        st.session_state.messages.append(("filter", AIMessage(content=pre_check)))

save()

with st.sidebar:
    st.image("assets/nle.png")
    st.divider()

    st.subheader(":robot_face: about this agent")
    if "help" in st.session_state:
        st.markdown(st.session_state.help)
    st.divider()

    st.subheader(":information_source: if you need some help")
    st.markdown(help)