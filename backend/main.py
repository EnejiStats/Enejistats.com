
import os
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Response, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.requests import Request
from typing import Optional, List
from pydantic import BaseModel
import json
import bcrypt
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create necessary directories
uploads_dir = Path("static/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# MongoDB setup with fallback to JSON
MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["enejistats"]
        players_collection = db["players"]
        contact_collection = db["contact_messages"]
        print("Connected to MongoDB")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        client = None
        db = None
        players_collection = None
        contact_collection = None
else:
    client = None
    db = None
    players_collection = None
    contact_collection = None
    print("Warning: MONGO_URI not set. Using JSON file storage.")

# Pydantic Models
class Player(BaseModel):
    player_id: str
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    dob: str
    nationality: str
    preferred_position_category: str
    preferred_position: str
    club: str
    photo_url: str

# JWT Helper Functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

# Helper function to save to JSON (fallback when MongoDB is not available)
def save_to_json(data):
    registrations_file = Path("registrations.json")
    if registrations_file.exists():
        with open(registrations_file, "r") as f:
            registrations = json.load(f)
    else:
        registrations = []
    
    registrations.append(data)
    
    with open(registrations_file, "w") as f:
        json.dump(registrations, f, indent=2)

# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the home page"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception:
        try:
            return templates.TemplateResponse("register.html", {"request": request})
        except Exception:
            raise HTTPException(status_code=404, detail="Home page not found")

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """Serve the about page"""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Serve the contact page"""
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request):
    """Serve the leaderboard page"""
    return templates.TemplateResponse("leaderboard.html", {"request": request})

@app.get("/browse", response_class=HTMLResponse)
async def browse(request: Request):
    """Serve the browse page"""
    return templates.TemplateResponse("browse.html", {"request": request})

@app.get("/stats-area", response_class=HTMLResponse)
async def stats_area(request: Request):
    """Serve the stats area page with tabbed access to Player and Browse."""
    return templates.TemplateResponse("stats-area.html", {"request": request})

@app.get("/stats", response_class=HTMLResponse)
async def stats(request: Request):
    """Serve the stats page"""
    return templates.TemplateResponse("stats_area.html", {"request": request})

@app.get("/player", response_class=HTMLResponse)
async def player(request: Request):
    """Serve the player page"""
    return templates.TemplateResponse("player.html", {"request": request})

@app.get("/stats/browse", response_class=HTMLResponse)
async def stats_browse(request: Request):
    """Serve the stats browse page"""
    return templates.TemplateResponse("browse.html", {"request": request})

@app.get("/stats/player", response_class=HTMLResponse)
async def stats_player(request: Request):
    """Serve the stats player page"""
    return templates.TemplateResponse("player.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def get_register_form(request: Request):
    """Serve the registration form"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request, access_token: str = Cookie(None)):
    """Serve the login page"""
    if access_token and verify_token(access_token):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/player-dashboard", response_class=HTMLResponse)
async def player_dashboard(request: Request):
    """Serve the player dashboard page with session check"""
    return templates.TemplateResponse("player-dashboard.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, access_token: str = Cookie(None)):
    """Serve the dashboard page with authentication"""
    user_id = verify_token(access_token)
    if not user_id:
        return RedirectResponse(url="/login")

    if not players_collection:
        return RedirectResponse(url="/login")

    user = players_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "player": user
    })

