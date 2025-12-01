from app.main import app
from app.database import engine
from app.config import settings

# Import sqladmin components
from sqladmin import Admin, ModelView


from app.schemas import User, Place, Rating 

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse


# 1. Configure the Authentication Backend
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # VALIDATION LOGIC:
        # Replace this with a database check in production!
        if username == "admin" and password == "secret123":
            # Set a session token
            request.session.update({"token": "valid_token"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

# 2. Initialize Auth
security_guard = AdminAuth(secret_key=settings.SECRET_KEY)



# --- ADMIN VIEWS CONFIGURATION ---
# These classes control what you see in the admin panel.
# You can customize 'column_list' based on the actual fields in your models.
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]         # Add fields you want to see
    icon = "fa-solid fa-user"

class PlaceAdmin(ModelView, model=Place):
    column_list = [Place.id, Place.name, Place.tags] # Add fields you want to see
    icon = "fa-solid fa-map-pin"

class RatingAdmin(ModelView, model=Rating):
    column_list = [Rating.id, Rating.user_id, Rating.place_id, Rating.score] # Add fields you want to see
    icon = "fa-solid fa-star"
# ---------------------------------


# Initialize Admin Interface
# This hooks the admin panel to your App and Database
admin = Admin(app, engine, authentication_backend=security_guard)

admin.add_view(UserAdmin)
admin.add_view(PlaceAdmin)
admin.add_view(RatingAdmin)
