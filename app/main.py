import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from typing import List, Optional, Any
from pydantic import BaseModel

from .database import engine, get_db, Base, SessionLocal
from . import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)

    # Create demo user if not exists
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.username == 'DemoUser').first():
            user = models.User(username='DemoUser', email='demo@example.com', bio='I am a demo user', image_url='https://via.placeholder.com/300')
            user.set_password('password')
            db.add(user)
            db.commit()
    finally:
        db.close()

    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Session Middleware
SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static Files
app.mount('/static', StaticFiles(directory='app/static'), name='static')

# Templates
templates = Jinja2Templates(directory='app/templates')

# Dependency: Get Current User
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return db.get(models.User, user_id)

# Pydantic Schemas
class UserResponse(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class SwipeRequest(BaseModel):
    swiped_id: int
    is_like: bool

# Routes

@app.get('/', response_class=HTMLResponse)
def index(request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url='/login', status_code=302)
    return templates.TemplateResponse('index.html', {'request': request, 'current_user': user})

@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

@app.post('/login', response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.check_password(password):
        return templates.TemplateResponse('login.html', {'request': request, 'error': 'Invalid username or password'})

    request.session['user_id'] = user.id
    return RedirectResponse(url='/', status_code=302)

@app.get('/register', response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})

@app.post('/register', response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(models.User).filter(models.User.username == username).first():
        return templates.TemplateResponse('register.html', {'request': request, 'error': 'Username taken'})
    if db.query(models.User).filter(models.User.email == email).first():
        return templates.TemplateResponse('register.html', {'request': request, 'error': 'Email registered'})

    user = models.User(username=username, email=email)
    user.set_password(password)
    db.add(user)
    db.commit()
    return RedirectResponse(url='/login', status_code=302)

@app.get('/logout')
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/login', status_code=302)

# API Routes

@app.get('/api/users', response_model=List[UserResponse])
def get_users(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Unauthorized')

    # Logic to filter swiped users
    swipes = db.query(models.Swipe.swiped_id).filter(models.Swipe.swiper_id == user.id).all()
    swiped_ids = [s[0] for s in swipes]
    swiped_ids.append(user.id)

    users = db.query(models.User).filter(models.User.id.notin_(swiped_ids)).limit(10).all()
    return users

@app.post('/api/swipe')
def swipe(
    swipe_data: SwipeRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail='Unauthorized')

    swipe = models.Swipe(swiper_id=user.id, swiped_id=swipe_data.swiped_id, is_like=swipe_data.is_like)
    db.add(swipe)

    match_found = False
    if swipe_data.is_like:
        # Check if the other user also liked the current user
        other_swipe = db.query(models.Swipe).filter(
            models.Swipe.swiper_id == swipe_data.swiped_id,
            models.Swipe.swiped_id == user.id,
            models.Swipe.is_like == True
        ).first()

        if other_swipe:
            match = models.Match(user1_id=user.id, user2_id=swipe_data.swiped_id)
            db.add(match)
            match_found = True

    db.commit()
    return {'success': True, 'match': match_found}

@app.get('/api/matches')
def get_matches(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail='Unauthorized')

    matches1 = db.query(models.Match).filter(models.Match.user1_id == user.id).all()
    matches2 = db.query(models.Match).filter(models.Match.user2_id == user.id).all()

    result = []
    for match in matches1 + matches2:
        other_id = match.user2_id if match.user1_id == user.id else match.user1_id
        other_user = db.get(models.User, other_id)
        if other_user:
            result.append({
                'match_id': match.id,
                'user': {
                    'id': other_user.id,
                    'username': other_user.username,
                    'image_url': other_user.image_url or 'https://via.placeholder.com/50'
                }
            })
    return result
