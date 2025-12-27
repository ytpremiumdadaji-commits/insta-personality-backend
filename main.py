import os
import requests
import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    username: str

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
RAPID_API_HOST = "instagram-profile-data-api.p.rapidapi.com"

# 1. Yeh naya route hai testing ke liye
@app.get("/")
def home():
    return {"status": "online", "message": "InstaPersona Backend is running!"}

@app.post("/analyze")
async def get_personality(request: AnalyzeRequest):
    insta_url = f"https://{RAPID_API_HOST}/user/info"
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }

    try:
        # Step 1: Instagram Data Fetch
        params = {"username": request.username} 
        insta_res = requests.get(insta_url, headers=headers, params=params)
        
        if insta_res.status_code != 200:
            # Agar Instagram API fail ho jaye
            raise HTTPException(status_code=insta_res.status_code, detail=f"Insta API Error: {insta_res.text}")

        data = insta_res.json()
        
        # Step 2: AI Analysis (OpenRouter)
        openai.api_key = OPENROUTER_API_KEY
        openai.api_base = "https://openrouter.ai/api/v1"

        # Vibe check prompt
        prompt = f"Analyze Instagram personality of {data.get('full_name', 'User')}. Bio: {data.get('biography', 'No bio')}. Give 3 funny traits."

        ai_res = openai.ChatCompletion.create(
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[{"role": "user", "content": prompt}],
            headers={
                "HTTP-Referer": "https://instapersona.vercel.app", # Optional but good
                "X-Title": "InstaPersona AI"
            }
        )

        return {
            "success": True,
            "data": {
                "name": data.get("full_name"),
                "username": request.username,
                "profile_pic": data.get("profile_pic_url"),
                "followers": data.get("follower_count", 0),
                "personality_report": ai_res.choices[0].message.content
            }
        }

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}") 
        return {"success": False, "error": str(e)}

