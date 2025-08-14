# 🚀 FastAPI Project

A modern web API built with [FastAPI](https://fastapi.tiangolo.com/) and PostgreSQL, featuring JWT authentication, email support, and Alembic migrations.

---

## 📌 Features
- 🔐 **JWT Authentication** (Login, Signup, Password Reset)
- 🗄 **PostgreSQL Database** with SQLAlchemy ORM
- 📧 Email sending with FastAPI-Mail
- 📜 Database migrations with Alembic
- 🛠 Environment-based configuration using Pydantic Settings

---

## 🛠 Tech Stack
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Auth:** python-jose, passlib[bcrypt]
- **Migrations:** Alembic
- **Email:** FastAPI-Mail
- **Environment Management:** python-decouple / pydantic-settings

---

## ⚙️ Installation

 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo

2️⃣ Create a virtual environment

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

3️⃣ Install dependencies

pip install -r requirements.txt

4️⃣ Set up environment variables
Create a .env file in the root directory:

DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME="FastAPI App"

### Running the App

uvicorn app.main:app --reload

### Database Migrations

alembic upgrade head

### API Documentation

Once running, visit:
Swagger UI → http://127.0.0.1:8000/docs
ReDoc → http://127.0.0.1:8000/redoc
