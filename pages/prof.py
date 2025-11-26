import streamlit as st
import json
import random
from firebase import game_ref, players_ref, answers_ref, timer_ref, stats_ref
from components import header, sub

st.set_page_config(page_title="Mini-Kahoot - Teacher", layout="wide")

# Chargement des questions
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

header("👨‍🏫 Mini-Kahoot — Teacher Mode")

# Créer une nouvelle partie si demandé
if st.button("Create new game"):
    # Permettre au prof de saisir un PIN personnalisé
    manual_pin = st.text_input("Enter custom PIN (or leave blank for random):", "")
    if manual_pin.isdigit() and len(manual_pin) == 6:
        pin = int(manual_pin)
    else:
        pin = random.randint(100000, 999999)

    game_data = {
        "pin": pin,
        "current": -1,
        "state": "waiting",
        "total": len(QUESTIONS)
    }
    game_ref.set(game_data)
    players_ref.set({})
    answers_ref.set({})
    stats_ref.set({})
    timer_ref.set({"time_left": 20})
    st.success(f"🎉 Game created with PIN: {pin}")
    st.stop()  # Recharge proprement

# Récupérer les données de la partie en cours
game_snapshot = game_ref.get()
game = game_snapshot.val() if game_snapshot and game_snapshot.val() else None

if not game:
    st.warning("Aucune partie active. Cliquez sur 'Create new game' pour démarrer.")
    st.stop()

# Affichage du PIN de la partie
st.subheader(f"Game PIN: **{game.get('pin', '???')}**")

# Récupérer les joueurs connectés
players_snapshot = players_ref.get()
players = players_snapshot.val() if players_snapshot and players_snapshot.val() else {}

state = game.get("state", "waiting")
current = game.get("current", -1)

# ---------- LOBBY ----------
if state == "waiting":
    header("Waiting for players…")
    st.write("Connected players:")
    data = [{"Player": name, "Score": score} for name, score in players.items() if isinstance(score, (int, float))]
    st.table(data) if data else st.write("*(Aucun joueur connecté pour l'instant)*")
    if st.button("Start game ▶️"):
        game_ref.update({"state": "in_question", "current": 0})
        timer_ref.set({"time_left": 20})

# ---------- QUESTION ----------
elif state == "in_question":
    if current >= len(QUESTIONS):
        st.error("Numéro de question invalide.")
        st.stop()
    q = QUESTIONS[current]
    header(f"Question {current+1}/{game['total']}")
    sub(q["question"])

    if q["type"] == "mcq":
        for c in q["choices"]:
            st.write(f"- {c}")
    elif q["type"] == "match":
        st.write("**Left:**")
        for s in q["left"]:
            st.write(f"- {s}")
        st.write("**Right:**")
        for s in q["right"]:
            st.write(f"- {s}")

    timer_snapshot = timer_ref.get()
    timer_data = timer_snapshot.val() if timer_snapshot else {}
    time_left = timer_data.get("time_left", 0)
    st.progress(time_left / 20)
    st.write(f"⏳ Time left: **{time_left} sec**")

    if st.button("Stop answers ⏹"):
        game_ref.update({"state": "show_results"})

# ---------- RESULTS ----------
elif state == "show_results":
    header("📊 Results")
    q = QUESTIONS[current]
    sub(q["question"])

    answers_snapshot = answers_ref.child(str(current)).get()
    answers = answers_snapshot.val() if answers_snapshot else {}
    total_players = len(players)
    responded = len(answers)

    if q["type"] == "mcq":
        stats = {choice: 0 for choice in q["choices"]}
        for ans in answers.values():
            stats[ans] = stats.get(ans, 0) + 1
        correct_text = q["choices"][q["answer"]]
        correct_count = stats.get(correct_text, 0)
        st.write(f"**Correct answer:** {correct_text}")
        st.write(f"**Answered correctly:** {correct_count} / {total_players}")
        st.write(f"**Responses received:** {responded} / {total_players}")
        st.bar_chart(stats)

    elif q["type"] == "match":
        stats = {f"{l} → {r}": 0 for l in q["left"] for r in q["right"]}
        for pair in answers.values():
            key = f"{q['left'][pair['left']]} → {q['right'][pair['right']]}"
            stats[key] += 1
        correct_pairs = q["correct_pair"]
        if not isinstance(correct_pairs[0], list):
            correct_pairs = [correct_pairs]
        correct_texts = [f"{q['left'][l]} → {q['right'][r]}" for l, r in correct_pairs]
        correct_count = sum(stats.get(text, 0) for text in correct_texts)
        st.write("**Correct match(es):**")
        for text in correct_texts:
            st.write(f"- {text}")
        st.write(f"**Answered correctly:** {correct_count} / {total_players}")
        st.write(f"**Responses received:** {responded} / {total_players}")
        st.bar_chart(stats)

    st.subheader("Current ranking:")
    sorted_list = sorted(players.items(), key=lambda x: x[1], reverse=True)
    st.table([{"Player": name, "Score": pts} for name, pts in sorted_list])

    if current < game["total"] - 1:
        if st.button("Next question ➔"):
            game_ref.update({"state": "in_question", "current": current + 1})
            timer_ref.set({"time_left": 20})
    else:
        if st.button("Show podium 🏆"):
            game_ref.update({"state": "podium"})

# ---------- PODIUM ----------
elif state == "podium":
    header("🏆 FINAL PODIUM 🏆")
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    if sorted_players:
        podium = ["🥇", "🥈", "🥉"]
        for i, (name, score) in enumerate(sorted_players[:3]):
            st.markdown(f"{podium[i]} **{i+1}st: {name}** — {score} pts")
    else:
        st.write("No players to display.")
    st.balloons()
