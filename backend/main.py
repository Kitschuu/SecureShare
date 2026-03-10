from fastapi import FastAPI
from database import engine, Base
from routers import auth, files, admin

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SecureShare API", description="End-to-End Encrypted File Sharing")

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Welcome to SecureShare API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
