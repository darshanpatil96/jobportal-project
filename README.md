# Job Portal

A Django-based job portal application that connects job seekers with employers.

## Features

- User authentication and profiles
- Job listings and applications
- Employer dashboard for job management
- Job seeker dashboard for applications and saved jobs
- Email notifications
- Company profiles and listings

## Technologies Used

- **Backend**: Django
- **Database**: SQLite (development)
- **Frontend**: HTML, CSS, JavaScript

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/jobportal_project.git
cd jobportal_project
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Project Structure

- `accounts/` - User authentication and profiles
- `applications/` - Job applications management
- `jobs/` - Job listings and search
- `templates/` - HTML templates
- `static/` - CSS and JavaScript files
- `media/` - User uploads

## Admin Panel

Access the Django admin panel at `/admin/` with your superuser credentials.

## License

MIT License
