# Recent Updates - Profile Features

## ✅ Completed Features

### 1. Cover Image Upload
- **Backend**: Created `/api/v1/auth/upload-cover` endpoint
- **Database**: Added `cover_image_url` column to User table (migration: `2103b65d3fb9`)
- **Frontend**: 
  - Added file input for cover image in Edit Profile modal
  - Preview functionality for cover image (max 10MB)
  - Cover image displays on profile page
  - Stored in `/uploads/covers/` directory

### 2. Bio Display Section
- **Backend**: `bio` field already exists in User model
- **Frontend**: 
  - Added dedicated bio section in "About" tab
  - Displays user's bio with proper formatting
  - Shows "No bio yet" if empty
  - Editable through Edit Profile modal

### 3. Liked Status Indicators (Teal Color)
- **Backend**: Using existing endpoints:
  - `GET /api/v1/likes/check/comment/{comment_id}` - Check if comment is liked
  - `GET /api/v1/likes/check/place/{place_id}` - Check if place is liked
- **Frontend**:
  - Liked comments show **filled heart icon** (fas fa-heart) in **teal color** (#14838B)
  - Unliked comments show **outline heart icon** (far fa-heart) in gray
  - Like button text changes from "Like" to "Liked"
  - Hover effects maintain proper colors

## 🎨 Visual Changes

### Profile Page
- **Cover Image**: Displayed at top of profile (replaces placeholder)
- **Bio Section**: New section below location info with icon and formatted text
- **Edit Profile Modal**: Now includes:
  - Display Name input
  - Avatar file upload (max 5MB) with preview
  - Cover image file upload (max 10MB) with preview
  - Bio textarea
  - Location input

### Detail Page (Place Reviews)
- **Liked Comments**: Heart icon is **teal** (#14838B) and **filled** (solid)
- **Unliked Comments**: Heart icon is **gray** and **outlined** (hollow)
- **Interactive**: Clicking toggles between liked/unliked states

## 📁 Modified Files

### Backend
1. `Backend/app/routers/auth.py` - Added `upload_cover()` endpoint
2. `Backend/app/schemas.py` - Added `cover_image_url` to User models
3. `Backend/alembic/versions/2103b65d3fb9_add_cover_image_to_user.py` - Migration file

### Frontend
1. `frontend/exSighting/profile.html` - Added cover input, bio section
2. `frontend/exSighting/src/js/profile.js` - Cover upload logic, bio display
3. `frontend/exSighting/src/js/detail.js` - Teal color for liked comments

## 🚀 How to Use

### Upload Cover Image
1. Go to profile page
2. Click "Edit Profile" button
3. Click "Choose File" under "Cover Image"
4. Select image (max 10MB)
5. Preview appears below
6. Click "Save Changes"
7. Cover image updates on profile page

### View Bio
1. Navigate to profile page
2. Go to "About" tab
3. Bio section appears below location info
4. Edit bio through "Edit Profile" modal

### See Liked Status
1. Go to any place detail page
2. Scroll to comments/reviews section
3. **Teal filled hearts** = You already liked this comment
4. **Gray outline hearts** = Not liked yet
5. Click heart to toggle like/unlike

## 🛠️ Technical Details

### API Endpoints Used
- `POST /api/v1/auth/upload-cover` - Upload cover image
- `GET /api/v1/auth/profile` - Get user profile data
- `PUT /api/v1/auth/profile` - Update profile (including bio, cover_image_url)
- `GET /api/v1/likes/check/comment/{id}` - Check comment like status
- `GET /api/v1/likes/check/place/{id}` - Check place like status

### File Storage
- Avatar images: `/uploads/avatars/`
- Cover images: `/uploads/covers/`
- Format: `cover_{user_id}_{timestamp}.{extension}`

### Color Scheme
- **Teal** (#14838B) - Primary brand color, used for:
  - Liked hearts
  - Active buttons
  - Hover states
- **Gray** (#999) - Inactive/unliked state

## 🔄 Server Status
Backend is running on http://0.0.0.0:8000

To restart backend:
```bash
cd Backend
export PYTHONPATH=$PWD
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
