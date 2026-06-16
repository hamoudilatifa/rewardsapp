import streamlit as st
from datetime import datetime
import time
import numpy as np
import io
import scipy.io.wavfile as wav
import base64
import json
import os
from mentor import obtenir_reponse_mentor

# Configuration de la page
st.set_page_config(page_title="Le guide des routines", page_icon="⚔️", layout="centered")

# --- CONFIGURATION ---
st.set_page_config(page_title="Le guide des routines", page_icon="⚔️", layout="centered")
PARENT_CODE = "1234"  # Change ce code par celui que tu veux pour les parents

# --- GESTION DE LA BASE DE DONNÉES UTILISATEURS (LOGIN) ---
USERS_FILE = "users_db.json"

def load_users():
    """Charge les identifiants et mots de passe autorisés."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# --- GESTION DE LA SAUVEGARDE DES SCORES (JSON) ---
SAVE_FILE = "save_data.json"

def load_data():
    default_data = {
        "gold": 0,
        "xp": 0,
        "level": 1,
        "completed_quests": [],
        "purchased_rewards": [],
        "owned_reward_ids": [],
        "pending_quests": [],
        "history": []
    }
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in default_data.items():
                    if key not in data:
                        data[key] = val
                return data
        except Exception:
            return default_data
    return default_data

def save_data():
    data_to_save = {
        "gold": st.session_state.gold,
        "xp": st.session_state.xp,
        "level": st.session_state.level,
        "completed_quests": list(st.session_state.completed_quests),
        "purchased_rewards": st.session_state.purchased_rewards,
        "owned_reward_ids": list(st.session_state.owned_reward_ids),
        "pending_quests": st.session_state.pending_quests, # <--- Sauvegarde de la liste
        "history": st.session_state.history
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# --- INITIALISATION DE L'ÉTAT DE CONNEXION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- DIALOGUE VALIDATION PARENTALE ---
@st.dialog("🛡️ Validation du Maître du donjon")
def confirm_quest_with_parent(quest_id, gold_reward, xp_reward):
    st.write(f"Une mission a été accomplie ! Un parent doit entrer le code pour valider.")
    code = st.text_input("Code Parent :", type="password")
    if st.button("Confirmer la validation"):
        if code == PARENT_CODE:
                    # La quête est validée, on met à jour les scores
                    st.session_state.completed_quests.add(quest_id)
                    st.session_state.gold += gold_reward
                    st.session_state.xp += xp_reward
                    
                    # On retire la quête de la liste des attentes si elle y était
                    st.session_state.pending_quests = [q for q in st.session_state.pending_quests if q['id'] != quest_id]
                    
                    save_data()
                    st.success("✅ Quête validée ! Le trésor a été ajouté.")
                    time.sleep(1)
                    st.rerun()
        else:
            st.error("❌ Code incorrect !")
            
# --- PERSONNALISATION VISUELLE (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #FDFBF7; }
    h1 { color: #FF6B6B !important; font-family: 'Comic Sans MS', cursive, sans-serif; text-align: center; }
    h2, h3 { color: #4D96FF !important; font-family: 'Comic Sans MS', cursive, sans-serif; }
    div.stButton > button {
        background-color: #4D96FF; color: white; border-radius: 20px;
        border: none; padding: 10px 20px; font-weight: bold; transition: all 0.3s ease;
    }
    div.stButton > button:hover { background-color: #FF6B6B; color: white; transform: scale(1.05); }
    
    .login-box {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05); border: 2px solid #4D96FF;
        margin-top: 20px;
    }
    .date-text { color: #7F8C8D; font-size: 14px; font-weight: bold; text-align: center; margin-bottom: 15px; }
    .timer-text { font-size: 48px; font-weight: bold; color: #FF6B6B; text-align: center; font-family: monospace; }
    .alarm-box {
        background-color: #FF6B6B; color: white; padding: 20px; 
        border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold;
        margin-bottom: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- ÉCRAN DE CONNEXION (SI PAS CONNECTÉ) ---
if not st.session_state.logged_in:
    # Affichage de l'image d'accueil
   # st.image("accueil.png", use_container_width=True)
    
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        # On rend le texte plus doux et adressé à elle
        st.subheader("🔑 Bonjour aventurière !")
        st.write("Veuillez entrer le code secret pour débloquer tes quêtes.")
        
        input_user = st.text_input("Ton nom :").strip().lower()
        input_password = st.text_input("Ton code magique :", type="password")
        
        st.write("")
        if st.button("Entrer dans le royaume 🚀", use_container_width=True):
            users_db = load_users()
            
            if input_user in users_db and users_db[input_user] == input_password:
                st.session_state.logged_in = True
                st.session_state.username = input_user
                st.rerun()
            else:
                st.error("❌ Oups ! Ce n'est pas le bon code. Réessaye !")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# --- SI CONNECTÉ : CHARGEMENT DU JEU ---
saved_data = load_data()
if "history" not in st.session_state:     st.session_state.history = saved_data.get("history", [])
if "pending_quests" not in st.session_state: st.session_state.pending_quests = saved_data["pending_quests"]
if "gold" not in st.session_state: st.session_state.gold = saved_data["gold"]
if "xp" not in st.session_state: st.session_state.xp = saved_data["xp"]
if "level" not in st.session_state: st.session_state.level = saved_data["level"]
if "completed_quests" not in st.session_state: st.session_state.completed_quests = set(saved_data["completed_quests"])
if "purchased_rewards" not in st.session_state: st.session_state.purchased_rewards = saved_data["purchased_rewards"]
if "owned_reward_ids" not in st.session_state: st.session_state.owned_reward_ids = set(saved_data["owned_reward_ids"])
if "just_leveled_up" not in st.session_state: st.session_state.just_leveled_up = False
if "active_timer" not in st.session_state: st.session_state.active_timer = None
if "timer_duration" not in st.session_state: st.session_state.timer_duration = 0
if "alarm_ringing" not in st.session_state: st.session_state.alarm_ringing = False

REWARDS_LIST = [
    {"id": "screen_15", "text": "📱 15 minutes de tablette", "cost": 20, "duration": 15 * 60}, 
    {"id": "screen_30", "text": "🎮 30 minutes de jeux", "cost": 35, "duration": 30 * 60},     
    {"id": "dinner_choice", "text": "🍕 Choisir le bon souper", "cost": 50, "duration": 0},
    {"id": "bedtime_delay", "text": "⏰ Bonus : +20 min avant le dodo", "cost": 40, "duration": 20 * 60}, 
]

# --- GÉNÉRATEUR AUDIO ---
def get_alarm_base64():
    sample_rate = 44100
    duration = 1.5
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * 900 * t)
    pulse = (np.sin(2 * np.pi * 6 * t) > 0).astype(int)
    audio_data = (wave * pulse * 32767).astype(np.int16)
    byte_io = io.BytesIO()
    wav.write(byte_io, sample_rate, audio_data)
    b64 = base64.b64encode(byte_io.getvalue()).decode()
    return b64

# --- SYSTÈME DYNAMIQUES DE NIVEAUX ---
xp_per_level = 100
current_level = max(1, (st.session_state.xp // xp_per_level) + 1)

if current_level > st.session_state.level:
    st.session_state.level = current_level
    st.session_state.just_leveled_up = True
elif current_level < st.session_state.level:
    st.session_state.level = current_level
    st.toast("📉 Oups ! Retour au niveau précédent.", icon="⚔️")
    save_data()

if st.session_state.just_leveled_up:
    st.balloons()
    st.toast("🎉 LEVEL UP !", icon="🔥")
    st.session_state.just_leveled_up = False
    save_data()


# --- SOMMAIRE / NAVIGATION (Sidebar) ---
st.sidebar.image("https://images.unsplash.com/photo-1599733589046-10c005739ef9?auto=format&fit=crop&w=150&q=80", use_container_width=True)
st.sidebar.title("🏰 Sommaire")

# --- DATE ET HEURE ---
jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

maintenant = datetime.now()
nom_jour = jours[maintenant.weekday()]
num_jour = maintenant.day
nom_mois = mois[maintenant.month - 1]
annee = maintenant.year
heure = maintenant.strftime("%H:%M")

st.sidebar.markdown(f"<div class='date-text'>📅 {nom_jour}, {num_jour} {nom_mois} {annee}<br>⏰ {heure}</div>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Où veux-tu aller ?",
    ["📜 Tableau des quêtes", "🏪 Boutique magique", "🎒 Mon sac à trésors" ,"💬 Mentor"]
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"👤 **Aventurèr(e) :** {st.session_state.username.capitalize()}")
st.sidebar.markdown(f"### 🛡️ Niveau {st.session_state.level}")
st.sidebar.markdown(f"💰 **Or :** {st.session_state.gold} PO")
st.sidebar.markdown(f"✨ **XP :** {st.session_state.xp % xp_per_level} / {xp_per_level}")

if st.sidebar.button("🚪 Déconnexion"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


st.sidebar.markdown("---")
with st.sidebar.expander("🛡️ Espace Maître du donjon"):
    parent_code = st.text_input("Code Parent", type="password")
    
    if parent_code == PARENT_CODE:
        # --- SECTION : QUÊTES EN ATTENTE ---
        st.subheader("⚔️ À valider")
        if not st.session_state.pending_quests:
            st.info("Aucune mission en attente.")
        else:
            for i, q in enumerate(st.session_state.pending_quests):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{q['text']}**")
                with col2:
                    # Bouton Validation
                    if st.button("✅", key=f"val_{i}"):
                        st.session_state.gold += q['gold']
                        st.session_state.xp += q['xp']
                        st.session_state.completed_quests.add(q['id'])
                        # Génération du message par le LLM
                        contexte = f"Niveau {st.session_state.level}, Or: {st.session_state.gold}"
                        message = obtenir_reponse_mentor(contexte, f"Félicite l'enfant pour avoir accompli : {q['text']}")
                        st.session_state.last_message = message # On le stocke pour l'afficher
                       
                        # Ajout à l'historique
                        st.session_state.history.append({"text": q['text'], "date": datetime.now().strftime("%d/%m %H:%M")})
                        
                        st.session_state.pending_quests.pop(i)
                        save_data()
                        st.rerun()
                    
                    # Bouton Refus (suppression de la liste attente)
                    if st.button("❌", key=f"ref_{i}"):
                        st.session_state.pending_quests.pop(i)
                        save_data()
                        st.toast("Mission refusée. L'enfant peut réessayer.")
                        st.rerun()

        # --- SECTION : HISTORIQUE ---
        st.markdown("---")
        st.subheader("📜 Historique")
        if not st.session_state.history:
            st.write("Pas encore d'historique.")
        else:
            # On affiche les 5 dernières
            for h in st.session_state.history[-5:]:
                st.write(f"✓ {h['text']} ({h['date']})")
                    

# --- CONTENU DYNAMIQUE ---

if page == "📜 Tableau des quêtes":
    st.title("📜 Quêtes du jour")
    
    # --- AFFICHAGE DU MESSAGE DU MENTOR ---
    # On vérifie si un message est en attente
    if "last_message" in st.session_state and st.session_state.last_message:
        st.success(f"✨ **Message du Mentor :**\n\n{st.session_state.last_message}")
        
        # Petit bouton pour "fermer" le message une fois lu
        if st.button("Lu ! 🛡️"):
            st.session_state.last_message = None
            st.rerun()
            
    affordable_rewards = [
        r for r in REWARDS_LIST 
        if st.session_state.gold >= r["cost"] and r["id"] not in st.session_state.owned_reward_ids
    ]
    if affordable_rewards:
        st.success(f"✨ **Bravo ! Tu as assez d'or pour débloquer une récompense !** Va vite faire un tour à la **🏪 Boutique Magique** pour dépenser tes pièces ! 🛍️")
    
    xp_restant = st.session_state.xp % xp_per_level
    progress_percentage = min(xp_restant / xp_per_level, 1.0)
    st.progress(progress_percentage, text=f"✨ XP : {xp_restant} / {xp_per_level} avant le niveau {st.session_state.level + 1}")
    st.write("")

    quests = [
        {"id": "lit", "text": "🛏️ Faire son lit douillet", "gold": 10, "xp": 20},
        {"id": "dents_matin", "text": "🪥 Dents étincelantes (Matin)", "gold": 5, "xp": 15},
        {"id": "devoirs", "text": "📚 Super devoirs", "gold": 25, "xp": 50},
        {"id": "rangement", "text": "🧸 Mission : Ranger la chambre", "gold": 15, "xp": 30},
        {"id": "dents_soir", "text": "🪥 Dents étincelantes (Soir)", "gold": 5, "xp": 15}
    ]

    def complete_quest(quest_id, gold_reward, xp_reward):
        if quest_id not in st.session_state.completed_quests:
            st.session_state.completed_quests.add(quest_id)
            st.session_state.gold += gold_reward
            st.session_state.xp += xp_reward
            save_data()

    def cancel_quest(quest_id, gold_reward, xp_reward):
        if quest_id in st.session_state.completed_quests:
            st.session_state.completed_quests.remove(quest_id)
            st.session_state.gold = max(0, st.session_state.gold - gold_reward)
            st.session_state.xp = max(0, st.session_state.xp - xp_reward)
            save_data()
            st.toast("↩️ Tâche annulée, score corrigé !", icon="🧹")

        # Fonction pour envoyer en validation
    def request_validation(quest_id, text, gold, xp):
        # On ajoute à la liste d'attente
        st.session_state.pending_quests.append({
            "id": quest_id, "text": text, "gold": gold, "xp": xp
        })
        save_data()
        
    for q in quests:
        is_done = q["id"] in st.session_state.completed_quests
        is_pending = any(pq['id'] == q['id'] for pq in st.session_state.pending_quests)
        
        col_q, col_btn = st.columns([3, 1])
        
        with col_q:
            if is_done: st.markdown(f"🌈 ~~{q['text']}~~ *(Bravo !)*")
            elif is_pending: st.markdown(f"⏳ **{q['text']}** *(En attente...)*")
            else: st.markdown(f"🌟 **{q['text']}**\n*(💰 +{q['gold']} Or | ✨ +{q['xp']} XP)*")
                
        with col_btn:
            if not is_done and not is_pending:
                    st.button("Valider ⚔️", key=f"btn_{q['id']}", on_click=request_validation, args=(q["id"], q["text"], q["gold"], q["xp"]))


    st.markdown("---")
    if st.button("🔄 Nouvelle Journée"):
        st.session_state.completed_quests = set()
        save_data()
        st.rerun()

elif page == "🏪 Boutique magique":
    st.title("🏪 La Boutique magique")
    
    # Dans l'affichage de la Boutique, ajoute ceci :
    if "last_reward_msg" in st.session_state:
        st.info(f"✨ {st.session_state.last_reward_msg}")
    if st.button("J'ai compris !"):
        del st.session_state.last_reward_msg
        
    st.write(f"Tu as actuellement : 💰 **{st.session_state.gold} Pièces d'Or**")
    
    def buy_reward(reward_id, cost, reward_text, duration):
        if st.session_state.gold >= cost and reward_id not in st.session_state.owned_reward_ids:
            st.session_state.gold -= cost
            st.session_state.purchased_rewards.append({"id": reward_id, "text": reward_text, "duration": duration})
            st.session_state.owned_reward_ids.add(reward_id)
            save_data()
            st.toast(f"🛍️ Débloqué : {reward_text} !", icon="🎉")
            
            # Appel LLM pour scénariser l'achat
            contexte = f"Récompense achetée : {reward_text}"
            message_magique = obtenir_reponse_mentor(contexte, "Donne une petite aventure épique liée à cette récompense.")
            
            st.session_state.last_reward_msg = message_magique
            save_data()
            st.rerun()
    for r in REWARDS_LIST:
        col_r, col_buy = st.columns([3, 1])
        is_already_bought = r["id"] in st.session_state.owned_reward_ids
        can_afford = st.session_state.gold >= r["cost"]
        
        with col_r: 
            if is_already_bought:
                st.markdown(f"🔒 ~~**{r['text']}**~~ *(Déjà dans ton sac !)*")
            else:
                st.markdown(f"🎁 **{r['text']}**\n*(Prix : 💰 {r['cost']} Or)*")
                
        with col_buy:
            if is_already_bought:
                st.button("Acheté !", key=f"buy_{r['id']}", disabled=True)
            else:
                st.button("Débloquer", key=f"buy_{r['id']}", disabled=not can_afford, on_click=buy_reward, args=(r["id"], r["cost"], r["text"], r["duration"]))

elif page == "🎒 Mon sac à trésors":
    st.title("🎒 Ton sac à trésors")
    
    if st.session_state.alarm_ringing:
        st.markdown("<div class='alarm-box'>🚨 ÉCOULEMENT DU TEMPS !<br>L'écran doit être éteint ! 🚨</div>", unsafe_allow_html=True)
        
        audio_b64 = get_alarm_base64()
        html_invisible_audio = f"""
        <audio autoplay loop style="display:none;">
            <source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">
        </audio>
        """
        st.components.v1.html(html_invisible_audio, height=0)
        st.warning("⚠️ Temps écoulé ! Donne immédiatement la tablette à un parent.")
        
        st.write("")
        if st.button("🔕 Éteindre et Valider (Papa/Maman)", use_container_width=True):
            st.session_state.alarm_ringing = False
            st.session_state.active_timer = None
            st.session_state.timer_duration = 0
            save_data()
            st.rerun()
        st.stop()

    if st.session_state.active_timer and not st.session_state.alarm_ringing:
        st.warning(f"⏳ Temps en cours pour : **{st.session_state.active_timer}**")
        countdown_placeholder = st.empty()
        
        for t in range(st.session_state.timer_duration, -1, -1):
            mins, secs = divmod(t, 60)
            countdown_placeholder.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
            time.sleep(1)
        
        st.session_state.alarm_ringing = True
        st.rerun()

    st.write("Voici tes récompenses en réserve. Tu peux en utiliser une seule à la fois !")
    st.write("")

    if st.session_state.purchased_rewards:
        
        def use_single_reward(index_to_remove, reward_id):
            reward_item = st.session_state.purchased_rewards.pop(index_to_remove)
            if reward_id in st.session_state.owned_reward_ids:
                st.session_state.owned_reward_ids.remove(reward_id)
            save_data()
            
            if reward_item["duration"] > 0:
                st.session_state.active_timer = reward_item["text"]
                st.session_state.timer_duration = reward_item["duration"]
            else:
                st.toast(f"🔥 Privilège activé : {reward_item['text']} !", icon="🎰")

        for index, item in enumerate(st.session_state.purchased_rewards):
            col_item, col_use = st.columns([3, 1])
            with col_item:
                st.markdown(f"⭐ **{item['text']}**")
            with col_use:
                st.button("Utiliser 🌟", key=f"use_{index}", on_click=use_single_reward, args=(index, item["id"]))
    else:
        st.info("Ton sac à trésor est vide pour l'instant. 🪙")

elif page == "💬 Mentor":
    st.title("💬 Discussion avec le Mentor")
    
    # Initialisation de l'historique de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage des messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Entrée utilisateur
    if prompt := st.chat_input("Pose une question au Mentor..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Appel LLM
        with st.chat_message("assistant"):
            contexte = f"Niveau {st.session_state.level}, Or: {st.session_state.gold}"
            reponse = obtenir_reponse_mentor(contexte, prompt)
            st.markdown(reponse)
        st.session_state.messages.append({"role": "assistant", "content": reponse})