import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from routers import auth, users, authors, articles, tags, feed, interactions, admin
from database import run_migrations

load_dotenv()

# ---------------------------------------------------------------------------
# Lifespan startup migrations
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="EchoBreaker API",
    description=(
        "API for the EchoBreaker digital publishing platform "
        "(Track B: Contrarian Recommendation Engine)"
    ),
    version="1.0.0",
    docs_url=None,   # we serve a custom /docs page below
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Vercel frontend (and localhost for dev)
# Set ALLOWED_ORIGINS in your Render environment variables:
#   e.g.  https://echobreaker.vercel.app,http://localhost:3000
# ---------------------------------------------------------------------------
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_str:
    allowed_origins = [orig.strip() for orig in allowed_origins_str.split(",") if orig.strip()]
else:
    # Safe defaults for local dev. In production, configure ALLOWED_ORIGINS.
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://eco-breaker-frontend.vercel.app"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if allowed_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Debug Exception Handler
# ---------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    import traceback
    print("Internal Server Error occurred:")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Check server logs for details."},
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(authors.router)
app.include_router(articles.router)
app.include_router(tags.router)
app.include_router(feed.router)
app.include_router(interactions.router)
app.include_router(admin.router)


# ---------------------------------------------------------------------------
# Custom Swagger UI (dark-themed)
# ---------------------------------------------------------------------------
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    openapi_url = app.openapi_url
    title = app.title + " — Swagger UI"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/gh/Itz-fork/Fastapi-Swagger-UI-Dark/assets/swagger_ui_dark.min.css">
    <style>
        body {{
            background: linear-gradient(135deg, #0f172a, #1e1b4b) !important;
            color: #f8fafc;
            font-family: 'Outfit', sans-serif;
            margin: 0; padding: 0; min-height: 100vh;
        }}
        .swagger-ui {{ font-family: 'Outfit', sans-serif !important; filter: drop-shadow(0 0 10px rgba(0,0,0,.5)); }}
        .swagger-ui .topbar {{ background: rgba(15,23,42,.8) !important; backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255,255,255,.1); }}
        .swagger-ui .info hgroup.main a {{ color: #38bdf8 !important; }}
        .swagger-ui .opblock {{ background: rgba(255,255,255,.03) !important; backdrop-filter: blur(5px) !important; border: 1px solid rgba(255,255,255,.1) !important; border-radius: 12px !important; margin-bottom: 15px !important; }}
        .swagger-ui .opblock-summary-method {{ border-radius: 6px !important; }}
        .swagger-ui .info .title {{ color: #f8fafc !important; }}
        .swagger-ui section.models {{ background: rgba(255,255,255,.03) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,.1) !important; }}
    </style>
    </head>
    <body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
    window.onload = function() {{
      const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
        dom_id: '#swagger-ui',
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
        layout: "BaseLayout",
        deepLinking: true,
        showExtensions: true,
        showCommonExtensions: true
      }})
      window.ui = ui
    }}
    </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ---------------------------------------------------------------------------
# Health-check root
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    # Only reveal whether database URL is configured to prevent infrastructure leakage
    db_configured = bool(os.getenv("DATABASE_URL"))
    return {
        "message": "EchoBreaker API is live. Visit /docs for Swagger UI. Version: 1.0.1",
        "database_configured": db_configured
    }

@app.get("/debug-env")
def debug_env():
    return {"db_url": os.getenv("DATABASE_URL")}
