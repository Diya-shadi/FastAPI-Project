from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.utils.security import get_password_hash
from app.database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_user_roles():
    """Seed initial user roles - this is mainly for documentation"""
    logger.info("User roles are defined in the UserRole enum:")
    logger.info("- admin: Full system access")
    logger.info("- user: Regular user access")
    logger.info("- editor: Content editing access")

def seed_superadmin():
    """Create initial superadmin user"""
    db = SessionLocal()
    
    try:
        # Check if superadmin already exists
        existing_admin = db.query(User).filter(
            User.email == "adminshadiya@gmail.com"
        ).first()
        
        if existing_admin:
            logger.info("Superadmin already exists")
            return
        
        # Create superadmin
        superadmin = User(
            email="adminshadiya@gmail.com",
            hashed_password=get_password_hash("admin123!"),
            full_name="Super Administrator",
            role=UserRole.admin,
            is_active=True,
            is_verified=True
        )
        
        db.add(superadmin)
        db.commit()
        
        logger.info("Superadmin created successfully")
        logger.info("Email: adminshadiya@gmail.com")
        logger.info("Password: admin123!")
        
    except Exception as e:
        logger.error(f"Error creating superadmin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_user_roles()
    seed_superadmin()