import json, os
import streamlit as st
import tiktoken
from datetime import datetime


CONTEXT_SIZE = 4096
MAX_TOKENS = 512

PARAMETERS = {
    "LMStudio": {"model": "local-model", "api_key": "not-needed", "base_url": "http://localhost:1234/v1"},
    "openai": {"model": "gpt-3.5-turbo",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "http://api.openai.com/v1"}
}

default = {"max_tokens": MAX_TOKENS,
    "temperature": 1,
    "top_p": 0.92,
}

provider = os.environ["llm_provider"]
parameters = default.copy()
parameters["model"] = PARAMETERS[provider]["model"]

get_stamp = lambda c: datetime.now().strftime(f"%Y%m%d{c}%H%M%S")

def save():
    conversation = {
        "scenario": st.session_state.scenario,
        "background": st.session_state.background,
        "setup": st.session_state.setup,
        "human": st.session_state.human,
        "assistant": st.session_state.assistant,
        "utterances": st.session_state.utterances,
        "model": PARAMETERS[provider]["model"],
    }
    if "help" in st.session_state:
        conversation["help"] = st.session_state.help
    if "stamp" in st.session_state:
        stamp = st.session_state["stamp"]
    else:
        stamp = get_stamp('.')
        st.session_state["stamp"] = stamp
    user_id_stamp = '.'.join([st.session_state["user_id"], stamp]) if "user_id" in st.session_state else stamp

    with open(f"save/{st.session_state.scenario.lower().replace(' ', '_')}.{user_id_stamp}.json", 'w') as json_file:
        json.dump(conversation, json_file)
    
    enc = tiktoken.encoding_for_model(PARAMETERS["openai"]["model"]) # IMPROVE THIS

    n_tokens = st.session_state.n_tokens\
        + sum([len(enc.encode(u)) for (_, u) in st.session_state.utterances])
    if 0.9 * (CONTEXT_SIZE - MAX_TOKENS) < n_tokens:
        st.session_state.speakable = False
    
def upload(name="default"):

    location = "scenarios"
    ok = True
    try:
        conversation = json.loads(open (f"./{location}/{name}.json", "r").read())
    except:
        ok = False

    if ok:
        if "show_context" in conversation:
            st.session_state.show_context = conversation["show_context"]
        else:
            st.session_state.show_context = True
        st.session_state.background = conversation["background"]
        st.session_state.setup = conversation["setup"]
        st.session_state.scenario = conversation["scenario"]
        if "help" in conversation:
            st.session_state.help = conversation["help"]
        st.session_state.human = conversation["human"] if "human" in conversation else "Human"
        st.session_state.assistant = conversation["assistant"] if "assistant" in conversation else "Agent"
        st.session_state.utterances = conversation["utterances"] if "utterances" in conversation else list()

        enc = tiktoken.encoding_for_model(PARAMETERS["openai"]["model"]) # IMPROVE THIS

        st.session_state.n_tokens = len(enc.encode(st.session_state.background))
        st.session_state.n_tokens += len(enc.encode(st.session_state.setup))
        st.session_state.speakable = True