import streamlit as st
import json
import random
import time
from firebase import game_ref, players_ref, answers_ref, timer_ref, stats_ref
from components import header, sub

st.set_page_config(page_title="Mini-Kahoot - Teacher", layout="wide")

# Chargement des questions
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

header("👨‍🏫 Mini-Kahoot — Teacher Mode")

# Récupérer les données de la partie en cours
game_snapshot = game_ref.get()
game = game_snapshot.val() if game_snapshot and game_snapshot.val() else None

# Si aucune partie n'existe, proposer d'en créer une
if not game:
    st.warning("Aucune partie active. Cliquez sur 'Create new game' pour démarrer.")
    if st.button("Create new game"):
        # Générer un PIN aléatoire et initialiser la partie
        pin = random.randint(100000, 999999)
        game_data = {
            "pin": pin,
            "current": -1,
            "state": "waiting",
            "total": len(QUESTIONS)
        }
        game_ref.set(game_data)
        players_ref.set({})     # Réinitialiser la liste des joueurs
        answers_ref.set({})     # Réinitialiser les réponses
        stats_ref.set({})       # Réinitialiser les statistiques
        timer_ref.set({"time_left": 20})  # Initialiser le timer (20 sec)
        game = game_data  # Mettre à jour localement la variable game
    else:
        st.stop()  # Arrêter le script tant qu'aucune partie n'est créée

# Afficher le PIN de la partie active
st.subheader(f"Game PIN: **{game.get('pin', '???')}**")

# Récupérer les joueurs connectés et leurs scores actuels
players_snapshot = players_ref.get()
players = players_snapshot.val() if players_snapshot and players_snapshot.val() else {}

# Extraire l'état actuel de la partie et l'index de la question courante
state = game.get("state", "waiting")
current = game.get("current", -1)

# ---------- LOBBY (Attente des joueurs) ----------
if state == "waiting":
    header("Waiting for players…")
    st.write("Connected players:")
    data = []
    for name, score in players.items():
        if isinstance(score, (int, float)):
            data.append({"Player": name, "Score": score})
    if data:
        st.table(data)
    else:
        st.write("*(Aucun joueur connecté pour l'instant)*")
    # Bouton pour démarrer le jeu une fois les joueurs prêts
    if st.button("Start game ▶️"):
        game_ref.update({"state": "in_question", "current": 0})
        timer_ref.set({"time_left": 20})

# ---------- QUESTION EN COURS ----------
elif state == "in_question":
    if current >= len(QUESTIONS):
        st.error("Numéro de question invalide.")
        st.stop()
    q = QUESTIONS[current]
    header(f"Question {current+1}/{game['total']}")
    sub(q["question"])

    # Afficher les choix (QCM) ou les listes à apparier
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

    # Afficher le timer et la barre de progression
    timer_snapshot = timer_ref.get()
    timer_data = timer_snapshot.val() if timer_snapshot else {}
    time_left = timer_data.get("time_left", 0)
    st.progress(time_left / 20)
    st.write(f"⏳ Time left: **{time_left} sec**")

    # Bouton pour arrêter les réponses et afficher les résultats
    if st.button("Stop answers ⏹"):
        game_ref.update({"state": "show_results"})

# ---------- AFFICHAGE DES RÉSULTATS ----------
elif state == "show_results":
    header("📊 Results")
    q = QUESTIONS[current]
    sub(q["question"])

    # Récupérer les réponses soumises par les joueurs pour cette question
    answers_snapshot = answers_ref.child(str(current)).get()
    answers = answers_snapshot.val() if answers_snapshot else {}
    total_players = len(players)
    responded = len(answers)

    if q["type"] == "mcq":
        # Calculer le nombre de réponses pour chaque choix
        stats = {choice: 0 for choice in q["choices"]}
        for pseudo, ans in answers.items():
            stats[ans] = stats.get(ans, 0) + 1
        correct_text = q["choices"][q["answer"]]
        correct_count = stats.get(correct_text, 0)
        st.write(f"**Correct answer:** {correct_text}")
        st.write(f"**Answered correctly:** {correct_count} / {total_players} players")
        st.write(f"**Responses received:** {responded} / {total_players} players")
        st.bar_chart(stats)
    elif q["type"] == "match":
        # Compter les correspondances proposées par les joueurs
        stats = {f"{l} → {r}": 0 for l in q["left"] for r in q["right"]}
        for pseudo, pair in answers.items():
            key = f"{q['left'][pair['left']]} → {q['right'][pair['right']]}"
            stats[key] += 1
        correct_pairs = q["correct_pair"]
        if not isinstance(correct_pairs[0], list):
            correct_pairs = [correct_pairs]
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
        st.bar_chart(stats)
    else:
        st.warning("Unknown question type.")

    # Afficher le classement actuel
    st.subheader("Current ranking:")
    sorted_list = sorted(players.items(), key=lambda x: x[1], reverse=True)
    ranking_data = [{"Player": name, "Score": pts} for name, pts in sorted_list]
    st.table(ranking_data)

    # Bouton pour passer à la question suivante ou afficher le podium final
    if current < game["total"] - 1:
        if st.button("Next question ➔"):
            game_ref.update({"state": "in_question", "current": current + 1})
            timer_ref.set({"time_left": 20})
    else:
        if st.button("Show podium 🏆"):
            game_ref.update({"state": "podium"})

# ---------- PODIUM FINAL ----------
elif state == "podium":
    header("🏆 FINAL PODIUM 🏆")
    sorted_players = sorted(players.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_players) == 0:
        st.write("No players to display.")
    else:
        st.markdown(f"🥇 **1st: {sorted_players[0][0]}** — {sorted_players[0][1]} pts")
        if len(sorted_players) > 1:
            st.markdown(f"🥈 **2nd: {sorted_players[1][0]}** — {sorted_players[1][1]} pts")
        if len(sorted_players) > 2:
            st.markdown(f"🥉 **3rd: {sorted_players[2][0]}** — {sorted_players[2][1]} pts")
    st.balloons()
