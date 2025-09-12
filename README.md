# FundFlow

**AI-Powered PE Back-Office Automation Platform**

FundFlow is designed to automate SALT (State and Local Tax) calculations for Private Equity fund back-office operations, eliminating manual processes and reducing error risks.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. **Clone and Setup**
   ```bash
   git clone <your-repo-url>
   cd FundFlow
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

2. **Start Development Environment**
   ```bash
   # With Docker (Recommended)
   make dev
   # or
   docker-compose up --build

   # Local Development
   make dev-local
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

## 📁 Project Structure

```
FundFlow/
├── README.md                    # This file
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/                # API routes
│   │   ├── core/               # Configuration
│   │   ├── models/             # Data models
│   │   ├── services/           # Business logic
│   │   └── utils/              # Utilities
│   ├── tests/                  # Backend tests
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── api/                # API client
│   │   ├── types/              # TypeScript types
│   │   └── utils/              # Utilities
│   └── package.json            # Node.js dependencies
├── docker/                     # Docker configurations
├── scripts/                    # Setup and utility scripts
├── data/                       # Data storage
│   ├── uploads/                # Uploaded files
│   ├── results/                # Calculation results
│   └── templates/              # Excel templates
├── logs/                       # Application logs
└── docs/                       # Documentation
```

## 🛠 Available Commands

### Development
```bash
make dev           # Start with Docker
make dev-local     # Start locally
make setup         # Initial setup
```

### Building & Testing
```bash
make build         # Build application
make test          # Run all tests
make lint          # Run linters
make type-check    # TypeScript type checking
```

### Docker Operations
```bash
make docker-build  # Build Docker images
make docker-up     # Start containers
make docker-down   # Stop containers
make docker-logs   # View logs
```

### Database
```bash
make db-migrate    # Run migrations
make db-seed       # Seed with sample data
```

## 🏗 Architecture

### Tech Stack
- **Backend**: Python 3.11 + FastAPI + SQLite
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **File Processing**: pandas + openpyxl
- **Development**: Docker + Docker Compose

### Key Features
- **File Upload**: Drag & drop Excel file upload
- **SALT Calculation**: Automated tax calculations
- **Results Dashboard**: Interactive results viewing
- **Excel Export**: Download calculation results
- **Template System**: Standard portfolio templates

## 📊 API Endpoints

- `POST /api/upload` - Upload portfolio Excel file
- `GET /api/results/{session_id}` - Get calculation results
- `GET /api/results/{session_id}/download` - Download results
- `GET /api/template` - Download portfolio template
- `GET /api/sessions` - List all sessions
- `GET /health` - Health check

## 🔧 Configuration

### Backend (.env)
```env
DATABASE_URL=sqlite:///./data/fundflow.db
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
MAX_UPLOAD_SIZE=10485760
```

### Frontend
- API proxy configured in `vite.config.ts`
- Environment variables in `.env` files

## 📝 Development Workflow

1. **Feature Development**
   - Create feature branch
   - Make changes
   - Run tests: `make test`
   - Run linting: `make lint`

2. **Code Quality**
   - Pre-commit hooks automatically format code
   - TypeScript strict mode enabled
   - Comprehensive error handling

## 🐳 Docker Development

The project includes a complete Docker development environment:

- **Multi-stage builds** for optimization
- **Volume mounting** for live reload
- **Health checks** for containers
- **Network isolation** between services

## 📈 Current Status: Prototype v1.2

This is a **prototype version** focused on:

- ✅ Core SALT calculation workflow
- ✅ File upload and processing
- ✅ Basic results dashboard
- ✅ Excel template system
- ⏳ User testing with partners

### Limitations (Prototype)
- SQLite database (single instance)
- Synchronous processing
- Basic security (file-based sessions)
- Limited to 10MB files, ~20 LPs

## 🚀 Future Roadmap (v1.3+)

- **Database**: PostgreSQL with replication
- **Architecture**: Microservices
- **API Integrations**: NetSuite, Salesforce
- **Security**: SOC 2 compliance
- **Performance**: Async processing, caching
- **Analytics**: Advanced dashboards

## 🤝 Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation
4. Use pre-commit hooks

## 📚 Documentation

- **API Docs**: http://localhost:8000/api/docs (when running)
- **Technical Design**: `docs/TDD/`
- **Product Requirements**: `docs/PRD/`

---

**Version**: 1.2.0 (Prototype)  
**Last Updated**: September 12, 2025