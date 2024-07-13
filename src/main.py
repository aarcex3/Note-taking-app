import uvicorn
from fastapi import FastAPI

from src.database.db import create_db_and_tables
from src.routers import health, notes, users
from src.utils.auth import security

app = FastAPI()
app.include_router(health.router)
app.include_router(notes.router)
app.include_router(users.router)
security.handle_errors(app)

if __name__ == "__main__":
    create_db_and_tables()
    uvicorn.run('__main__:app', host='0.0.0.0', port=8000, workers=4)
