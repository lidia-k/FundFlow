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
│   ├── app/                    # FastAPI app configuration
│   ├── src/                    # Source code (main implementation)
│   │   ├── api/                # API routes (upload, results, SALT rules)
│   │   ├── database/           # Database connection and setup
│   │   ├── models/             # Data models (11 models)
│   │   └── services/           # Business logic (11 services)
│   ├── tests/                  # Backend tests (pytest)
│   ├── alembic/                # Database migrations
│   ├── requirements.txt        # Python dependencies
│   └── pyproject.toml          # Python project configuration
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components (18+ components)
│   │   │   └── ui/             # Shadcn UI components
│   │   ├── pages/              # Page components (Upload, Dashboard)
│   │   ├── api/                # API client utilities
│   │   ├── hooks/              # Custom React hooks
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Frontend utility functions
│   ├── tests/                  # Frontend tests (Jest + Playwright)
│   │   ├── e2e/                # End-to-end tests
│   │   └── fixtures/           # Test data and fixtures
│   ├── public/                 # Static assets
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
- **Backend**: Python 3.11 + FastAPI + SQLite + SQLAlchemy ORM
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Shadcn UI
- **File Processing**: pandas + openpyxl for Excel handling
- **Tax Engine**: Custom SALT rule processor with validation
- **Testing**: pytest + Jest + Playwright for comprehensive coverage
- **Development**: Docker + Docker Compose with hot reload

### Key Features
- **File Upload**: Drag & drop Excel file upload with validation
- **SALT Rule Management**: Complete tax rule lifecycle management
- **Tax Calculation Engine**: Automated withholding and composite tax calculations
- **Results Dashboard**: Modal-based interactive results viewing
- **Audit Reporting**: Detailed CSV reports for compliance
- **Excel Export**: Download calculation results and templates
- **Template System**: Dynamic v1.3 format portfolio templates

## 📊 API Endpoints

### Core Upload & Results
- `POST /api/upload` - Upload portfolio Excel file
- `GET /api/results/{session_id}` - Get calculation results
- `GET /api/results/{session_id}/preview` - Preview results with tax calculations
- `GET /api/results/{session_id}/download` - Download results
- `GET /api/results/{session_id}/report` - Download detailed audit report (CSV)
- `GET /api/template` - Download portfolio template
- `GET /api/sessions` - List all sessions

### SALT Rule Management
- `POST /api/salt-rules/upload` - Upload SALT rule workbooks
- `GET /api/salt-rules` - List rule sets with filtering
- `GET /api/salt-rules/{id}` - Get detailed rule set information
- `GET /api/salt-rules/{id}/validation` - Get validation results
- `GET /api/salt-rules/{id}/preview` - Preview rule changes
- `GET /api/salt-rules/template` - Download SALT rules template

### System
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

## 📈 Current Status: v1.2.1 - Epic 2A/2B Complete

This version includes **production-ready tax processing** with:

- ✅ Complete SALT rule management system (Epic 2A)
- ✅ Automated tax calculation engine (Epic 2B)
- ✅ Advanced results dashboard with modal workflow
- ✅ Comprehensive audit reporting
- ✅ Enhanced Excel template system (v1.3 format)
- 🎯 Ready for production deployment and user testing

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

**Version**: 1.2.1 (Epic 2A/2B Complete)  
**Last Updated**: September 21, 2025