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

# Screenshot ke hisaab se credentials
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
# Hostname screenshot mein "instagram-scraper-stable" dikh raha hai
RAPID_API_HOST = "instagram-scraper-stable.p.rapidapi.com"

@app.get("/")
def home():
    return {"status": "online", "message": "Backend is running with Scraper API!"}

@app.post("/analyze")
async def get_personality(request: AnalyzeRequest):
    # Screenshot ke mutabiq sahi endpoint: /v1/info
    insta_url = f"https://{RAPID_API_HOST}/v1/info"
    
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": RAPID_API_HOST
    }

    try:
        # Screenshot mein parameter ka naam 'username_or_url' dikh raha hai
        params = {"username_or_id_or_url": request.username} 
        
        insta_res = requests.get(insta_url, headers=headers, params=params)
        
        if insta_res.status_code != 200:
            raise HTTPException(status_code=insta_res.status_code, detail="Instagram Profile Not Found")

        data = insta_res.json().get("data", {}) # Is API mein data key ke andar info hoti hai
        
        # Profile details nikalna
        full_name = data.get("full_name", "User")
        bio = data.get("biography", "No bio available")
        profile_pic = data.get("profile_pic_url")
        followers = data.get("follower_count", 0)

        # AI Analysis (OpenRouter)
        openai.api_key = OPENROUTER_API_KEY
        openai.api_base = "https://openrouter.ai/api/v1"

        prompt = f"Analyze the Instagram vibe of {full_name} (@{request.username}). Bio: {bio}. Followers: {followers}. Give a funny 3-point summary."

        ai_res = openai.ChatCompletion.create(
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "success": True,
            "data": {
                "name": full_name,
                "username": request.username,
                "profile_pic": profile_pic,
                "followers": followers,
                "personality_report": ai_res.choices[0].message.content
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"success": False, "error": "API Error: Please check if the username is public."}

