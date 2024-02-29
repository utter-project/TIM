PROVIDER = "replicate"
REPLICATE_MODEL = "meta/llama-2-7b-chat:52551facc68363358effaacb0a52b5351843e2d3bf14f58aff5f0b82d756078c"

CONTEXT_SIZE = 4096
MAX_TOKENS = 512

MODELS = {
    "instruct": "text-davinci-003",
    "chat": "gpt-3.5-turbo"
}

import streamlit as st

import json, os
from datetime import datetime

import openai, tiktoken
import replicate

openai.api_key = os.environ["OPENAI_API_KEY"]

default = {"max_tokens": MAX_TOKENS,
    "temperature": 1,
    "top_p": 0.92,
}

instruct_default = default.copy()
instruct_default["engine"] = MODELS["instruct"]

instruct_gpt = lambda p: openai.Completion.create(**{**instruct_default, **p}).choices[0].text

chat_default = default.copy()
chat_default["model"] = MODELS["chat"]

chat_gpt = lambda ms: openai.ChatCompletion.create(**{**chat_default, **ms}).choices[0].message.content

dialog = lambda us: '\n'.join([{"user": st.session_state.human, "assistant": st.session_state.assistant}[r] + f": {u}" for (r, u) in us])

get_stamp = lambda c: datetime.now().strftime(f"%Y%m%d{c}%H%M%S")

def openai_utter(utterance, system, model_family="chat"):
    response, error = '', ''
    try:
        if "chat" == model_family:
            messages = [{"role": "system", "content": system}]
            for r, u in st.session_state.utterances:
                messages.append({"role": r, "content": u})
            messages.append({"role": "user", "content": utterance})
            response = chat_gpt({"messages": messages}).rstrip()

        else:
            context = '\n'.join([system, '\n', dialog(st.session_state.utterances)])
            prompt = f"{context}\n{st.session_state.human}: {utterance}\n{st.session_state.assistant}:"
            response = instruct_gpt({"prompt": prompt, "stop": f"{st.session_state.human}:"})

    except openai.error.APIError as e:
        error = (f"OpenAI API returned an API Error: {e}")
        pass
    except openai.error.APIConnectionError as e:
        error = f"Failed to connect to OpenAI API: {e}"
        pass
    except openai.error.RateLimitError as e:
        error = f"OpenAI API request exceeded rate limit: {e}"
        pass
    except openai.error.Timeout as e:
        error = f"OpenAI API request timed out: {e}"
        pass
    except openai.error.InvalidRequestError as e:
        error = f"Invalid request to OpenAI API: {e}"
        pass
    except openai.error.AuthenticationError as e:
        error = f"Authentication error with OpenAI API: {e}"
        pass
    except openai.error.ServiceUnavailableError as e:
        error = f"OpenAI API service unavailable: {e}"
        pass
    return response.rstrip(), error

def replicate_utter(utterance, system, _):
    userify = lambda u: f"[INST] {u} [/INST]"

    messages = [userify(u) if "user" == r else r for r, u in st.session_state.utterances]
    messages.append(userify(utterance))

    output = replicate.run(
        REPLICATE_MODEL,
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


def utter(utterance, model_family="chat"):
    system = '\n'.join([st.session_state.background, st.session_state.setup])

    f = openai_utter if "openai" == PROVIDER else replicate_utter
    return f(utterance, system, model_family)

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

def save():
    conversation = {
        "scenario": st.session_state.scenario,
        "background": st.session_state.background,
        "setup": st.session_state.setup,
        "human": st.session_state.human,
        "assistant": st.session_state.assistant,
        "utterances": st.session_state.utterances,
        "model_family": st.session_state.model_family,
        "model": MODELS[st.session_state.model_family],
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
    
    enc = tiktoken.encoding_for_model(MODELS[st.session_state.model_family])

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
        if "model_family" in conversation:
            st.session_state.model_family = conversation["model_family"]
        else:
            st.session_state.model_family = "instruct"
        st.session_state.human = conversation["human"] if "human" in conversation else "Human"
        st.session_state.assistant = conversation["assistant"] if "assistant" in conversation else "Agent"
        st.session_state.utterances = conversation["utterances"] if "utterances" in conversation else list()

        enc = tiktoken.encoding_for_model(MODELS[st.session_state.model_family])

        st.session_state.n_tokens = len(enc.encode(st.session_state.background))
        st.session_state.n_tokens += len(enc.encode(st.session_state.setup))
        st.session_state.speakable = True