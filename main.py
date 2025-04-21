from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import re
import math
from collections import defaultdict
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

cache = {}

def process_text(text: str) -> list:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if not paragraphs:
        return []
    
    paragraphs_ = []
    word_tf = defaultdict(int)
    
    for para in paragraphs:
        words = re.findall(r'\w+', para.lower())
        for word in words:
            word_tf[word] += 1
        paragraphs_.append(set(words))
    
    word_df = defaultdict(int)
    for word in word_tf:
        for para_set in paragraphs_:
            if word in para_set:
                word_df[word] += 1
    
    n_paragraphs = len(paragraphs)
    word_idf = {}
    for word in word_tf:
        df = word_df[word]
        word_idf[word] = math.log(n_paragraphs / df) if df != 0 else 0
    
    data = [{"word": word, "tf": word_tf[word], "idf": word_idf[word]} for word in word_tf]
    sorted_data = sorted(data, key=lambda x: x["idf"], reverse=True)[:50]
    
    return sorted_data

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    processed_data = process_text(content)
    cache_id = str(uuid.uuid4())
    cache[cache_id] = processed_data
    return RedirectResponse(url=f"/results?cache_id={cache_id}&page=1", status_code=303)

@app.get("/results", response_class=HTMLResponse)
async def show_results(request: Request, cache_id: str, page: int = 1):
    data = cache.get(cache_id, [])
    per_page = 10
    total_pages = (len(data) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    current_data = data[start:end]
    
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "data": current_data,
            "current_page": page,
            "total_pages": total_pages,
            "cache_id": cache_id
        }
    )

