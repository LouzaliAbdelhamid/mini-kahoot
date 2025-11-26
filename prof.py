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

    game_ref.set({
        "pin": pin,
        "current": -1,
        "state": "waiting",  # waiting / in_question / show_results / podium
        "total": len(QUESTIONS)
    })

    players_ref.set({})
    answers_ref.set({})
    stats_ref.set({})
    timer_ref.set({"time_left": 20})

game = game_ref.get()
players = players_ref.get() or {}

if not game:
    st.warning("No game active.")
    st.stop()

st.subheader(f"Game PIN: **{game['pin']}**")

state = game["state"]
current = game["current"]

# ---------- LOBBY ----------
if state == "waiting":
    header("Waiting for players…")

    st.write("Connected players:")
    st.table(players)

    if st.button("Start game ▶️"):
        game_ref.update({"state": "in_question", "current": 0})
        timer_ref.set({"time_left": 20})

# ---------- QUESTION ----------
elif state == "in_question":
    q = QUESTIONS[current]

    header(f"Question {current+1}/{game['total']}")
    sub(q["question"])

    if q["type"] == "mcq":
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

    # Timer
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
    answers = answers_ref.child(str(current)).get() or {}

    if q["type"] == "mcq":
        stats = {choice: 0 for choice in q["choices"]}
        for pseudo, ans in answers.items():
            stats[ans] += 1

    elif q["type"] == "match":
        stats = {}
        for l in q["left"]:
            for r in q["right"]:
                stats[f"{l} → {r}"] = 0

        for pseudo, pair in answers.items():
            key = f"{q['left'][pair['left']]} → {q['right'][pair['right']]}"
            stats[key] += 1

    st.bar_chart(stats)

    st.subheader("Current ranking:")
    st.table(players)

    # Next question
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

    try:
        st.markdown(f"🥇 **1st: {sorted_players[0][0]}** — {sorted_players[0][1]} pts")
        st.markdown(f"🥈 **2nd: {sorted_players[1][0]}** — {sorted_players[1][1]} pts")
        st.markdown(f"🥉 **3rd: {sorted_players[2][0]}** — {sorted_players[2][1]} pts")
    except:
        st.write("Not enough players.")

    st.balloons()
