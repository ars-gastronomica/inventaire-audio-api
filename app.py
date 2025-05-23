import openai
import pandas as pd
import tempfile
import os
import json
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uvicorn

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.post("/process")
async def process_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        fichier_audio = temp_audio.name
        temp_audio.write(await file.read())
        temp_audio.flush()

    with open(fichier_audio, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    texte = transcript["text"]

    prompt = (
        "Voici une transcription vocale d'inventaire :\n" +
        texte +
        "\nFournis-moi un tableau structuré en JSON avec les champs : Lieu, Emplacement, Produit, Référence, "
        "Quantité brute, Quantité estimée, Note. Une ligne par produit. "
        "Indique 'Non précisé' si une info est manquante. "
        "La réponse doit être un tableau JSON directement exploitable (sans texte autour)."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    json_response = response["choices"][0]["message"]["content"]
    if json_response.startswith("```json"):
        json_response = json_response.strip("```json\n").strip("```")
    donnees = json.loads(json_response)

    df = pd.DataFrame(donnees)
    temp_xlsx = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    df.to_excel(temp_xlsx.name, index=False)

    return FileResponse(temp_xlsx.name, filename="inventaire.xlsx")
