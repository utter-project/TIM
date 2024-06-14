import json, os
import streamlit as st
from datetime import datetime
import langchain_core
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama



MODELS = {
    #"local": {"model": "mistral-ins-7b-q4", "api_key": "not-needed", "base_url": "http://127.0.0.1:1337/"},
    "local": {"model": "gemma-2b", "api_key": "not-needed", "base_url": "http://127.0.0.1:1337/"},
    #"nle": {"model": "phi3:instruct", "api_key": "not-needed", "base_url": "http://10.57.16.172:11434"},
    "nle": {"model": "llama3:70b-instruct-fp16", "api_key": "not-needed", "base_url": "http://10.57.16.172:11434"},
    "openai-gpt-3.5-turbo": {"model": "gpt-3.5-turbo-0125",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "https://api.openai.com/v1"},
    "openai-gpt-4": {"model": "gpt-4-0125-preview",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "https://api.openai.com/v1"},
    "openai-gpt-4o": {"model": "gpt-4o-2024-05-13",  "api_key": os.environ["OPENAI_API_KEY"], "base_url": "https://api.openai.com/v1"}
#    "anthropic-haiku": {"model": "claude-3-haiku-20240307", "api_key": os.environ["ANTHROPIC_API_KEY"], "base_url": "https://api.anthropic.com"},
#    "anthropic-sonnet": {"model": "claude-3-sonnet-20240229", "api_key": os.environ["ANTHROPIC_API_KEY"], "base_url": "https://api.anthropic.com"}
}

DEFAULT = {
        "temperature": 0.7
    }

get_stamp = lambda c: datetime.now().strftime(f"%Y%m%d{c}%H%M%S")

get_role = lambda m: {AIMessage: "assistant", HumanMessage: "human", SystemMessage: "system"}[type(m)]
serialize_messages = lambda ms: [{"source": s, "role": get_role(m), "content": m.content} for (s, m) in ms]

def load_meeting_name():
    try:
        with open('meeting_name.txt', 'r') as file:
            return file.read()
    except FileNotFoundError:
        return ''

def save():
    utterer = MODELS[st.session_state.utterer].copy()
    del utterer["api_key"]
    filterer = MODELS[st.session_state.filterer].copy()
    del filterer["api_key"]
    interaction = {
        "scenario": st.session_state.scenario,
        "human": st.session_state.human,
        "assistant": st.session_state.assistant,
        "filters": st.session_state.filters,
        "messages": serialize_messages(st.session_state.messages),
        "utterer": utterer,
        "filterer": filterer,
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

def load_file(location, name, part):
    filename = f"./{location}/{name}/{part}.md"
    try:
        with open(filename) as f:
            system[part] = '\n'.join(f.readlines())
    except FileNotFoundError:
        system[part] = ""
        st.error(f"File {filename} not found")
    except Exception as e:
        system[part] = ""
        st.error(f"An error occurred: {e}")


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
        st.session_state.utterer = scenario["utterer"]
        st.session_state.filterer = scenario["filterer"]\
            if "filterer" in scenario else scenario["utterer"]
        st.session_state.filters = scenario["filters"]\
            if "filters" in scenario else ["be polite."]
        st.session_state.filter_emoji = scenario["filter_emoji"]\
            if "filter_emoji" in scenario else ":face_with_one_eyebrow_raised:"
        st.session_state.principle_emoji = scenario["principle_emoji"]\
            if "principle_emoji" in scenario else ":anxious_face_with_sweat:"

    system = dict()

    # List of parts excluding 'meeting'
    parts = ["persona", "principles", "content"]
    for part in parts:
        try:
            with open(f"./{location}/{name}/{part}.md") as f:
                system[part] = '\n'.join(f.readlines())
        except:
                system[part] = ""


    # Add a file uploader for the user to upload the 'meeting' content dynamically
    #the line below does not work so trying a different approach
    #uploaded_file = st.file_uploader("Upload the meeting content file here:", type=["md"])
    #ability to load a meeting file

    if 'meeting_name' not in st.session_state:
        st.session_state['meeting_name'] = load_meeting_name()


    try:
        with open(f"./{location}/{name}/{st.session_state['meeting_name']}.md") as f:
            system["meeting"] = '\n'.join(f.readlines())
            print("meeting file uploaded")
    except:
            system["meeting"] = ""
            print("meeting file NOT uploaded")

    # List of parts INCLUDING 'meeting'
    parts = ["persona", "principles", "content", "meeting"]

    if "messages" not in st.session_state:
        st.session_state.messages = [
                ("application", SystemMessage(content='\n'.join([system[p] for p in parts])))
            ]


def principles(name="default"):
    location = "scenarios"
    ok = True
    try:
        scenario = json.loads(open (f"./{location}/{name}/config.json", "r").read())
    except:
        ok = False

    part = "principles"
    try:
        with open(f"./{location}/{name}/{part}.md") as f:
            princ = '\n'.join(f.readlines())
    except:
            princ = ""

    return princ


def connect(llm, params=DEFAULT, models=MODELS):

    parameters = params.copy()
    parameters["model"] = models[llm]["model"]

    if llm.startswith("anthropic"):
        client = ChatAnthropic(**{
                **{"anthropic_api_url": models[llm]["base_url"], "anthropic_api_key": models[llm]["api_key"]},
                **parameters
            })
    if llm.startswith("nle"):
        client = ChatOllama(**{
                **{"base_url": models[llm]["base_url"], "api_key": models[llm]["api_key"]},
                **parameters
            })
    else:
        client = ChatOpenAI(**{
                **{"base_url": models[llm]["base_url"], "api_key": models[llm]["api_key"]},
                **parameters
            })

    return client
