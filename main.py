import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from routers import auth, users, authors, articles, tags, feed, interactions, admin

load_dotenv()

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
)

# ---------------------------------------------------------------------------
# CORS — allow the Vercel frontend (and localhost for dev)
# Set ALLOWED_ORIGINS in your Render environment variables:
#   e.g.  https://echobreaker.vercel.app,http://localhost:3000
# If the variable is absent we default to allowing all origins (dev-friendly).
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Debug Exception Handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    import traceback
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
        headers={"Access-Control-Allow-Origin": "*"}
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
    db_url = os.getenv("DATABASE_URL", "")
    masked_db_url = "Not Set"
    if db_url:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            netloc = parsed.netloc
            if "@" in netloc:
                user_pass, host_port = netloc.split("@", 1)
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    netloc = f"{user}:******@{host_port}"
                else:
                    netloc = f"{user_pass}:******@{host_port}"
            masked_db_url = parsed._replace(netloc=netloc).geturl()
        except Exception as e:
            masked_db_url = f"Error: {str(e)}"
            
    return {
        "message": "EchoBreaker API is live. Visit /docs for Swagger UI. Version: 1.0.1",
        "database_url": masked_db_url
    }
