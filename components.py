import streamlit as st

def header(text):
    st.markdown(f"<h1 style='text-align:center;color:white'>{text}</h1>", unsafe_allow_html=True)

def sub(text):
    st.markdown(f"<h3 style='text-align:center;color:#ffdd00'>{text}</h3>", unsafe_allow_html=True)

def answer_button(label, css_class):
    return st.button(label, key=label, use_container_width=True)

def countdown(seconds):
    for i in range(seconds, -1, -1):
        st.session_state["timer"] = i
        yield i
