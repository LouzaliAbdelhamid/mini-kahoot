import streamlit as st

st.set_page_config(page_title="Mini-Kahoot", layout="centered")

st.title("🎉 Mini-Kahoot")

st.write("Choisissez votre mode :")

col1, col2 = st.columns(2)

with col1:
    if st.button("👨‍🏫 Mode Prof"):
        st.switch_page("prof.py")

with col2:
    if st.button("🎓 Mode Élève"):
        st.switch_page("eleve.py")
