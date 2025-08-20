# VoiceVibe Backend - Django REST API

## 🎯 Overview

VoiceVibe is an AI-powered language learning platform specifically designed to help Indonesian learners improve their English speaking skills. This Django backend provides comprehensive REST APIs for mobile and web applications, featuring real-time audio processing, AI-driven evaluations, and culturally-responsive gamification.

## 🚀 Features

### Core Functionality
- **AI-Powered Speech Evaluation**: Integration with OpenAI/Anthropic for phonetic, sequential, and pragmatic analysis
- **Real-time Audio Processing**: WebSocket support for live audio streaming and transcription
- **Adaptive Learning Paths**: Personalized curriculum based on proficiency levels (A1-C2)
- **Cultural Adaptation**: Indonesian-specific content and scenarios
- **Gamification System**: Culturally-responsive rewards based on Hofstede's dimensions
- **Comprehensive Analytics**: Detailed tracking of user progress and performance metrics

### Technical Features
- JWT-based authentication with refresh tokens
- WebSocket connections for real-time features
- Celery for async task processing
- Redis for caching and session management
- PostgreSQL for robust data storage
- API documentation with Swagger/ReDoc

## 📁 Project Structure

```
VoiceVibe-backend-django/
├── apps/                      # Django applications
│   ├── authentication/        # JWT auth & user registration
│   ├── users/                # User profiles & management
│   ├── learning_paths/       # Adaptive curriculum system
│   ├── speaking_sessions/    # Audio recording & WebSocket
│   ├── ai_evaluation/        # AI-powered assessment
│   ├── gamification/         # Points, badges, leaderboards
│   ├── cultural_adaptation/  # Indonesian cultural content
│   └── analytics/            # Performance tracking
├── core/                     # Project configuration
│   ├── settings/            # Environment-specific settings
│   │   ├── base.py         # Common settings
│   │   ├── development.py   # Dev environment
│   │   └── production.py    # Production settings
│   ├── urls.py             # Main URL configuration
│   ├── wsgi.py            # WSGI application
│   └── asgi.py            # ASGI for WebSockets
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend development)

### Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/voicevibe-backend.git
cd voicevibe-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Configure PostgreSQL**
```sql
CREATE DATABASE voicevibe_db;
CREATE USER voicevibe_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE voicevibe_db TO voicevibe_user;
```

6. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create superuser**
```bash
python manage.py createsuperuser
```

8. **Collect static files**
```bash
python manage.py collectstatic
```

9. **Start development server**
```bash
python manage.py runserver
```

For WebSocket support:
```bash
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

## 📝 API Documentation

### Base URL
```
Development: http://localhost:8000/api/v1/
Production: https://api.voicevibe.com/api/v1/
```

### Authentication
All API endpoints require JWT authentication except for registration and login.

```http
Authorization: Bearer <access_token>
```

### Main Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| Auth | `/auth/` | Login, register, refresh tokens |
| Users | `/users/` | User profiles, preferences |
| Learning | `/learning/` | Learning paths, modules, lessons |
| Sessions | `/sessions/` | Speaking practice sessions |
| Evaluation | `/evaluate/` | AI-powered assessments |
| Gamification | `/gamification/` | Points, badges, leaderboards |
| Cultural | `/cultural/` | Cultural scenarios and content |
| Analytics | `/analytics/` | Progress tracking and insights |

### Interactive Documentation
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## 🧪 Testing

Run the test suite:
```bash
pytest
```

With coverage:
```bash
pytest --cov=apps --cov-report=html
```

## 🚀 Deployment

### Production Configuration

1. **Update settings**
```python
# core/settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['api.voicevibe.com']
```

2. **Use Gunicorn**
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

3. **Configure Nginx**
```nginx
server {
    listen 80;
    server_name api.voicevibe.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔧 Environment Variables

Key environment variables (see `.env.example`):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=voicevibe_db
DB_USER=voicevibe_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# JWT
ACCESS_TOKEN_LIFETIME=15
REFRESH_TOKEN_LIFETIME=7
```

## 📊 Database Schema

### Key Models

- **User**: Extended Django user with language preferences
- **UserProfile**: Additional user information and settings
- **LearningPath**: Personalized curriculum for each user
- **SpeakingSession**: Audio recordings and practice sessions
- **AIEvaluation**: AI-generated feedback and scores
- **Achievement**: Gamification badges and rewards
- **CulturalScenario**: Indonesian-specific content
- **Analytics**: Performance metrics and insights

## 🔄 WebSocket Events

### Session Events
- `session.start`: Begin recording session
- `session.audio`: Stream audio chunks
- `session.end`: Complete recording
- `session.feedback`: Receive AI evaluation

### Real-time Updates
- `achievement.unlocked`: New badge earned
- `leaderboard.update`: Position changes
- `progress.milestone`: Learning goal reached

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- Backend Lead: [Your Name]
- AI Integration: [Team Member]
- DevOps: [Team Member]

## 📧 Contact

For questions or support, please contact:
- Email: support@voicevibe.com
- Discord: [VoiceVibe Community](https://discord.gg/voicevibe)

## 🎯 Roadmap

### Phase 1 (Completed) ✅
- Core authentication system
- User management
- Basic learning paths
- Speaking session recording

### Phase 2 (Current) 🚧
- AI evaluation integration
- Gamification features
- Cultural adaptation
- Analytics dashboard

### Phase 3 (Upcoming) 📅
- Social features
- Peer learning
- Advanced analytics
- Mobile optimization

---

**Built with ❤️ for Indonesian English learners**
