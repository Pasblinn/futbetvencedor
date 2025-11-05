# Football Analytics - Advanced Predictive System

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 Overview

Advanced predictive analytics system for football betting analysis designed for **educational and analytical purposes only**. The system achieves a target reliability of ~95% through rigorous statistical analysis, machine learning models, and real-time validation.

**⚠️ IMPORTANT DISCLAIMER**: This application is purely for educational, research, and analytical purposes. It is not intended for commercial gambling activities or real money betting. Please gamble responsibly and within legal frameworks.

## ✨ Key Features

### 🧠 Advanced Prediction Engine
- **Form Analysis**: Comprehensive team performance analysis over last 15 games
- **Head-to-Head Analysis**: Historical match data and patterns
- **Expected Goals (xG)**: Advanced metrics including xG, xGA, possession, shots
- **Weather Impact**: Real-time weather condition analysis and impact assessment
- **Injury Factor**: Player availability and impact calculations
- **Referee Analysis**: Official statistics and tendencies

### 🎲 Intelligent Combination Generator
- **Smart Combinations**: Automated generation of doubles, trebles, and multiples
- **Odds Optimization**: Target range of 1.5-2.0 odds with high probability
- **Risk Assessment**: Comprehensive risk analysis and correlation checking
- **Kelly Criterion**: Optimal stake calculations using modified Kelly Criterion
- **Value Detection**: Identification of value bets through probability vs. odds analysis

### 📊 Real-time Analytics
- **Live Odds Monitoring**: Real-time odds tracking and movement analysis
- **Performance Tracking**: ROI and win rate monitoring with detailed statistics
- **Backtesting**: Historical performance validation
- **Monte Carlo Simulations**: Probability calculations using advanced statistical methods

### 🎨 Modern User Interface
- **Responsive Design**: Modern, clean interface with dark/light theme support
- **Interactive Dashboard**: Real-time data visualization and insights
- **Mobile Optimized**: Fully responsive across all device sizes
- **Professional UI**: Clean design with advanced data visualization

## 🏗️ Architecture

### Backend (Python FastAPI)
- **High Performance**: Async FastAPI with automatic API documentation
- **Advanced Analytics**: Sophisticated prediction algorithms and statistical analysis
- **Real-time Data**: Integration with multiple football data sources
- **Caching**: Redis-based caching for optimal performance
- **Database**: PostgreSQL with SQLAlchemy ORM

### Frontend (React + TypeScript)
- **Modern Stack**: React 18 with TypeScript for type safety
- **State Management**: Zustand for efficient state management
- **UI Framework**: TailwindCSS with custom design system
- **Data Visualization**: Interactive charts and graphs
- **Real-time Updates**: Live data updates and notifications

## 🚀 Quick Start

### Clone the Repository
```bash
git clone https://github.com/Pasblinn/futbetvencedor.git
cd futbetvencedor
```

### Setup Environment
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your API keys
# See Configuration section below for details

# 3. Start services with Docker (recommended)
docker-compose up -d --build

# Wait for services to initialize (about 30 seconds)
# Visit http://localhost:3000 for the application
# Visit http://localhost:8000/docs for API documentation
```

### Alternative: Manual Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm start
```

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for local development)
- **PostgreSQL 15+** (if running locally)
- **Redis** (if running locally)

## 🔧 Configuration

### Setting Up API Keys

**IMPORTANT**: Never commit your `.env` file with real API keys to Git! The repository includes a `.env.example` template.

#### Step 1: Copy the Template
```bash
# In the project root
cp .env.example .env
```

#### Step 2: Get Your API Keys

1. **Football-Data.org API** (Required)
   - Register at: https://www.football-data.org/client/register
   - Free tier: 10 calls/minute, 12 major competitions
   - Copy your API key

2. **API-Sports (API-Football)** (Required)
   - Register at: https://v3.football.api-sports.io
   - Free tier: 100 requests/day
   - This is the main data source for ML

3. **The Odds API** (Optional)
   - Register at: https://the-odds-api.com/
   - Free tier: 500 requests/month

4. **OpenWeatherMap API** (Optional)
   - Register at: https://openweathermap.org/api
   - Free tier: 1000 calls/day

