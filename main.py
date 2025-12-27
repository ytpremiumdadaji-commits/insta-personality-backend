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

@app.get("/")
def health_check():
    return {"status": "success", "message": "Backend is live on separate repo!"}

@app.post("/analyze")
async def get_personality(request: AnalyzeRequest):
    insta_url = f"https://{RAPID_API_HOST}/user/info"
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }
    try:
        insta_res = requests.get(insta_url, headers=headers, params={"username": request.username})
        if insta_res.status_code != 200:
            raise HTTPException(status_code=404, detail="Instagram profile not found")
        data = insta_res.json()
        
        bio = data.get("biography", "No bio available")
        full_name = data.get("full_name", request.username)

        openai.api_key = OPENROUTER_API_KEY
        openai.api_base = "https://openrouter.ai/api/v1"

        prompt = f"Analyze Instagram personality of {full_name} (@{request.username}). Bio: {bio}. Give 3 points."

        ai_res = openai.ChatCompletion.create(
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "success": True,
            "data": {
                "name": full_name,
                "username": request.username,
                "profile_pic": data.get("profile_pic_url"),
                "followers": data.get("follower_count", 0),
                "personality_report": ai_res.choices[0].message.content
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
