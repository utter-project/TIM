from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
import re

from app.common import get_role, connect, save, upload, principles



if "scenario" not in st.session_state:
    params = st.query_params

    if "scenario" in params:
        upload(params["scenario"])
        #myprinciples+=principles(params["scenario"])
        st.session_state.myprinciples=principles(params["scenario"])
    else:
        upload("default")
        #myprinciples+=principles("default")
        st.session_state.myprinciples=principles("default")


utterer = connect(st.session_state.utterer)
filterer = connect(st.session_state.filterer, {"temperature": 0})

parser = StrOutputParser()

help = """Note that the conversation is saved to a log file after each turn of utterance and response."""
extract = lambda ms: [m for _, m in ms]

def save_meeting_name():
    with open('meeting_name.txt', 'w') as file:
        file.write(st.session_state['meeting_name'])


def check(llm=filterer, parser=parser):

    system = """  """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system),
         MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | llm | parser
    return chain.invoke({"messages": extract(st.session_state.messages[1::])})

st.subheader(st.session_state.welcome)

for (source, message) in st.session_state.messages[1:]:
    with st.chat_message(get_role(message)):
        st.markdown(((st.session_state.filter_emoji + " ") if "filterer" == source else "") + message.content)

if utterance := st.chat_input("try me!"):

    filterprompt = """You only act as a binary filter in front of a conversational agent. Your response to the utterance is OK if it respects the following guidelines and KO otherwise.
    Guidelines: a valid (OK) utterance should:
    {}""".format("- " + "\n- ".join(st.session_state.filters)+"\n Always add a short explanation after OK or KO about your decision. Now give your response for the following utterance: ")
    utterance4filter=filterprompt+utterance
    st.session_state.messages.append(("chat_input", HumanMessage(content=utterance4filter)))
    with st.chat_message("user"):
        st.markdown(utterance)
    # all inputs are first checked by a filtering LLM, check() is applied to utterance4filter
    pre_check = check()
    print("FILTER: ", pre_check)
    print("\n")
    if pre_check.startswith("OK"):
        # answer from the main model, streamed
        #need to go back from utterance4filter to utterance
        st.session_state.messages.pop()
        st.session_state.messages.append(("chat_input", HumanMessage(content=utterance)))
        with st.chat_message("assistant"):
            stream = utterer.stream(extract(st.session_state.messages))
            response = st.write_stream(stream)
            #start check principles - remove all this to go back to previous version
            #open principles.md filter_emoj
            #end read principles.md file
            principleprompt = """ You only act as a binary filter in front of a conversational agent. You should check if an utterance respect the following principles: \n"""
            principleprompt+=st.session_state.myprinciples
            response4principles=principleprompt+"Now answer OK if the following utterance respects the above principles and KO otherwise. Always add a short explanation about your decision: \n ["+response+"] "
            #print("RESPONSE4PRINCIPLES: ", response4principles)
            st.session_state.messages.append(("chat_input", HumanMessage(content=response4principles)))
            pre_check = check()
            print("PRINCIPLES: ", pre_check)
            print("\n")
            #end check principles
            #do a pop here otherwise principles will be shown on the chat interface
            if pre_check.startswith("OK"): #in PRINCIPLES=OK
                st.session_state.messages.pop()
                st.session_state.messages.append(("utterer", AIMessage(content=response)))
            else: #PRINCIPLES=KO
                st.session_state.messages.pop()
                st.markdown(st.session_state.principle_emoji + " [This answer might not respect my principles!]\n " )
                #st.session_state.messages.append(("utterer", AIMessage(content=pre_check)))
                st.session_state.messages.append(("utterer", AIMessage(content=response)))
    else:
        # answer from the filtering model
        #this pop is absolutaly needed here otherwise filter info will pollute the conversation history
        st.session_state.messages.pop()
        with st.chat_message("assistant"):
            tmp=re.sub("KO", "", pre_check)
            explanation=re.sub("Explanation:", "", tmp)
            #st.markdown(st.session_state.filter_emoji + " " + pre_check)
            st.markdown(st.session_state.filter_emoji + " " + explanation)
        st.session_state.messages.append(("filterer", AIMessage(content=pre_check)))

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
    st.divider()

    st.subheader(":green_book:  meeting transcript file")
    st.session_state['meeting_name'] = st.text_input("Enter the meeting name:")
    save_meeting_name()
