import streamlit as st
from openai import OpenAI

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

def obtenir_reponse_mentor(contexte, prompt_utilisateur):
    system_prompt = f"""Tu es un Maître de Guilde médiéval fantastique bienveillant. 
    Tu t'adresses à une jeune aventurière. Ton rôle est de :
    1. Féliciter ses accomplissements.
    2. L'aider à s'organiser.
    3. Scénariser ses récompenses.
    Ton contexte actuel est : {contexte}
    Reste court, magique et encourageant."""
    
    # Appel à l'API Groq (via le modèle Llama 3)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_utilisateur}
        ],
        temperature=0.7 # Un peu de créativité pour le côté magique
    )
    
    return response.choices[0].message.content
