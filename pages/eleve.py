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
    if not pseudo or pseudo.strip() == "":
        st.error("Please enter a nickname.")
    elif game and pin == game["pin"]:
        # Prevent joining mid-game or duplicate nickname
        if game["state"] != "waiting":
            st.error("Cannot join, game already in progress.")
        else:
            existing_score = players_ref.child(pseudo).get()
            if existing_score is not None:
                st.error("Nickname already taken, choose another.")
            else:
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

    # Check if this student already answered
    prev_answer = answers_ref.child(str(current)).child(pseudo).get()
    if prev_answer is not None:
        # Already answered, display their answer and outcome
        if q["type"] == "mcq":
            chosen = prev_answer  # answer text
            correct_text = q["choices"][q["answer"]]
            if chosen == correct_text:
                st.success(f"✅ You answered: **{chosen}**. That is correct!")
            else:
                st.error(f"❌ You answered: **{chosen}**. That is incorrect.")
            st.info("Please wait for the next question...")
        elif q["type"] == "match":
            if isinstance(prev_answer, dict) and "left" in prev_answer and "right" in prev_answer:
                left_idx = prev_answer["left"]
                right_idx = prev_answer["right"]
                left_text = q["left"][left_idx] if left_idx is not None else None
                right_text = q["right"][right_idx] if right_idx is not None else None
                if left_text is not None and right_text is not None:
                    # Determine correctness
                    correct_pairs = q["correct_pair"]
                    if not isinstance(correct_pairs[0], list):
                        correct_pairs = [correct_pairs]
                    is_correct = [left_idx, right_idx] in correct_pairs
                    if is_correct:
                        st.success(f"✅ You matched: **{left_text} → {right_text}**. That is correct!")
                    else:
                        st.error(f"❌ You matched: **{left_text} → {right_text}**. That is incorrect.")
                else:
                    st.error("Your answer data is invalid.")
            else:
                st.error("Your answer data is invalid.")
            st.info("Please wait for the next question...")
    else:
        # Not answered yet, show input options
        if q["type"] == "mcq":
            choice = st.radio("Select your answer:", q["choices"])
            if st.button("Submit"):
                correct_text = q["choices"][q["answer"]]
                speed_bonus = timer_val * 10
                score = players_ref.child(pseudo).get() or 0

                if choice == correct_text:
                    new_score = score + 1000 + speed_bonus
                    players_ref.child(pseudo).set(new_score)
                    st.success("Correct! Speed bonus applied.")
                else:
                    st.error("Incorrect answer.")

                # Record the answer
                answers_ref.child(str(current)).child(pseudo).set(choice)
        elif q["type"] == "match":
            st.subheader("Select the left sentence:")
            left_choice = st.radio("Left side:", q["left"])
            st.subheader("Select the correct ending:")
            right_choice = st.radio("Right side:", q["right"])

            if st.button("Submit"):
                # Determine indices of selected options
                left_index = q["left"].index(left_choice)
                right_index = q["right"].index(right_choice)

                correct_pairs = q["correct_pair"]
                if not isinstance(correct_pairs[0], list):
                    correct_pairs = [correct_pairs]
                is_correct = [left_index, right_index] in correct_pairs

                speed_bonus = timer_val * 10
                score = players_ref.child(pseudo).get() or 0

                if is_correct:
                    new_score = score + 1000 + speed_bonus
                    players_ref.child(pseudo).set(new_score)
                    st.success("Correct match! Bonus added.")
                else:
                    st.error("Incorrect match.")

                # Record the answer
                answers_ref.child(str(current)).child(pseudo).set({
                    "left": left_index,
                    "right": right_index
                })

# ---------- RESULTS ----------
elif state == "show_results":
    # Show waiting message and current score/rank
    players = players_ref.get() or {}
    score = players.get(pseudo, 0)
    total_players = len(players)
    # Determine rank of this player
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    rank = None
    for i, (name, pts) in enumerate(sorted_players):
        if name == pseudo:
            rank = i + 1
            break
    st.info("Waiting for next question...")
    st.write(f"Your current score: **{score}** pts")
    if rank is not None:
        st.write(f"Your rank: **{rank}** out of {total_players} players")

# ---------- PODIUM ----------
elif state == "podium":
    st.success("🎉 QUIZ FINISHED! 🎉")
    players = players_ref.get() or {}
    if players:
        score = players.get(pseudo, 0)
        total_players = len(players)
        sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
        rank = None
        for i, (name, pts) in enumerate(sorted_players):
            if name == pseudo:
                rank = i + 1
                break
        st.write(f"Your final score: **{score}** pts")
        if rank is not None:
            st.write(f"You ranked **{rank}** out of {total_players} players")
    st.write("Check the podium on the big screen!")
