import streamlit as st
import time
import json
from firebase import game_ref, players_ref, answers_ref, timer_ref
from components import header

st.set_page_config(page_title="Mini-Kahoot - Student", layout="centered")

header("🎓 Mini-Kahoot — Student")

# ---------- LOGIN ----------
pseudo = st.text_input("Your nickname:")
pin = st.number_input("Game PIN:", step=1)

if st.button("Join"):
    game = game_ref.get()
    if game and pin == game["pin"]:
        players_ref.child(pseudo).set(0)
        st.success("Connected! Waiting for the game...")
    else:
        st.error("Incorrect PIN")

game = game_ref.get()
if not game:
    st.stop()

state = game["state"]
current = game["current"]

# Load all questions
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# ---------- WAITING ----------
if state == "waiting":
    st.info("Waiting for the teacher to start...")

# ---------- QUESTION ----------
elif state == "in_question":
    q = QUESTIONS[current]
    header(q["question"])

    # TIMER
    timer_val = timer_ref.get()["time_left"]
    st.write(f"⏳ Time left: **{timer_val} sec**")

    # ---------- MCQ ----------
    if q["type"] == "mcq":
        choice = st.radio("Select your answer:", q["choices"])

        if st.button("Submit"):
            correct = q["choices"][q["answer"]]
            speed_bonus = timer_val * 10
            score = players_ref.child(pseudo).get() or 0

            if choice == correct:
                new_score = score + 1000 + speed_bonus
                players_ref.child(pseudo).set(new_score)
                st.success("Correct! Speed bonus applied.")
            else:
                st.error("Incorrect answer.")

            answers_ref.child(str(current)).child(pseudo).set(choice)

    # ---------- MATCHING ----------
    elif q["type"] == "match":
        st.subheader("Select the left sentence:")
        left_choice = st.radio("Left side:", q["left"])

        st.subheader("Select the correct ending:")
        right_choice = st.radio("Right side:", q["right"])

        if st.button("Submit"):
            left_index = q["left"].index(left_choice)
            right_index = q["right"].index(right_choice)

            correct = q["correct_pair"]
            # convert to list-of-lists if needed
            if not isinstance(correct[0], list):
                correct = [correct]

            is_correct = [left_index, right_index] in correct

            speed_bonus = timer_val * 10
            score = players_ref.child(pseudo).get() or 0

            if is_correct:
                new_score = score + 1000 + speed_bonus
                players_ref.child(pseudo).set(new_score)
                st.success("Correct match! Bonus added.")
            else:
                st.error("Incorrect match.")

            answers_ref.child(str(current)).child(pseudo).set({
                "left": left_index,
                "right": right_index
            })

# ---------- RESULTS ----------
elif state == "show_results":
    st.info("Waiting for next question...")

# ---------- PODIUM ----------
elif state == "podium":
    st.success("🎉 QUIZ FINISHED! 🎉")
    st.write("Check the podium on the big screen!")
