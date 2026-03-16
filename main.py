import os

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from ai_generator import OUTPUT_ORDER, generate_all
from auth import get_current_user, hash_password, login_user, logout_user, verify_password
from database import (
    create_generations,
    create_user,
    get_remaining_generations,
    get_user_by_email,
    init_db,
    increment_generation_count,
)
from models import GenerateRequest

USAGE_LIMIT = 3

app = FastAPI(title="ContentForge")

secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
app.add_middleware(SessionMiddleware, secret_key=secret_key)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": user},
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        "signup.html",
        {"request": request, "error": None},
    )


@app.post("/signup", response_class=HTMLResponse)
def signup(request: Request, email: str = Form(...), password: str = Form(...)):
    existing = get_user_by_email(email.lower().strip())
    if existing:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Email already exists."},
        )
    password_hash = hash_password(password)
    user_id = create_user(email.lower().strip(), password_hash)
    login_user(request, user_id)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email.lower().strip())
    if not user or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid email or password."},
        )
    login_user(request, user["id"])
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    remaining = get_remaining_generations(user["id"], USAGE_LIMIT)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "remaining": remaining,
            "usage_limit": USAGE_LIMIT,
            "output_order": OUTPUT_ORDER,
        },
    )


@app.post("/generate")
async def generate(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")

    payload = await request.json()
    try:
        data = GenerateRequest(**payload)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request payload.")

    remaining = get_remaining_generations(user["id"], USAGE_LIMIT)
    if remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="Monthly generation limit reached. Try again next month.",
        )

    try:
        outputs = generate_all(data.content.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    create_generations(user["id"], data.content.strip(), outputs)
    new_count = increment_generation_count(user["id"])
    remaining_after = max(0, USAGE_LIMIT - new_count)

    return JSONResponse(
        {
            "outputs": outputs,
            "remaining": remaining_after,
        }
    )
