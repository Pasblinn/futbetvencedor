# Football Analytics - Development Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### One-Command Setup
```bash
./scripts/setup.sh
```

This script will:
- Set up environment files
- Build and start all services
- Run database migrations
- Check service health

## 🏗️ Architecture Overview

### Backend (FastAPI + Python)
- **Location**: `./backend/`
- **Port**: 8000
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for performance optimization
- **APIs**: Integration with Football-Data.org, Odds API, Weather API

### Frontend (React + TypeScript)
- **Location**: `./frontend/`
- **Port**: 3000
- **Framework**: React 18 with TypeScript
- **Styling**: TailwindCSS with custom design system
- **State**: Zustand for state management
- **UI**: Custom components with Lucide icons

### Database
- **PostgreSQL**: Main data storage
- **Redis**: Caching and session management
- **Alembic**: Database migrations

## 📁 Project Structure

```
football-analytics/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   ├── ml/             # Machine learning models
│   │   └── utils/          # Utility functions
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   └── run.py             # Application entry point
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── package.json        # Node dependencies
│   └── tailwind.config.js  # Tailwind configuration
├── shared/                 # Shared types and utilities
├── docs/                   # Documentation
├── scripts/                # Development scripts
└── docker-compose.yml      # Service orchestration
```

## 🛠️ Development Workflow

### Running Services
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Backend Development
```bash
# Access backend container
docker-compose exec backend bash

# Run migrations
python -m alembic upgrade head

# Create new migration
python -m alembic revision --autogenerate -m "description"

# Run tests
pytest

# Format code
black app/
isort app/
```

### Frontend Development
```bash
# Access frontend container
docker-compose exec frontend sh

# Install dependencies
npm install

# Run development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Database Operations
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U football_user -d football_analytics

# View Redis data
docker-compose exec redis redis-cli
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database
POSTGRES_SERVER=postgres
POSTGRES_USER=football_user
POSTGRES_PASSWORD=football_pass
POSTGRES_DB=football_analytics
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379

# API Keys (Required for full functionality)
FOOTBALL_DATA_API_KEY=your_key_here
ODDS_API_KEY=your_key_here
WEATHER_API_KEY=your_key_here

# Security
SECRET_KEY=your_secret_key_here
```

#### Frontend (.env)
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1

# Application
REACT_APP_VERSION=1.0.0
REACT_APP_NAME=Football Analytics
```

## 📊 Key Features Implementation

### 1. Predictive Analysis Engine
- **Location**: `backend/app/services/prediction_service.py`
- **Features**:
  - Team form analysis (last 15 games)
  - Head-to-head analysis
  - Expected Goals (xG) calculations
  - Weather impact assessment
  - Injury factor analysis

### 2. Betting Combinations Generator
- **Location**: `backend/app/services/combination_service.py`
- **Features**:
  - Doubles, trebles, and multiple bets
  - Odds range filtering (1.5-2.0)
  - Correlation analysis
  - Kelly Criterion calculations
  - Risk assessment

### 3. Real-time Data Integration
- **Location**: `backend/app/services/`
- **Features**:
  - Football-Data.org API integration
  - Live odds monitoring
  - Weather condition tracking
  - Automatic data refresh

### 4. Advanced UI Components
- **Location**: `frontend/src/components/`
- **Features**:
  - Responsive dashboard
  - Interactive match cards
  - Combination analysis cards
  - Real-time notifications
  - Dark/light theme support

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_predictions.py
```

### Frontend Testing
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- MatchCard.test.tsx
```

## 📈 Performance Optimization

### Backend
- Redis caching for API responses
- Database query optimization
- Async processing for long-running tasks
- Connection pooling

### Frontend
- Code splitting with React.lazy()
- Memoization for expensive calculations
- Optimized bundle size
- Service worker for caching

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker status
docker ps

# View service logs
docker-compose logs [service_name]

# Restart services
docker-compose restart
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U football_user

# Reset database
docker-compose down -v
docker-compose up -d
```

#### API Key Issues
- Ensure all required API keys are set in `backend/.env`
- Check API key validity and limits
- Monitor API rate limits in logs

#### Frontend Build Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check
```

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints
- `GET /api/v1/matches/today` - Today's matches
- `POST /api/v1/predictions/{match_id}` - Generate prediction
- `GET /api/v1/predictions/combinations/today` - Betting combinations
- `GET /api/v1/analytics/team/{team_id}/form` - Team form analysis

## 🔄 Deployment

### Production Deployment
1. Set up production environment variables
2. Configure SSL certificates
3. Set up reverse proxy (Nginx)
4. Configure monitoring and logging
5. Set up automated backups

### Environment-specific Configurations
- **Development**: Hot reload, debug mode
- **Staging**: Production-like with test data
- **Production**: Optimized, secure, monitored

## 📞 Support

For development support:
1. Check this documentation
2. Review API documentation at http://localhost:8000/docs
3. Check service logs with `docker-compose logs`
4. Review the project's issue tracker

## 🎯 Next Steps

1. **Configure API Keys**: Add your external API keys to `backend/.env`
2. **Customize Predictions**: Modify prediction algorithms in `prediction_service.py`
3. **Add Features**: Extend the UI with additional components
4. **Optimize Performance**: Implement caching strategies
5. **Add Tests**: Increase test coverage for critical components