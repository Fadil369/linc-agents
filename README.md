# BrainSAIT LINC Agent Architecture - Quick Start Guide

## Overview
This is a unified AI-powered healthcare platform for Saudi Arabia featuring 16 specialized LINC (Language-Integrated, Intelligent, Networked, and Contextual) agents.

## Quick Deployment

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM recommended
- Ports 3000, 5432, 6379, 8000-8010 available

### 1. Clone and Setup
```bash
git clone https://github.com/Fadil369/linc-agents.git
cd linc-agents
cp .env.example .env
```

### 2. Start the Platform
```bash
# Start all services
docker compose -f docker-compose.dev.yml up -d

# Check service status
docker compose -f docker-compose.dev.yml ps

# View logs
docker compose -f docker-compose.dev.yml logs -f
```

### 3. Access the Platform
- **Web Interface:** http://localhost:3000
- **MasterLINC API:** http://localhost:8000/docs
- **AuthLINC API:** http://localhost:8001/docs
- **DoctorLINC API:** http://localhost:8010/docs

## Core Services

### MasterLINC (Port 8000)
Central orchestration hub that:
- Routes user requests to appropriate agents
- Coordinates workflows across agents
- Monitors system health and metrics
- Manages agent registry

### AuthLINC (Port 8001)
Security gateway providing:
- User registration and authentication
- JWT token management
- Role-based access control
- Session management

### DoctorLINC (Port 8010)
Healthcare agent offering:
- Clinical note processing
- SOAP note generation
- Prescription management
- Diagnostic assistance
- FHIR resource creation

## Testing the System

### 1. Register a User
```bash
curl -X POST "http://localhost:8001/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor1",
    "email": "doctor@example.com",
    "password": "password123",
    "full_name": "Dr. Ahmed Ali",
    "arabic_name": "د. أحمد علي",
    "role": "doctor",
    "preferred_language": "ar"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor1",
    "password": "password123",
    "agent_name": "web"
  }'
```

### 3. Check Agent Status
```bash
curl "http://localhost:8000/agents"
```

### 4. Route a Workflow
```bash
curl -X POST "http://localhost:8000/workflow/route" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "user_intent": "I need to see a doctor about my headache",
    "preferred_language": "en",
    "priority": "normal"
  }'
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │    MasterLINC   │    │    AuthLINC     │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 8001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   DoctorLINC    │
                    │   (Port 8010)   │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   PostgreSQL    │    │     Redis       │
                    │   (Port 5432)   │    │   (Port 6379)   │
                    └─────────────────┘    └─────────────────┘
```

## Development

### Running Tests
```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests
python -m pytest tests/unit/ -v

# Run specific test
python -m pytest tests/unit/test_masterlinc.py::test_health_check -v
```

### Development Setup
```bash
# Setup development environment
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh

# Install Node dependencies for UI
npm install

# Run individual agent
cd agents/masterlinc
python main.py
```

## Configuration

### Environment Variables
Key variables in `.env`:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: JWT signing secret
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `ENVIRONMENT`: development/production

### Database
The system automatically creates:
- User accounts and sessions
- Agent registry and status
- Conversation history
- Healthcare records (FHIR compatible)
- System events and audit logs

## Features Implemented

### ✅ Core Infrastructure
- FastAPI-based microservices
- PostgreSQL database with SQLAlchemy
- Redis for caching and messaging
- JWT authentication
- Docker containerization

### ✅ Healthcare Capabilities
- FHIR-compatible data models
- Clinical note processing
- Prescription management
- Diagnostic assistance
- Arabic/English language support

### ✅ Web Interface
- Responsive design with Arabic RTL support
- Real-time agent communication
- Multi-language UI
- Agent selection and chat interface

## Next Steps

### Additional Agents (Framework Ready)
- NurseLINC: Nursing workflow automation
- PatientLINC: Patient experience navigation
- BizLINC: Healthcare business intelligence
- PayLINC: Payment processing
- ChatLINC: Multilingual communication hub

### Enhanced Features
- Voice processing with Whisper
- AI-powered clinical insights
- Saudi regulatory compliance (NPHIES)
- Mobile applications
- Advanced analytics

## Support

For issues and development:
- Check logs: `docker compose logs [service_name]`
- Health checks: `curl http://localhost:8000/health`
- API documentation: Available at `/docs` endpoints
- Database access: Connect to PostgreSQL on port 5432

## Security Notes

**Development Environment:**
- Default passwords and secrets are used
- Ports are exposed for testing
- Debug mode enabled

**Production Deployment:**
- Change all default passwords
- Use environment-specific secrets
- Enable HTTPS/TLS
- Configure firewall rules
- Set up monitoring and backups