#### Step 3: Configure Your `.env` File
```bash
# Edit the .env file and add your keys:
FOOTBALL_DATA_API_KEY=your_real_key_here
API_SPORTS_KEY=your_real_key_here
ODDS_API_KEY=your_real_key_here
WEATHER_API_KEY=your_real_key_here  # Optional
```

#### Security Notes
- ✅ The `.env` file is in `.gitignore` and will NOT be pushed to GitHub
- ✅ All hardcoded API keys have been removed from the codebase
- ✅ Use `.env.example` as a reference for required variables
- ⚠️ Never share your `.env` file or API keys publicly

## 📊 System Capabilities

### Prediction Accuracy
- **Overall Target**: 95% reliability on recommended bets
- **Market Coverage**: 1X2, Over/Under, BTTS, Corners, Asian Handicap
- **Data Sources**: 15+ statistical metrics per team
- **Real-time Validation**: Continuous odds monitoring and lineup verification

### Supported Markets
- **Match Outcomes**: 1X2 predictions with confidence scoring
- **Goals Markets**: Over/Under 1.5, 2.5, 3.5 with Poisson distribution
- **Both Teams to Score**: Advanced probability calculations
- **Corner Markets**: Detailed corner analysis and predictions
- **Custom Markets**: Extensible framework for additional markets

### Performance Metrics
- **Backtesting**: Historical performance validation
- **ROI Tracking**: Return on investment calculations
- **Win Rate Analysis**: Detailed success rate tracking
- **Risk Assessment**: Comprehensive risk evaluation

## 🛠️ Development

For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md).

### Project Structure
```
football-analytics/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── ml/             # Machine learning models
│   └── alembic/            # Database migrations
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API integration
│   │   ├── store/          # State management
│   │   └── types/          # TypeScript definitions
├── shared/                 # Shared utilities
├── docs/                   # Documentation
└── scripts/                # Development scripts
```

### Available Commands
```bash
# Development
docker-compose up -d          # Start all services
docker-compose logs -f        # View logs
docker-compose down           # Stop services

# Backend
docker-compose exec backend bash                    # Access backend shell
docker-compose exec backend python -m pytest       # Run tests
docker-compose exec backend python -m alembic upgrade head  # Run migrations

# Frontend
docker-compose exec frontend sh         # Access frontend shell
docker-compose exec frontend npm test   # Run tests
docker-compose exec frontend npm run build  # Build for production
```

## 📈 Performance Features

### Optimization
- **Caching Strategy**: Multi-layer caching with Redis
- **Database Optimization**: Efficient queries with proper indexing
- **API Rate Limiting**: Smart rate limiting to prevent API exhaustion
- **Async Processing**: Non-blocking operations for better performance

### Monitoring
- **Health Checks**: Automated service health monitoring
- **Performance Metrics**: Response time and throughput tracking
- **Error Logging**: Comprehensive error tracking and logging
- **API Monitoring**: External API usage and rate limit monitoring

## 🧪 Testing

### Backend Testing
```bash
# Run all tests
docker-compose exec backend python -m pytest

# Run with coverage
docker-compose exec backend python -m pytest --cov=app

# Run specific tests
docker-compose exec backend python -m pytest tests/test_predictions.py -v
```

### Frontend Testing
```bash
# Run all tests
docker-compose exec frontend npm test

# Run with coverage
docker-compose exec frontend npm test -- --coverage

# Type checking
docker-compose exec frontend npm run type-check
```

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Development Guide**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **API Reference**: http://localhost:8000/redoc (when running)

## 🚨 Important Notes

### Educational Purpose
This system is designed for:
- ✅ Learning about sports analytics and prediction algorithms
- ✅ Understanding statistical analysis and probability calculations
- ✅ Exploring modern web development practices
- ✅ Research into sports data analysis techniques

### Not Intended For
- ❌ Commercial gambling operations
- ❌ Real money betting advice
- ❌ Guaranteed profit systems
- ❌ Replacement for professional gambling advice

### Responsible Use
- Always gamble responsibly and within your means
- Be aware of gambling laws in your jurisdiction
- Understand that no prediction system is 100% accurate
- Use the system for educational and analytical purposes only

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Football-Data.org for comprehensive football data
- The Odds API for real-time betting odds
- OpenWeatherMap for weather data
- The open-source community for amazing tools and libraries

---

**Remember**: This tool is for educational and analytical purposes only. Always gamble responsibly and within legal frameworks. Past performance does not guarantee future results.