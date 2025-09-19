# FundFlow Project Overview

## Project Purpose
FundFlow is an AI-powered automation platform designed to solve manual SALT (State and Local Tax) calculation challenges for Private Equity fund back-office operations. This is a prototype version (v1.2) focused on validating the core workflow of Excel file upload, SALT calculation, and results generation.

**Key Goal**: Validate user experience and data processing workflow with 2-3 test partner clients by Q1 2026.

## Key Features
- **File Upload**: Drag & drop Excel file upload with validation
- **SALT Calculation**: Automated tax calculations using pre-stored EY SALT data
- **Results Dashboard**: Interactive results viewing and management
- **Excel Export**: Download calculation results in Excel format
- **Template System**: Standard portfolio templates for data input
- **User Session Management**: Track uploads and calculations per session

## Target Users
- **Primary**: Tax Directors who need intuitive, fast workflow (e.g., "Sarah Chen")
- **Secondary**: Fund administrators and back-office staff

## Success Metrics
- **Performance**: 30min upload-to-results completion time
- **Accuracy**: 95% Excel format recognition accuracy
- **Concurrency**: Support 3-5 concurrent users
- **Processing**: 30min processing for typical files (~10 portfolios, ~20 LPs)

## Project Status: Prototype v1.2
- ✅ Complete MVP implementation with all core features
- ✅ Backend: 21 Python files with database models, services, and API endpoints
- ✅ Frontend: 15+ React components with Shadcn UI, drag-drop upload, data grids
- ✅ E2E testing: Playwright test suite covering complete upload workflow
- ✅ Docker configuration with healthy containers
- ✅ v1.3 format support with flexible column detection
- ✅ Shared enums for entity types and jurisdictions to ensure data consistency
- 🎯 **Ready for user validation**: Working end-to-end prototype

## Scope & Limitations
### In Scope for v1.2
- Excel file upload and processing (up to 10MB)
- SALT calculation with pre-stored EY data
- Support for ~10 portfolio companies, ~20 LPs
- Basic results dashboard and Excel export

### Out of Scope (Future v1.3+)
- API integrations (NetSuite, Salesforce)
- Real-time data synchronization
- Large-scale processing (50+ portfolios, 100+ LPs)
- SOC 2 security compliance
- Microservices architecture