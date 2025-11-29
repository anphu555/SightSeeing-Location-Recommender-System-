from app.main import app
from app.database import engine

# Import sqladmin components
from sqladmin import Admin, ModelView


from app.schemas import User, Place, Rating 

# --- ADMIN VIEWS CONFIGURATION ---
# These classes control what you see in the admin panel.
# You can customize 'column_list' based on the actual fields in your models.
class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username]         # Add fields you want to see
    icon = "fa-solid fa-user"

class PlaceAdmin(ModelView, model=Place):
    column_list = [Place.id, Place.name] # Add fields you want to see
    icon = "fa-solid fa-map-pin"

class RatingAdmin(ModelView, model=Rating):
    column_list = [Rating.id, Rating.user_id, Rating.place_id] # Add fields you want to see
    icon = "fa-solid fa-star"
# ---------------------------------


# Initialize Admin Interface
# This hooks the admin panel to your App and Database
admin = Admin(app, engine)

admin.add_view(UserAdmin)
admin.add_view(PlaceAdmin)
admin.add_view(RatingAdmin)