@app.get("/logout")
async def logout():
    """Handle user logout"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@app.get("/success", response_class=HTMLResponse)
async def registration_success():
    """Show registration success page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Registration Success | Enejistats</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { box-sizing: border-box; }
            body { margin: 0; font-family: 'Segoe UI', sans-serif; background-color: #f5f7fa; color: #333; }
            header, footer { background-color: #1e1e2f; color: white; padding: 1rem; text-align: center; }
            nav { margin-top: 0.5rem; }
            nav a { color: white; margin: 0 0.75rem; text-decoration: none; font-weight: 500; }
            main { max-width: 800px; margin: 2rem auto; padding: 2rem; background: white; border-radius: 8px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); text-align: center; }
            h2 { color: #004aad; }
            .success-button { display: inline-block; margin: 0.5rem; padding: 0.75rem 1.5rem; background-color: #004aad; color: white; text-decoration: none; border-radius: 6px; }
        </style>
    </head>
    <body>
        <header>
            <h1>Enejistats</h1>
            <nav>
                <a href="/">Home</a>
                <a href="/leaderboard">Leaderboard</a>
                <a href="/register">Register</a>
                <a href="/stats/browse">Browse</a>
            </nav>
        </header>
        <main>
            <h2>Registration Successful!</h2>
            <p>Thank you for registering with Enejistats. Your registration has been submitted successfully.</p>
            <a href="/register" class="success-button">Register Another Player</a>
            <a href="/login" class="success-button">Login</a>
        </main>
        <footer>
            <p>&copy; 2025 Enejistats</p>
        </footer>
    </body>
    </html>
    """)

@app.get("/registrations")
async def get_registrations():
    """Get all registrations (for testing purposes)"""
    if players_collection:
        try:
            registrations = list(players_collection.find({}, {"_id": 0}))
            return {"registrations": registrations, "source": "mongodb"}
        except Exception as e:
            print(f"MongoDB query error: {e}")
    
    registrations_file = Path("registrations.json")
    if registrations_file.exists():
        with open(registrations_file, "r") as f:
            registrations = json.load(f)
        return {"registrations": registrations, "source": "json"}
    
    return {"registrations": [], "source": "none"}

@app.post("/login")
async def post_login(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle user login"""
    if not players_collection:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Database not available."
        })

    user = players_collection.find_one({"email": email})

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Invalid email or password."
        })

    stored_password = user["password"]
    if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Invalid email or password."
        })

    token = create_access_token({"sub": str(user["_id"])})
    res = RedirectResponse(url="/dashboard", status_code=302)
    res.set_cookie("access_token", token, httponly=True, max_age=3600)
    return res

@app.post("/submit-contact")
async def submit_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    """Handle contact form submission"""
    contact_data = {
        "name": name,
        "email": email,
        "message": message
    }
    
    if contact_collection:
        try:
            contact_collection.insert_one(contact_data)
        except Exception as e:
            print(f"Failed to save contact message: {e}")
    
    return templates.TemplateResponse("contact.html", {"request": request, "success": True})

