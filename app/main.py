from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, dashboard

app = FastAPI(
    title="FastAPI Login System",
    description="A complete authentication system with FastAPI and PostgreSQL",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    return {
        "message": "FastAPI Login System with Dashboard User Management is running!",
        "features": [
            "User Registration with Role Dropdown Selection",
            "Dashboard-based User Management",
            "Role-based Access Control",
            "Email Verification System",
            "JWT-based Authentication",
            "Password Reset via Email",
            "Bulk User Operations",
            "User Analytics and Reports",
            "Advanced User Search and Filtering"
        ],
        "dashboard_endpoints": {
            "auth": {
                "roles": "GET /auth/user-roles - Get role dropdown",
                "register": "POST /auth/register - Register with role",
                "login": "POST /auth/login - User login"
            },
            "dashboard": {
                "home": "GET /dashboard/ - Dashboard home with stats",
                "profile": "GET /dashboard/profile - My profile",
                "update_profile": "PUT /dashboard/profile - Update my profile"
            },
            "user_management": {
                "create_user": "POST /dashboard/users - Create user (Admin)",
                "list_users": "GET /dashboard/users - List users with filters",
                "get_user": "GET /dashboard/users/{id} - Get user details",
                "update_user": "PUT /dashboard/users/{id} - Update user",
                "delete_user": "DELETE /dashboard/users/{id} - Delete user (Admin)",
                "activate": "PATCH /dashboard/users/{id}/activate (Admin)",
                "deactivate": "PATCH /dashboard/users/{id}/deactivate (Admin)",
                "verify": "PATCH /dashboard/users/{id}/verify (Admin)",
                "bulk_actions": "POST /dashboard/users/bulk-action (Admin)",
                "stats": "GET /dashboard/users/stats - User statistics",
                "by_role": "GET /dashboard/users/by-role/{role} - Users by role",
                "roles": "GET /dashboard/users/roles - Role dropdown"
            },
            "analytics": {
                "user_growth": "GET /dashboard/analytics/user-growth",
                "activity_report": "GET /dashboard/reports/user-activity"
            }
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)