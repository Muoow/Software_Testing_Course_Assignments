import os
from dotenv import load_dotenv
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError

load_dotenv()

SUPPORTED_AIS = {
    "deepseek": {
        "name": "DeepSeek V3",
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat"
    },
    "qwen": {
        "name": "Qwen 2.5",
        "api_key": os.getenv("QWEN_API_KEY", ""),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus"
    },
    "doubao": {
        "name": "doubao",
        "api_key": os.getenv("DOUBAO_API_KEY", ""),
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seed-2-0-lite-260215"
    }
}

router = APIRouter()

UPLOAD_DIR = "uploads"
PROMPT_DIR = "prompts"

class GenerateTestCaseRequest(BaseModel):
    filename: str
    user_requirement: str
    ai_name: str

def load_prompt():
    prompt_path = os.path.join(PROMPT_DIR, "base_on_requirements.md")
    if not os.path.exists(prompt_path):
        raise HTTPException(status_code=500, detail="Prompt file not found. Please check the prompts directory.")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def read_requirement_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Requirement document '{filename}' not found. Please upload it first.")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def get_ai_config(ai_name: str):
    if ai_name not in SUPPORTED_AIS:
        supported_list = ", ".join(SUPPORTED_AIS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported AI name '{ai_name}'. Currently supported: {supported_list}"
        )
    
    ai_config = SUPPORTED_AIS[ai_name]
    if not ai_config.get("api_key") or ai_config["api_key"].startswith("YOUR_"):
        raise HTTPException(
            status_code=500,
            detail=f"AI '{ai_config['name']}' API Key not configured. Please contact administrator."
        )
    
    return ai_config

def call_ai_to_generate(requirement_content: str, user_requirement: str, ai_config: dict):
    try:
        client = OpenAI(
            api_key=ai_config["api_key"],
            base_url=ai_config["base_url"]
        )

        system_prompt = load_prompt()
        user_input = f"""
        [Project Requirements Document]
        {requirement_content}

        [User Additional Requirements]
        {user_requirement if user_requirement else 'None'}
        """

        response = client.chat.completions.create(
            model=ai_config["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )

        ai_response = response.choices[0].message.content.strip()
        
        try:
            start = ai_response.find("[")
            end = ai_response.rfind("]") + 1
            if start == -1 or end == 0:
                raise ValueError("No valid JSON array found in AI response")
            json_str = ai_response[start:end]
            return json.loads(json_str)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response: {str(e)}. First 200 chars: {ai_response[:200]}..."
            )

    except AuthenticationError:
        raise HTTPException(status_code=401, detail=f"AI '{ai_config['name']}' API Key is invalid")
    except APIConnectionError:
        raise HTTPException(status_code=502, detail=f"Cannot connect to AI '{ai_config['name']}' service. Please check network connection.")
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"AI '{ai_config['name']}' service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown AI call error: {str(e)}")

@router.get("/supported-ais")
async def get_supported_ais():
    safe_ais = []
    for key, config in SUPPORTED_AIS.items():
        safe_ais.append({
            "key": key,
            "name": config["name"],
            "model": config["model"]
        })
    return {
        "status": "success",
        "data": safe_ais
    }

@router.post("/generate-test-case")
async def generate_test_case(request: GenerateTestCaseRequest):
    ai_config = get_ai_config(request.ai_name)
    requirement_content = read_requirement_file(request.filename)
    test_cases = call_ai_to_generate(requirement_content, request.user_requirement, ai_config)
    
    return {
        "status": "success",
        "filename": request.filename,
        "used_ai": ai_config["name"],
        "test_cases": test_cases
    }