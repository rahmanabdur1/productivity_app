
Django and frontend(Dash)

# Django Backend for Employee Time Tracking & Productivity

This is the backend API for the Employee Time Tracking & Productivity Web Application, built with Django and Django REST Framework, using PostgreSQL as the database.

## 1. Setup

### 1.1. Prerequisites

* Python 3.8+
* pip (Python package installer)
* PostgreSQL database server (running)

### 1.2. Virtual Environment & Dependencies

1.  Navigate into the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create a Python virtual environment:
    ```bash
    python -m venv .venv
    ```
3.  Activate the virtual environment:
    * **On Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    * **On macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```
4.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    (If `requirements.txt` doesn't exist, create it by running `pip install Django djangorestframework psycopg2-binary django-cors-headers` and then `pip freeze > requirements.txt`.)

### 1.3. PostgreSQL Database Configuration

1.  **Create a PostgreSQL database and user:**
    * Open your PostgreSQL client (e.g., `psql` in terminal, or pgAdmin).
    * Connect as the `postgres` superuser.
    * Execute the following SQL commands. **Remember to replace `your_db_name`, `your_db_user`, and `your_db_password` with your chosen values.**
        ```sql
        CREATE DATABASE your_db_name;
        CREATE USER your_db_user WITH PASSWORD 'your_db_password';
        ALTER ROLE your_db_user SET client_encoding TO 'utf8';
        ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
        ALTER ROLE your_db_user SET timezone TO 'UTC';
        GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
        ```
2.  **Update Django `settings.py`:**
    * Open `my_productivity_backend/settings.py`.
    * Locate the `DATABASES` section and update it with your PostgreSQL credentials:
        ```python
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'your_db_name',
                'USER': 'your_db_user',
                'PASSWORD': 'your_db_password',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
        ```
    * Ensure `corsheaders` and your custom apps (`users`, `timetracking`, `projects`) are in `INSTALLED_APPS`.
    * Verify `CORS_ALLOWED_ORIGINS` includes your Dash frontend's URL (e.g., `"http://localhost:8050"`).

### 1.4. Database Migrations

1.  Apply the database migrations to create tables for your models:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

### 1.5. Create Superuser (Admin Account)

1.  Create an administrative user for the Django admin panel and initial testing:
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to set a username, email, and password.

### 1.6. Create User Groups (Optional but Recommended for Roles)

For robust role management, create these groups in the Django admin panel (`http://127.0.0.1:8000/admin/`) under "Authentication and Authorization" -> "Groups":
* `Employees`
* `TeamHeads`
* `ProjectManagers`

You can then assign users to these groups via the admin panel. The `User` model's `role` property in `users/models.py` will automatically reflect these group memberships.

## 2. Running the Backend

1.  Make sure your virtual environment is active (`(.venv)` in your terminal prompt).
2.  Start the Django development server:
    ```bash
    python manage.py runserver
    ```
    The API will be accessible at `http://127.0.0.1:8000/api/`.

## 3. API Endpoints (Examples)

Once the server is running, you can access the browsable API at `http://127.0.0.1:8000/api/`.

* **Authentication:**
    * `POST /api/token/`: Obtain an authentication token. Send `username` and `password`.
* **Users:**
    * `GET /api/users/`: List all users (admin only).
    * `GET /api/users/<id>/`: Retrieve a specific user (admin only).
    * `GET /api/users/me/`: Retrieve the profile of the currently authenticated user.
    * `POST /api/users/`: Create a new user (admin only).
    * `PUT/PATCH /api/users/<id>/`: Update a user (admin only).
    * `DELETE /api/users/<id>/`: Delete a user (admin only).
    * `POST /api/users/<id>/set_role/`: Set a user's role (admin only).
* **Time Logs:**
    * `GET /api/timelogs/`: List time logs (filtered by user role).
    * `POST /api/timelogs/`: Create a new time log.
    * `GET /api/timelogs/daily_summary/`: Get daily working hours and app usage summary for the current user.
* **App Usage:**
    * `GET /api/appusages/`: List app usages (filtered by user role).
    * `GET /api/appusages/summary/`: Get summary of app usage (e.g., by app name).
* **Activity Metrics:**
    * `GET /api/activitymetrics/`: List activity metrics (filtered by user role).
* **Teams:**
    * `GET /api/teams/`: List all teams.
    * `POST /api/teams/`: Create a new team (admin/team head).
* **Projects:**
    * `GET /api/projects/`: List all projects.
    * `POST /api/projects/`: Create a new project (admin/project manager).
    * `GET /api/projects/<id>/progress_report/`: Get a progress report for a specific project.

## 4. Development Notes

* **Security:** This setup is for development. For production, ensure `DEBUG = False`, `SECRET_KEY` is strong, `ALLOWED_HOSTS` is configured, and use HTTPS.
* **Permissions:** The `IsOwnerOrAdminOrTeamHeadOrProjectManager` custom permission is a starting point. You might need to refine it further based on your exact access control requirements.
* **Filtering:** For dashboards (e.g., Team Head, Project Manager), you'll need to implement more sophisticated filtering on the backend views (e.g., `filterset_fields` with `django-filter`) to allow the frontend to request data for specific teams or projects.
* **Data Population:** After setting up, you'll need to populate your database with some initial data (users, teams, projects, time logs) either via the Django admin panel or by creating custom management commands.
