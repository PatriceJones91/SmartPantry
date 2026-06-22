from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth, pantry, surveys, recommendations, admin, barcodes, profile

app = FastAPI(
    title="Smart Pantry 2.0 API",
    version="1.0.0",
    description="Backend API for Smart Pantry 2.0 React and Supabase application.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(pantry.router, prefix="/api/pantry", tags=["pantry"])
app.include_router(surveys.router, prefix="/api/surveys", tags=["surveys"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(barcodes.router, prefix="/api/barcodes", tags=["barcodes"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
