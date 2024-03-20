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
        "temperature": 0.3
    }

provider = os.environ["llm_provider"]
parameters = default.copy()
parameters["model"] = MODELS[provider]["model"]

get_stamp = lambda c: datetime.now().strftime(f"%Y%m%d{c}%H%M%S")

get_role = lambda m: {AIMessage: "assistant", HumanMessage: "human", SystemMessage: "system"}[type(m)]
serialize_messages = lambda ms: [{"role": get_role(m), "content": m.content} for m in ms]

def save():
    interaction = {
        "scenario": st.session_state.scenario,
        "human": st.session_state.human,
        "assistant": st.session_state.assistant,
        "messages": serialize_messages(st.session_state.messages),
        "model": MODELS[provider]["model"],
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
        interaction = json.loads(open (f"./{location}/{name}/config.json", "r").read())
    except:
        ok = False

    if ok:
        if "show_context" in interaction :
            st.session_state.show_context = interaction["show_context"]
        else:
            st.session_state.show_context = True
        st.session_state.scenario = interaction["scenario"]
        if "help" in interaction:
            st.session_state.help = interaction["help"]
        st.session_state.human = interaction["human"] if "human" in interaction else "Human"
        st.session_state.assistant = interaction["assistant"] if "assistant" in interaction else "Agent"

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
