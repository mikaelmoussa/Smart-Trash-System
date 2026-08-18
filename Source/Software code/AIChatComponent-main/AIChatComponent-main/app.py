# appfast.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from datetime import datetime
from functions import get_answer

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODIFICATION START ---
@app.get("/get_answer")
async def get_answer_api(
    query: str,
    request: Request,
    history: str = "",
    name: str = "",  # Add name as an optional query parameter
    email: str = ""  # Add email as an optional query parameter
):
# --- MODIFICATION END ---
    try:
        request_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        client_ip = request.client.host
        server_host = request.scope.get("server", ("localhost",))[0]
        full_query = f"{history}\nUser: {query}" if history else f"User: {query}"
        
        # --- MODIFICATION: Pass name and email to the backend function ---
        response = get_answer(query=full_query, name=name, email=email)
        
        # --- MODIFICATION: Update logging to include user info ---
        log_message = (
            f"Client: {client_ip} - User: {name} ({email}) - Server: {server_host} - "
            f"Request Time: {request_time} - Query: '{query}' - Generated Answer: '{response['Answer']}'"
        )
        logging.info(log_message)
        
        return response
    except Exception as e:
        logging.error(f"Failed to Generate Answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)