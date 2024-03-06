import streamlit as st

from app.common import dialog, boldify, go_back, save, upload, utter, get_stamp

print("top")

help = """`speak` sends your utterance to the agent,  
`retry` requests an alternate response from the agent,  
`revert` suppresses both your previous utterance and the response from the agent from the conversation.

Note that the conversation is saved to a log file after each turn of utterance and response.
"""

if "scenario" not in st.session_state:
    params = st.query_params
    if "scenario" in params:
        upload(params["scenario"][0])
    else:
        upload("default")

tab1, tab2, tab3 = st.tabs([":robot_face: Welcome", ":speech_balloon: Conversation", ":information_source: Help"])

with tab1:
    st.subheader(st.session_state.scenario)
    if "help" in st.session_state:
        st.markdown(st.session_state.help)
    st.image("assets/tim.jpeg")

with tab2:
    # this is quite hacky...
    if "FormSubmitter:dialog-Retry" in st.session_state\
    or "FormSubmitter:dialog-Revert" in st.session_state:
        if st.session_state["FormSubmitter:dialog-Retry"]\
        or st.session_state["FormSubmitter:dialog-Revert"]:
            go_back()

    st.subheader(st.session_state.scenario)

    if "utterances" not in st.session_state:
        st.session_state.utterances = list()

    with st.form("dialog"):
        utterance = st.text_input(st.session_state.human, key="utterance")
        c1, c2, c3 = st.columns(3)
        with c1:
            submit = st.form_submit_button(label="Speak", disabled=not st.session_state.speakable)
        with c2:
            if utterance:
                retry = st.form_submit_button(label="Retry")
            else:
                retry = ''
        with c3:
            if utterance:
                revert = st.form_submit_button(label="Revert")
            else:
                revert = ''

        if submit or retry:
            if '' != utterance:
                answer, error = utter(utterance)
                warning = "sorry but the agent couldn't answer. You might want to try again..."
                if '' != error:
                    print(get_stamp(':'), error)
                    st.warning(warning, icon="😵‍💫")
                else:
                    st.session_state.utterances.append(("user", utterance))
                    st.session_state.utterances.append(("assistant", answer))

    for l in dialog(st.session_state.utterances[::-1]).split('\n'):
        st.write(boldify(l))

    save()

with tab3:
    st.markdown(help)