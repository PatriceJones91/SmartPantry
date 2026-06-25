from fastapi import Request, Response
from fastapi import FastAPI
from routes.barcodes import router as barcodes_router

from routes import auth, pantry, surveys, recommendations, admin, barcodes, profile

app = FastAPI(



    title="Smart Pantry 2.0 API",
    version="1.0.0",
    description="Backend API for Smart Pantry 2.0 React and Supabase application.",
)

# Direct CORS middleware for deployed Vercel frontend
@app.middleware("http")
async def smart_pantry_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")

    allowed = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://smart-pantry-kappa.vercel.app",
        "https://smart-pantry-capstone.vercel.app",
    }

    is_vercel_preview = bool(origin and origin.endswith(".vercel.app"))
    is_allowed = bool(origin and (origin in allowed or is_vercel_preview))

    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        response = await call_next(request)

    if is_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"

    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "86400"

    return response



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


app.include_router(barcodes_router, prefix="/api", tags=["barcodes"])
