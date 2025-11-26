import streamlit as st
from components import header

st.set_page_config(page_title="Mini-Kahoot", layout="centered")

header("🎉 Mini-Kahoot")

st.write("Choisissez votre mode :")

if st.button("🧑‍🏫 Mode Prof"):
    st.switch_page("prof")

if st.button("🎓 Mode Élève"):
    st.switch_page("eleve")
