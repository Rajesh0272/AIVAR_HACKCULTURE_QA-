from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.orchestration.orchestrator import AIVAROrchestrator
app=FastAPI(title="AIVAR Autonomous QA")
class RunRequest(BaseModel): url:str
@app.get("/",response_class=HTMLResponse)
def home(): return """<!doctype html><html><head><title>AIVAR</title><style>body{font-family:Arial;max-width:900px;margin:40px auto}input{width:70%;padding:12px}button{padding:12px}pre{background:#f4f4f4;padding:15px;white-space:pre-wrap}</style></head><body><h1>AIVAR — Autonomous Test Orchestration Agent</h1><p>Enter a web application URL and run the autonomous QA lifecycle.</p><input id='url' value='http://127.0.0.1:9000'><button onclick='run()'>Run AIVAR</button><pre id='out'>Ready.</pre><script>async function run(){out.textContent='Running...';try{let r=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:document.getElementById('url').value})});out.textContent=JSON.stringify(await r.json(),null,2)}catch(e){out.textContent=e}}</script></body></html>"""
@app.post("/run")
def run(req:RunRequest):
    try:return AIVAROrchestrator().run(req.url).model_dump()
    except Exception as e: raise HTTPException(status_code=500,detail=str(e))

