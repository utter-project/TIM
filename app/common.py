import json, os
import streamlit as st
from datetime import datetime
import langchain_core
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


MODELS = {
    "LMStudio": {"model": "local-model", "api_key": "not-needed", "base_url": "http://localhost:1234/v1"},
    "openai-gpt-3.5-turbo": {"model": "gpt-3.5-turbo-0125",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "https://api.openai.com/v1"},
    "openai-gpt-4": {"model": "gpt-4-0125-preview",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "https://api.openai.com/v1"},
    "anthropic-haiku": {"model": "claude-3-haiku-20240307", "api_key": os.environ["ANTHROPIC_API_KEY"], "base_url": "https://api.anthropic.com"},
    "anthropic-sonnet": {"model": "claude-3-sonnet-20240229", "api_key": os.environ["ANTHROPIC_API_KEY"], "base_url": "https://api.anthropic.com"}
}

default = {
        "temperature": 0.7
    }

parameters = default.copy()

get_stamp = lambda c: datetime.now().strftime(f"%Y%m%d{c}%H%M%S")

get_role = lambda m: {AIMessage: "assistant", HumanMessage: "human", SystemMessage: "system"}[type(m)]
serialize_messages = lambda ms: [{"source": s, "role": get_role(m), "content": m.content} for (s, m) in ms]

def save():
    utterer = MODELS[st.session_state.utterer].copy()
    del utterer["api_key"]
    interaction = {
        "scenario": st.session_state.scenario,
        "human": st.session_state.human,
        "assistant": st.session_state.assistant,
        "filters": st.session_state.filters,
        "messages": serialize_messages(st.session_state.messages),
        "utterer": utterer
    }
    if "help" in st.session_state:
        interaction["help"] = st.session_state.help
    if "stamp" in st.session_state:
        stamp = st.session_state["stamp"]
    else:
        stamp = get_stamp('.')
        st.session_state["stamp"] = stamp
    user_id_stamp = '.'.join([st.session_state["user_id"], stamp]) if "user_id" in st.session_state else stamp

    with open(f"save/{st.session_state.scenario.lower().replace(' ', '_')}.{user_id_stamp}.json", 'w') as json_file:
        json.dump(interaction, json_file)
    
def upload(name="default"):
    location = "scenarios"
    ok = True
    try:
        scenario = json.loads(open (f"./{location}/{name}/config.json", "r").read())
    except:
        ok = False

    st.session_state.scenario = name
    if ok:
        st.session_state.welcome = scenario["welcome"]
        if "help" in scenario:
            st.session_state.help = scenario["help"]
        st.session_state.human = scenario["human"]\
            if "human" in scenario else "Human"
        st.session_state.assistant = scenario["assistant"]\
            if "assistant" in scenario else "Agent"
        st.session_state.filters = scenario["filters"]\
            if "filters" in scenario else ["be polite."]
        st.session_state.filter_emoji = scenario["filter_emoji"]\
            if "filter_emoji" in scenario else ":face_with_one_eyebrow_raised:"
        st.session_state.utterer = scenario["utterer"]

    system = dict()
    parts = ["persona", "principles", "content"]
    for part in parts:
        try:
            with open(f"./{location}/{name}/{part}.md") as f:
                system[part] = '\n'.join(f.readlines())
        except:
                system[part] = ""
    if "messages" not in st.session_state:
        st.session_state.messages = [
                ("application", SystemMessage(content='\n'.join([system[p] for p in parts])))
            ]
