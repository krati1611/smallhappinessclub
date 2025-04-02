from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from auth import AuthHandler, get_current_user
from contact_handler import ContactHandler
import config

# Set up logging from central config
config.setup_logging()
logger = logging.getLogger("smallhappiness")

# Initialize FastAPI app
app = FastAPI(title="Small Happiness Club")

# Add middleware
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize handlers
auth_handler = AuthHandler()
contact_handler = ContactHandler()

@app.get("/", response_class=HTMLResponse)
async def get_content(request: Request):
    """Serves the main page."""
    try:
        # Try to get current user if logged in
        user = None
        try:
            user = await get_current_user(request)
        except:
            pass  # User is not logged in, which is fine
            
        return templates.TemplateResponse(
            "main.html",
            {
                "request": request,
                "user": user
            }
        )
    except Exception as e:
        logger.error(f"Error serving main page: {str(e)}")
        return HTMLResponse("An error occurred", status_code=500)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serves the login page."""
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving login page: {str(e)}")
        return HTMLResponse("An error occurred", status_code=500)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serves the signup page."""
    try:
        return templates.TemplateResponse("signup.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving signup page: {str(e)}")
        return HTMLResponse("An error occurred", status_code=500)

@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Serves the contact page."""
    try:
        # Try to get current user if logged in
        user = None
        try:
            user = await get_current_user(request)
        except:
            pass  # User is not logged in, which is fine
            
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "user": user
            }
        )
    except Exception as e:
        logger.error(f"Error serving contact page: {str(e)}")
        return HTMLResponse("An error occurred", status_code=500)

@app.post("/contact")
async def handle_contact(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    copy: bool = Form(False),
    human: bool = Form(...)
):
    """Handle contact form submission"""
    try:
        if not human:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please confirm you are human"
            )
        
        # Get current user if logged in
        current_user = None
        try:
            current_user = await get_current_user(request)
        except:
            pass  # User is not logged in, which is fine for contact form
            
        # Handle the contact submission
        result = await contact_handler.handle_contact_submission(
            name=name,
            email=email,
            message=message,
            copy=copy,
            user_id=current_user["id"] if current_user else None
        )
        
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "message": result["message"],
                "success": True
            }
        )
    except HTTPException as he:
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "error": he.detail,
                "success": False
            }
        )
    except Exception as e:
        logger.error(f"Error handling contact form: {str(e)}")
        return templates.TemplateResponse(
            "contact.html",
            {
                "request": request,
                "error": "An error occurred while sending your message",
                "success": False
            }
        )

@app.post("/signup")
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...)
):
    """Handle user registration"""
    try:
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        if len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        result = await auth_handler.register_user(email, password, first_name, last_name)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "message": "Registration successful! Please login."}
        )
    except HTTPException as he:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": he.detail}
        )
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "An error occurred during registration"}
        )

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle user login"""
    try:
        result = await auth_handler.login_user(email, password)
        response = templates.TemplateResponse(
            "main.html",
            {
                "request": request,
                "user": result["user"]
            }
        )
        response.set_cookie(
            key="access_token",
            value=f"Bearer {result['access_token']}",
            httponly=True,
            max_age=1800,
            secure=True
        )
        return response
    except HTTPException as he:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": he.detail}
        )
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "An error occurred during login"}
        )

@app.get("/logout")
async def logout(request: Request):
    """Handle user logout"""
    response = templates.TemplateResponse(
        "main.html",
        {"request": request}
    )
    response.delete_cookie("access_token")
    return response

@app.get("/profile")
async def profile(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Protected route example"""
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": current_user}
    )

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {config.APP_NAME} application")
    uvicorn.run(app, host=config.HOST, port=config.PORT, debug=config.DEBUG) 