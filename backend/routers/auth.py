"""Single-account authentication with opaque, expiring server-side sessions."""
import hashlib
import hmac
import secrets
import time
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix='/api/auth', tags=['authentication'])
COOKIE = 'execflow_session'
LIFETIME = 8 * 60 * 60
USER = {'name': 'Arjun Malhotra', 'email': 'arjun@company'}
PASSWORD_HASH = '24e26abbe6eb1ac6302f82054c5c230b38d2fe2e01686e4554615760a93944f6'
sessions: dict[str, float] = {}

def session_key(token):
    return hashlib.sha256(token.encode()).hexdigest()

def authenticated(request: Request):
    token = request.cookies.get(COOKIE, '')
    if not token:
        return False
    key = session_key(token)
    expires = sessions.get(key, 0)
    if expires <= time.time():
        sessions.pop(key, None)
        return False
    return True

class LoginInput(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=256)

@router.post('/login')
def login(body: LoginInput, request: Request, response: Response):
    digest = hashlib.pbkdf2_hmac('sha256', body.password.encode(), b'execflow-single-user-v1', 210000).hex()
    password_ok = hmac.compare_digest(digest, PASSWORD_HASH)
    email_ok = hmac.compare_digest(body.email.strip().lower().encode(), USER['email'].encode())
    if not (password_ok and email_ok):
        raise HTTPException(401, 'Email or password is incorrect.')
    now = time.time()
    for key, expiry in list(sessions.items()):
        if expiry <= now:
            sessions.pop(key, None)
    old_token = request.cookies.get(COOKIE)
    if old_token:
        sessions.pop(session_key(old_token), None)
    token = secrets.token_urlsafe(32)
    sessions[session_key(token)] = now + LIFETIME
    response.set_cookie(COOKIE, token, max_age=LIFETIME, httponly=True,
        secure=request.url.scheme == 'https', samesite='strict', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return USER

@router.get('/me')
def me(request: Request, response: Response):
    if not authenticated(request):
        raise HTTPException(401, 'Please sign in to continue.')
    response.headers['Cache-Control'] = 'no-store'
    return USER

@router.post('/logout')
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE, '')
    sessions.pop(session_key(token), None)
    response.delete_cookie(COOKIE, path='/', httponly=True, samesite='strict')
    return {'ok': True}