@app.post("/register")
async def register_user(
    request: Request,
    userType: str = Form(...),
    firstName: Optional[str] = Form(None),
    middleName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    playerNationality: Optional[str] = Form(None),
    playerPhoto: Optional[UploadFile] = File(None),
    preferredPositionCategory: Optional[str] = Form(None),
    preferredPosition: Optional[str] = Form(None),
    otherPositions: Optional[List[str]] = Form(None),
    dominantFoot: Optional[str] = Form(None),
    height: Optional[int] = Form(None),
    weight: Optional[int] = Form(None),
    league: Optional[str] = Form(None),
    leagueClub: Optional[str] = Form(None),
    generalClub: Optional[str] = Form(None),
    clubAssociation: Optional[str] = Form(None),
    club: Optional[str] = Form(None),
    player_id: Optional[str] = Form(None),
    first_name: Optional[str] = Form(None),
    middle_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    preferred_position_category: Optional[str] = Form(None),
    preferred_position: Optional[str] = Form(None),
    photo_url: Optional[str] = Form(None)
):
    """Handle both web form registration and API registration"""
    
    try:
        # Check if this is an API call
        is_api_call = bool(player_id and first_name and last_name)
        
        if is_api_call:
            # Handle API registration
            new_player = {
                "player_id": player_id,
                "first_name": first_name,
                "middle_name": middle_name or "",
                "last_name": last_name,
                "dob": dob,
                "nationality": nationality,
                "preferred_position_category": preferred_position_category,
                "preferred_position": preferred_position,
                "club": club,
                "photo_url": photo_url
            }
            
            try:
                if players_collection:
                    players_collection.insert_one(new_player.copy())
                else:
                    save_to_json(new_player)
                
                return JSONResponse(content={
                    "success": True, 
                    "message": "Player registered successfully via API",
                    "player": new_player
                })
            except Exception as e:
                print(f"API registration error: {e}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"Registration failed: {str(e)}"
                }, status_code=500)
        
        # Handle web form registration
        if userType not in ["player", "club", "scout"]:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Invalid user type selected"
            })
        
        if userType == "player":
            # Validate required fields
            required_fields = {
                "firstName": firstName,
                "lastName": lastName,
                "email": email,
                "password": password,
                "dob": dob,
                "gender": gender,
                "playerNationality": playerNationality,
                "preferredPositionCategory": preferredPositionCategory,
                "preferredPosition": preferredPosition,
                "dominantFoot": dominantFoot,
                "height": height,
                "weight": weight,
                "league": league,
                "clubAssociation": clubAssociation
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                return templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                })
            
            # Check if email already exists
            if players_collection:
                existing_user = players_collection.find_one({"email": email})
                if existing_user:
                    return templates.TemplateResponse("register.html", {
                        "request": request,
                        "error": "Email already registered"
                    })
            
            # Handle photo upload
            photo_filename = None
            if playerPhoto and playerPhoto.filename:
                try:
                    content = await playerPhoto.read()
                    if len(content) > 20 * 1024:  # 20KB limit
                        return templates.TemplateResponse("register.html", {
                            "request": request,
                            "error": "Photo size must be 20KB or less"
                        })
                    
                    photo_filename = f"{firstName.lower()}_{lastName.lower()}.jpg"
                    file_path = uploads_dir / photo_filename
                    with open(file_path, "wb") as buffer:
                        buffer.write(content)
                except Exception as e:
                    print(f"Photo upload error: {e}")
                    return templates.TemplateResponse("register.html", {
                        "request": request,
                        "error": "Failed to upload photo"
                    })
            
            # Hash password
            try:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            except Exception as e:
                print(f"Password hashing error: {e}")
                return templates.TemplateResponse("register.html", {
                    "request": request,
                    "error": "Password processing failed"
                })
            
            # Determine selected club
            selected_club = leagueClub or generalClub or club
            
            # Prepare registration data
            registration_data = {
                "userType": userType,
                "firstName": firstName,
                "middleName": middleName,
                "lastName": lastName,
                "email": email,
                "password": hashed_password,
                "dob": dob,
                "gender": gender,
                "nationality": playerNationality,
                "photo": photo_filename,
                "preferredPositionCategory": preferredPositionCategory,
                "preferredPosition": preferredPosition,
                "otherPositions": otherPositions or [],
                "dominantFoot": dominantFoot,
                "height": height,
                "weight": weight,
                "league": league,
                "club": selected_club,
                "clubAssociation": clubAssociation
            }
            
            # Save to database
            try:
                if players_collection:
                    clean_data = {k: v for k, v in registration_data.items() if v is not None and k != 'userType'}
                    players_collection.insert_one(clean_data)
                else:
                    save_to_json(registration_data)
                
                return RedirectResponse(url="/success", status_code=303)
            except Exception as e:
                print(f"Database save error: {e}")
                try:
                    save_to_json(registration_data)
                    return RedirectResponse(url="/success", status_code=303)
                except Exception as json_error:
                    print(f"JSON fallback error: {json_error}")
                    return templates.TemplateResponse("register.html", {
                        "request": request,
                        "error": "Registration failed. Please try again."
                    })
        else:
            # Other user types not implemented yet
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": f"{userType.title()} registration coming soon!"
            })
    
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "An unexpected error occurred. Please try again."
        })

@app.post("/validate-player")
async def validate(player: Player):
    """Validate player data using Pydantic model"""
    return {"message": "Player data is valid", "player": player.dict()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
