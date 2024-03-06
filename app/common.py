import streamlit as st

import json, os
from datetime import datetime

import openai, tiktoken
import replicate

CONTEXT_SIZE = 4096
MAX_TOKENS = 512

PARAMETERS = {
    "replicate": {"model": "meta/llama-2-7b-chat:52551facc68363358effaacb0a52b5351843e2d3bf14f58aff5f0b82d756078c", "api_key": "", "base_url": ""},
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

def openai_utter(utterance, system):
    response, error = '', ''
    try:
        messages = [{"role": "system", "content": system}]
        for r, u in st.session_state.utterances:
            messages.append({"role": r, "content": u})
        messages.append({"role": "user", "content": utterance})
        response = chat({"messages": messages}).rstrip()

    except openai.APIError as e:
        error = (f"OpenAI API returned an API Error: {e}")
        pass
    except openai.APIConnectionError as e:
        error = f"Failed to connect to OpenAI API: {e}"
        pass
    except openai.RateLimitError as e:
        error = f"OpenAI API request exceeded rate limit: {e}"
        pass
    except openai.Timeout as e:
        error = f"OpenAI API request timed out: {e}"
        pass
    except openai.InvalidRequestError as e:
        error = f"Invalid request to OpenAI API: {e}"
        pass
    except openai.AuthenticationError as e:
        error = f"Authentication error with OpenAI API: {e}"
        pass
    except openai.ServiceUnavailableError as e:
        error = f"OpenAI API service unavailable: {e}"
        pass
    return response.rstrip(), error

def replicate_utter(utterance, system, _):
    userify = lambda u: f"[INST] {u} [/INST]"

    messages = [userify(u) if "user" == r else r for r, u in st.session_state.utterances]
    messages.append(userify(utterance))

    output = replicate.run(
        PARAMETERS[provider]["model"],
        input={
            "prompt": '\n'.join(messages),
            "system": system
        }
    )

    sequence = list()
    try:
        for token in output:
            sequence.append(token)
        response, error = ''.join(sequence), ''
    except:
        response, error = '', "Replicate API returned an error"

    return response.rstrip(), error

if provider in ["openai", "LMStudio"]:
    client = openai.Client(base_url=PARAMETERS[provider]["base_url"], api_key=PARAMETERS[provider]["api_key"])
    chat = lambda ms: client.chat.completions.create(**{**parameters, **ms}).choices[0].message.content
    utter_function = openai_utter
else:
    utter_function = replicate_utter

dialog = lambda us: '\n'.join([{"user": st.session_state.human, "assistant": st.session_state.assistant}[r] + f": {u}" for (r, u) in us])

def utter(utterance, function=utter_function):
    print(utterance)
    system = '\n'.join([st.session_state.background, st.session_state.setup])

    return function(utterance, system)

boldify = lambda l: ("**" + l.replace(":", "**:", 1)) if l.startswith(st.session_state.human) or l.startswith(st.session_state.assistant) else l

def go_back():
    if st.session_state.utterances:
        st.session_state.utterances.pop()
        _, utterance = st.session_state.utterances.pop()
        st.session_state.utterance = utterance.strip()

def command(cmd, password=None):
    if "list" == cmd:
        filenames = [fn for fn in sorted(os.listdir("save")) if fn.endswith(".json")]
        if not filenames:
            st.warning("no log files yet...")
        for fn in filenames:
            st.markdown(f"[{fn}](?filename={fn[:-5]}&password={password})")
    else:
        st.error(":rotating_light: unknown command!")

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