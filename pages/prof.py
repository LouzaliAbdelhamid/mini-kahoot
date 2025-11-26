import streamlit as st
import json
import time
from firebase import game_ref, players_ref, answers_ref, timer_ref, stats_ref
from components import header, sub

st.set_page_config(page_title="Mini-Kahoot - Teacher", layout="wide")

# Load questions
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

header("👨‍🏫 Mini-Kahoot — Teacher Mode")

# ---------- CREATE NEW GAME ----------
if st.button("Create new game"):
    import random
    pin = random.randint(100000, 999999)
    # Initialize game data
    game_ref.set({
        "pin": pin,
        "current": -1,
        "state": "waiting",  # possible states: waiting / in_question / show_results / podium
        "total": len(QUESTIONS)
    })
    players_ref.set({})
    answers_ref.set({})
    stats_ref.set({})
    timer_ref.set({"time_left": 20})

game = game_ref.get()
if not game:
    st.warning("Aucune partie active. Clique sur 'Create new game' pour démarrer.")
    st.stop()

players = players_ref.get() or {}
st.subheader(f"Game PIN: **{game.get('pin', '???')}**")

state = game["state"]
current = game["current"]

# ---------- LOBBY ----------
if state == "waiting":
    header("Waiting for players…")
    st.write("Connected players:")
    if players:
        data = [{"Player": name, "Score": pts} for name, pts in players.items()]
        st.table(data)
    else:
        st.write("*(No players yet)*")
    if st.button("Start game ▶️"):
        game_ref.update({"state": "in_question", "current": 0})
        timer_ref.set({"time_left": 20})

# ---------- QUESTION ----------
elif state == "in_question":
    q = QUESTIONS[current]
    header(f"Question {current+1}/{game['total']}")
    sub(q["question"])

    if q["type"] == "mcq":
        # Display choices
        for c in q["choices"]:
            st.write(f"- {c}")
    elif q["type"] == "match":
        left, right = q["left"], q["right"]
        st.write("**Left:**")
        for s in left:
            st.write(f"- {s}")
        st.write("**Right:**")
        for s in right:
            st.write(f"- {s}")

    # Timer display (progress bar)
    timer_data = timer_ref.get()
    time_left = timer_data["time_left"]
    st.progress(time_left / 20)
    st.write(f"⏳ Time left: **{time_left} sec**")

    if st.button("Stop answers ⏹"):
        game_ref.update({"state": "show_results"})

# ---------- RESULTS ----------
elif state == "show_results":
    header("📊 Results")
    q = QUESTIONS[current]
    # Show question text and correct answer
    sub(q["question"])
    answers = answers_ref.child(str(current)).get() or {}
    total_players = len(players)
    responded = len(answers)

    if q["type"] == "mcq":
        # Calculate answer counts
        stats = {choice: 0 for choice in q["choices"]}
        for pseudo, ans in answers.items():
            stats[ans] += 1
        correct_text = q["choices"][q["answer"]]
        correct_count = stats.get(correct_text, 0)
        st.write(f"**Correct answer:** {correct_text}")
        st.write(f"**Answered correctly:** {correct_count} / {total_players} players")
        st.write(f"**Responses received:** {responded} / {total_players} players")
    elif q["type"] == "match":
        # Calculate answer counts for each possible pair
        stats = {}
        for l in q["left"]:
            for r in q["right"]:
                stats[f"{l} → {r}"] = 0
        for pseudo, pair in answers.items():
            key = f"{q['left'][pair['left']]} → {q['right'][pair['right']]}"
            stats[key] += 1
        # Determine correct match pair(s)
        correct_pairs = q["correct_pair"]
        if not isinstance(correct_pairs[0], list):
            correct_pairs = [correct_pairs]
        # Display correct matches
        if len(correct_pairs) > 1:
            st.write("**Correct matches:**")
            correct_texts = []
            for pair in correct_pairs:
                l_idx, r_idx = pair
                text = f"{q['left'][l_idx]} → {q['right'][r_idx]}"
                correct_texts.append(text)
                st.write(f"- {text}")
            correct_count = sum(stats.get(text, 0) for text in correct_texts)
        else:
            l_idx, r_idx = correct_pairs[0]
            correct_text = f"{q['left'][l_idx]} → {q['right'][r_idx]}"
            st.write(f"**Correct match:** {correct_text}")
            correct_count = stats.get(correct_text, 0)
        st.write(f"**Answered correctly:** {correct_count} / {total_players} players")
        st.write(f"**Responses received:** {responded} / {total_players} players")
        # stats chart (match combos)
        st.bar_chart(stats)
    else:
        # Unexpected question type
        st.warning("Unknown question type.")
        stats = {}
    # Display bar chart for answers (for MCQ, after computing stats)
    if q["type"] == "mcq":
        st.bar_chart(stats)

    st.subheader("Current ranking:")
    # Display ranking sorted by score
    sorted_list = sorted(players.items(), key=lambda x: x[1], reverse=True)
    ranking_data = [{"Player": name, "Score": pts} for name, pts in sorted_list]
    st.table(ranking_data)

    # Next question or finish game
    if current < game["total"] - 1:
        if st.button("Next question ➡️"):
            game_ref.update({"state": "in_question", "current": current + 1})
            timer_ref.set({"time_left": 20})
    else:
        if st.button("Show podium 🏆"):
            game_ref.update({"state": "podium"})

# ---------- PODIUM ----------
elif state == "podium":
    header("🏆 FINAL PODIUM 🏆")
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_players) == 0:
        st.write("No players to display.")
    else:
        # Display top 3 winners
        st.markdown(f"🥇 **1st: {sorted_players[0][0]}** — {sorted_players[0][1]} pts")
        if len(sorted_players) > 1:
            st.markdown(f"🥈 **2nd: {sorted_players[1][0]}** — {sorted_players[1][1]} pts")
        if len(sorted_players) > 2:
            st.markdown(f"🥉 **3rd: {sorted_players[2][0]}** — {sorted_players[2][1]} pts")
    st.balloons()
