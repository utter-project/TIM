import json, os
import streamlit as st
from datetime import datetime
import langchain_core
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


MODELS = {
    "LMStudio": {"model": "local-model", "api_key": "not-needed", "base_url": "http://localhost:1234/v1"},
    "openai": {"model": "gpt-3.5-turbo",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "https://api.openai.com/v1"},
    "anthropic": {"model": "claude-3-haiku-20240307", "api_key": os.environ["ANTHROPIC_API_KEY"], "base_url": "https://api.anthropic.com"}
}

default = {
        "temperature": 0.6
    }

parameters = default.copy()

get_stamp = lambda c: datetime.now().strftime(f"%Y%m%d{c}%H%M%S")

get_role = lambda m: {AIMessage: "assistant", HumanMessage: "human", SystemMessage: "system"}[type(m)]
serialize_messages = lambda ms: [{"role": get_role(m), "content": m.content} for m in ms]

def save():
    interaction = {
        "scenario": st.session_state.scenario,
        "human": st.session_state.human,
        "assistant": st.session_state.assistant,
        "filters": st.session_state.filters,
        "messages": serialize_messages(st.session_state.messages),
        "provider": MODELS[st.session_state.provider],
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
    print(name)
    location = "scenarios"
    ok = True
    try:
        scenario = json.loads(open (f"./{location}/{name}/config.json", "r").read())
    except:
        ok = False

    if ok:
        st.session_state.scenario = scenario["scenario"]
        if "help" in scenario:
            st.session_state.help = scenario["help"]
        st.session_state.human = scenario["human"] if "human" in scenario else "Human"
        st.session_state.assistant = scenario["assistant"] if "assistant" in scenario else "Agent"
        st.session_state.filters = scenario["filters"] if "filters" in scenario.keys() else ["be polite."]
        st.session_state.provider = scenario["provider"]

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
                SystemMessage(content='\n'.join([system[p] for p in parts]))
            ]
