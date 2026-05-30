# PROJECT_CONTEXT.md
# ARTISAN. — AI-Powered Hiring Platform
> Single source of truth for developers and AI coding assistants.
> 
> Last Updated: 2026-05-24

---

# 1. Executive Summary

ARTISAN. is a premium AI-powered hiring platform built with Django.

The platform connects:
- Job Seekers (Employees)
- Employers (Recruiters / Companies)

through:
- AI resume parsing
- AI candidate-job matching
- hiring pipelines
- interview scheduling
- analytics
- notifications
- employer ATS workflows

The architecture follows:

```txt
Thin Views → Service Layer → ORM Models → Database

Core philosophy:

reusable services
scalable workflows
production-style backend architecture
AI-ready design
future API compatibility
2. System Architecture
┌─────────────────────────────┐
│        Frontend UI          │
│ Django Templates + Tailwind│
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│         Views Layer         │
│       core/views.py         │
│ Auth, redirects, rendering  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│        Service Layer        │
├─────────────────────────────┤
│ core/services.py            │
│ core/ai/                    │
│ core/hiring/                │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│        ORM Models           │
│       core/models.py        │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ SQLite / PostgreSQL DB      │
└─────────────────────────────┘
3. Platform Roles
Role	Purpose	Main Features
Jobseeker	Search & apply to jobs	Resume upload, AI matching, saved jobs, application tracking
Employer	Manage hiring workflows	Post jobs, review candidates, schedule interviews
Admin	Platform management	Django admin tools
4. Core Platform Features
Feature	Status	Description
Authentication	Complete	Login, register, logout
Email Verification	Complete	Required before applying/posting
Job Listings	Complete	Search, filter, pagination
Saved Jobs	Complete	Save/unsave functionality
Applications	Complete	Apply, edit, withdraw
AI Resume Parsing	Complete	PDF parsing + NLP extraction
AI Match Scoring	Complete	Candidate-job compatibility
Hiring Pipeline	Complete	Multi-stage transitions
Interview Scheduling	Complete	Employer interview workflow
Notifications	Complete	In-app alerts
Timeline Tracking	Complete	Audit-style application history
Employer Dashboard	Complete	Hiring analytics
Employer ATS Portal	In Progress	Dedicated employer workspace
5. Tech Stack
Layer	Technology
Language	Python 3.12+
Framework	Django 5.2.8
Database	SQLite (dev), PostgreSQL (production)
AI Parsing	PyMuPDF
NLP	spaCy
Frontend	Django Templates + Tailwind CSS
Deployment	Render
Static Files	WhiteNoise
Server	Gunicorn
6. Directory Structure
jobportal_project/
│
├── manage.py
├── PROJECT_CONTEXT.md
├── requirements.txt
├── render.yaml
│
├── jobportal/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── services.py
│   ├── utils.py
│   ├── signals.py
│   ├── admin.py
│   │
│   ├── ai/
│   │   ├── resume_parser.py
│   │   └── matching_engine.py
│   │
│   └── hiring/
│       ├── workflow.py
│       ├── pipeline.py
│       ├── timeline.py
│       ├── interviews.py
│       └── notifications.py
│
├── templates/
│   ├── auth/
│   ├── jobs/
│   ├── dashboard/
│   ├── employer/
│   └── includes/
│
├── static/
├── media/
└── staticfiles/
7. Service Layer Responsibilities
Service	Responsibility
ResumeParserService	Extract structured data from resumes
MatchingEngineService	Compute AI compatibility scores
PipelineService	Validate hiring stage transitions
TimelineService	Create audit timeline events
InterviewService	Schedule and manage interviews
NotificationService	Send in-app notifications
ApplicationWorkflowService	Orchestrate post-application workflow
8. Main Database Relationships
User
 └── UserProfile
      ├── Job
      ├── Application
      ├── SavedJob
      └── Notification

Application
 ├── ParsedResume
 ├── ApplicationMatchScore
 ├── Interview
 ├── ApplicationStatusHistory
 └── ApplicationTimelineEvent
9. Main Models
Model	Purpose
UserProfile	Role-based profile system
Job	Job postings
Application	Candidate applications
SavedJob	Bookmarked jobs
Notification	In-app alerts
ParsedResume	Extracted resume data
ApplicationMatchScore	AI compatibility scoring
Interview	Interview scheduling
ApplicationStatusHistory	Hiring stage history
ApplicationTimelineEvent	Audit event log
10. Main Workflows
Registration Workflow
Register User
      │
      ▼
Send Activation Email
      │
      ▼
Activate Account
      │
      ▼
Email Verified
Job Application Workflow
Candidate Applies
       │
       ▼
Application Created
       │
       ▼
ApplicationWorkflowService
       │
 ┌─────┼────────────────────┐
 ▼     ▼                    ▼
Timeline Resume Parse   Notifications
Log      │
          ▼
     Match Engine
          │
          ▼
    Match Score Saved
Hiring Pipeline Workflow
Applied
   │
   ▼
Screening
   │
   ▼
Technical Round
   │
   ▼
HR Round
   │
   ▼
Final Review
   │
   ▼
Offer Sent
   │
 ┌─┴──────────┐
 ▼            ▼
Hired      Rejected
Interview Workflow
Employer Schedules Interview
            │
            ▼
Interview Record Created
            │
            ▼
Notification + Email Sent
            │
            ▼
Timeline Updated
            │
            ▼
Interview Completed/Cancelled
11. AI Resume Parsing
Item	Detail
Service	ResumeParserService
File	core/ai/resume_parser.py
Libraries	PyMuPDF, spaCy
Input	PDF Resume
Output	Structured JSON
Extracted Data	Skills, education, experience, certifications, contacts

Workflow:

PDF Upload
    │
    ▼
Extract Text
    │
    ▼
NLP Parsing
    │
    ▼
Structured Resume Data
    │
    ▼
Save ParsedResume
12. AI Match Engine
Item	Detail
Service	MatchingEngineService
File	core/ai/matching_engine.py
Purpose	Candidate-job compatibility scoring

Scoring Factors:

skills overlap
experience relevance
education relevance
semantic similarity
keyword matching

Example:

Python Match: 92%
React Match: 85%
Communication: Medium
Overall Match: 88%
13. Employer ATS Portal
Purpose

Dedicated employer hiring workspace.

URL Namespace:

/employer/*
Planned Pages
Page	Purpose
Dashboard	Hiring overview
My Jobs	Manage job postings
Applications Hub	Review candidates
Candidate Detail	ATS-style candidate screen
Interviews	Schedule and track interviews
Company Profile	Employer branding
Analytics	Hiring metrics
14. Employer Portal Architecture
Employer Dashboard
       │
       ├── My Jobs
       ├── Applications Hub
       ├── Candidate Detail
       ├── Interviews
       ├── Analytics
       └── Company Profile
15. Candidate Detail Screen (ATS Core)

The most important employer page:

/employer/applications/<id>/

Combines:

AI match %
parsed resume
timeline history
pipeline stage
interview management
candidate review

This page acts as the ATS control center.

16. Critical Business Rules
ALWAYS FOLLOW
Email verification required before applying/posting
One application per user/job
Views must stay thin
Business logic belongs in services
Use PipelineService.transition()
Use ApplicationWorkflowService after applying
Timeline events required for major actions
Employers cannot access seeker-only pages
Job seekers cannot access employer pages
17. AI Coding Rules
DO
reuse services
preserve architecture
keep views thin
optimize queries
maintain backward compatibility
use transactions when needed
DO NOT
duplicate business logic
place AI logic in views
rewrite authentication
bypass pipeline validation
directly modify Application.status
create giant functions
18. Current Employer Portal Roadmap
Priority	Feature
High	Employer layout shell
High	Employer sidebar
High	Applications hub
High	Candidate detail page
Medium	Analytics expansion
Medium	Interview calendar
Medium	Celery reminders
Low	REST API
Low	Team recruiters
Low	Subscription billing
19. Known Issues
Issue	Severity
Duplicate navbar on home page	Medium
Bloated requirements.txt	Medium
Missing profile guards in templates	Medium
Salary sorting uses strings	Low
spaCy model not bundled	Low
20. Environment Variables
SECRET_KEY=
DEBUG=
DATABASE_URL=
ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=
EMAIL_BACKEND=
DEFAULT_FROM_EMAIL=
21. Development Commands
Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
Tests
python manage.py test core
python manage.py check
spaCy Setup
python -m spacy download en_core_web_sm
22. Architecture Decisions
Decision	Reason
Single core app	Simpler architecture
Service-oriented backend	Scalability
Thin views	Maintainability
Timeline events	Audit logging
Pipeline validation	Workflow integrity
JSON embedding snapshots	Future ML support
Email verification	Spam prevention
No REST API yet	Faster HTML-first development
23. Future Scalability Plan

Planned future upgrades:

Celery + Redis
semantic embeddings
PostgreSQL optimization
REST API layer
recruiter team accounts
advanced analytics
AI recommendations
vector database support
24. Quick Contributor Checklist
1. Read PROJECT_CONTEXT.md
2. Setup .env
3. Run migrations
4. Start server
5. Verify email flow
6. Apply to job with PDF
7. Test AI parsing
8. Test match scoring
9. Test hiring pipeline
10. Run tests before commit
25. Final Engineering Philosophy

ARTISAN. is designed as:

Public Marketing Site
        +
Job Seeker Platform
        +
Employer ATS Portal
        +
AI Hiring Intelligence Layer

inside a single scalable Django ecosystem.

Primary engineering goals:

scalability
maintainability
AI-ready architecture
reusable workflows
production-grade backend design