from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import requests
import os
from dotenv import load_dotenv
import uvicorn


# Carrega variáveis de ambiente
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(
    title="Steam Requirements API com IA",
    description="API que fornece requisitos mínimos e recomendados de jogos da Steam e verifica compatibilidade das especificações do usuário com GROQ IA",
    version="1.1"
)

# Carrega o csv
try:
    df = pd.read_csv("dados/steam_requirements_data.csv")
except Exception as e:
    raise RuntimeError(f"Erro ao carregar o dataset: {e}")

# Realizando um pequeno tratamento
if df.columns[0] == "":
    df.drop(columns=df.columns[0], inplace=True)

df["steam_appid"] = pd.to_numeric(df["steam_appid"], errors="coerce")
df.dropna(subset=["steam_appid"], inplace=True)
df["steam_appid"] = df["steam_appid"].astype(int)
df.reset_index(drop=True, inplace=True)
df = df.replace({np.nan: None})
dados = df.to_dict(orient="records")

# Modoldando o corpo das especificações do usuario 
class EspecificacoesUsuario(BaseModel):
    steam_appid: int
    sistema_operacional: str
    processador: str
    memoria_ram_gb: int
    placa_de_video: str
# Função para montar o prompt a ser usado no groq
def montar_prompt(usuario: EspecificacoesUsuario, requisitos_jogo: str) -> str:
    return f"""
O usuário possui um computador com as seguintes especificações:
- Sistema Operacional: {usuario.sistema_operacional}
- Processador: {usuario.processador}
- Memória RAM: {usuario.memoria_ram_gb} GB
- Placa de vídeo: {usuario.placa_de_video}

O jogo com Steam App ID {usuario.steam_appid} possui os seguintes requisitos mínimos:
{requisitos_jogo}

Com base nessas informações, o computador do usuário consegue rodar esse jogo?
Responda apenas com "Sim" ou "Não" e uma breve justificativa.
"""

# Função para consultar a API do groq 
def consultar_groq(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Seção de endpoints

# Endpoint de infos basicas
@app.get("/")
def home():
    return {
        "projeto": "Steam Requirements API com IA",
        "autor": "Erik",
        "descricao": "API que fornece requisitos mínimos e recomendados de jogos da Steam e verifica compatibilidade das especificações do usuário com uso de IA",
        "Data_coleta": "05/01/2019",
        "total_registros": len(dados)
    }

# Endpoint que pega os dados 
@app.get("/dados")
def listar_todos(skip: int = 0, limit: int = 10):
    return dados[skip:skip + limit]

# Endpoint que pega pelo id do jogo
@app.get("/dados/{item_id}")
def buscar_por_id(item_id: int):
    resultado = [item for item in dados if item["steam_appid"] == item_id]
    if resultado:
        return {"item": resultado[0]}
    else:
        return {"erro": f"Nenhum jogo encontrado com steam_appid = {item_id}"}

# Endpoint caso o usuario seja burro
@app.get("/como-encontrar-id")
def instrucoes_para_id():
    return {
        "mensagem": (
            "Para encontrar o Steam App ID de um jogo, acesse o site https://steamdb.info/ "
            "e digite o nome do jogo na barra de pesquisa. Na página do jogo, procure pelo campo 'App ID'."
        )
    }

# Endpoint da verificação das especs com o groq
@app.post("/verificar-especs-ia")
def verificar_especs_ia(usuario: EspecificacoesUsuario):
    jogo = next((item for item in dados if item["steam_appid"] == usuario.steam_appid), None)
    if not jogo:
        return {"erro": "Jogo não encontrado."}

    requisitos = jogo.get("minimum", "Requisitos mínimos não disponíveis.")
    prompt = montar_prompt(usuario, requisitos)
    try:
        resposta = consultar_groq(prompt)
    except Exception as e:
        return {"erro": f"Falha ao consultar IA: {str(e)}"}

    return {
        "jogo_id": usuario.steam_appid,
        "requisitos_minimos": requisitos,
        "resposta_ia": resposta
    }

# rodando localmente
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

#print("Chave carregada:", GROQ_API_KEY)
