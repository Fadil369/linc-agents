# BrainSAIT LINC Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

> **Unified BrainSAIT LINC Agent Architecture** - A scalable, modular framework for intelligent healthcare AI agents

## 🏗️ Architecture Overview

The BrainSAIT LINC (Language Intelligence Network Connector) Agent Architecture is a unified framework designed to orchestrate specialized AI agents for healthcare, business, and development operations. This system provides a scalable, secure, and extensible foundation for intelligent agent interactions.

### Key Features

- 🏥 **Healthcare-First Design** - Built for medical environments with HIPAA and Saudi MOH compliance
- 🔒 **Security-Centric** - End-to-end encryption, RBAC, and comprehensive audit logging
- 🚀 **Highly Scalable** - Containerized microservices with Kubernetes orchestration
- 🔧 **Modular & Extensible** - Plugin-based architecture with standardized APIs
- 🌐 **Multi-Language Support** - Arabic and English language processing
- 📊 **Real-time Analytics** - Built-in monitoring, metrics, and business intelligence

## 🎯 Agent Ecosystem

### Core Infrastructure
- **🎯 Master LINC** (`masterlinc:8000`) - Central orchestration and routing hub
- **🔐 Auth LINC** (`authlinc:8001`) - Authentication and authorization service

### Healthcare Agents
- **👨‍⚕️ Doctor LINC** (`doctorlinc:8010`) - Clinical decision support and medical queries
- **👩‍⚕️ Nurse LINC** (`nurslinc:8011`) - Patient care coordination and medication management
- **🏥 Patient LINC** (`patientlinc:8012`) - Patient engagement and health education
- **👥 CareTeam LINC** (`careteamlinc:8013`) - Multi-disciplinary care coordination

### Business Operations
- **📈 Business LINC** (`bizlinc:8020`) - Operational analytics and performance monitoring
- **💳 Payment LINC** (`paylinc:8021`) - Financial transactions and billing automation
- **📊 Insight LINC** (`insightlinc:8022`) - Data analytics and business intelligence

### Development & Automation
- **💻 Dev LINC** (`devlinc:8030`) - Code generation and development workflow automation
- **🤖 Auto LINC** (`autolinc:8031`) - Process automation and workflow orchestration
- **🔍 Code LINC** (`codelinc:8032`) - Code analysis, security scanning, and optimization

### Content & Communication
- **📱 Media LINC** (`medialinc:8040`) - Medical imaging and document management
- **📚 Education LINC** (`edulinc:8041`) - Medical education and training content
- **💬 Chat LINC** (`chatlinc:8042`) - Natural language processing and conversational AI

### Identity & Compliance
- **🆔 OpenID LINC** (`oidlinc:8050`) - Identity federation and compliance reporting

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **Node.js 18+** (for frontend development)
- **Python 3.11+** (for backend development)
- **PostgreSQL 15+** and **Redis 7+** (or use Docker containers)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Fadil369/linc-agents.git
   cd linc-agents
   ```

2. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development environment**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Install dependencies**
   ```bash
   # Backend dependencies
   pip install -r requirements.txt

   # Frontend dependencies
   npm install
   ```

5. **Access the services**
   - Master LINC: http://localhost:8000
   - Auth LINC: http://localhost:8001
   - Web UI: http://localhost:5173 (in development)
   - API Documentation: http://localhost:8000/docs

### Production Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Using Kubernetes
kubectl apply -k infra/kubernetes/

# Deploy web interface to Cloudflare Pages
npm run build
wrangler pages deploy dist/

# Or use the deployment script
npm run deploy:pages
```

> **Note**: This project uses **Cloudflare Pages only** for web hosting. Cloudflare Workers integration has been intentionally excluded to simplify deployment and focus on static site hosting with Pages Functions.

## 📁 Project Structure

```
linc-agents/
├── agents/                     # Individual LINC agents
│   ├── masterlinc/            # Master orchestration agent
│   ├── authlinc/              # Authentication service
│   ├── doctorlinc/            # Doctor agent
│   ├── nurslinc/              # Nurse agent
│   └── ...                    # Other specialized agents
├── shared/                     # Shared libraries and utilities
│   ├── auth/                  # Authentication utilities
│   ├── config/                # Configuration management
│   ├── database/              # Database models and utilities
│   ├── messaging/             # Inter-agent communication
│   ├── models/                # Shared data models
│   ├── monitoring/            # Monitoring and observability
│   └── utils/                 # Common utilities
├── docs/                       # Documentation
│   ├── architecture/          # Architecture documentation
│   ├── api/                   # API documentation
│   ├── deployment/            # Deployment guides
│   └── user-guides/           # User documentation
├── infra/                      # Infrastructure as Code
│   ├── docker/                # Docker configurations
│   ├── kubernetes/            # Kubernetes manifests
│   ├── cloudflare-pages/      # Cloudflare Pages deployment
│   ├── terraform/             # Terraform configurations
│   └── scripts/               # Deployment scripts
├── ui/                         # Web interfaces
│   ├── web/                   # Main web application
│   └── admin/                 # Administrative interface
├── tests/                      # Testing suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── data/                       # Data storage
├── logs/                       # Application logs
├── models/                     # AI/ML models
└── templates/                  # Configuration templates
```

## 🛠️ Development Guide

### Creating a New Agent

1. **Use the agent template**
   ```bash
   cp -r agents/template agents/myagent
   cd agents/myagent
   ```

2. **Update configuration**
   ```python
   # src/config/settings.py
   class Settings(BaseSettings):
       agent_name: str = "My Agent"
       port: int = Field(default=8060, env="MY_AGENT_PORT")
   ```

3. **Implement business logic**
   ```python
   # src/services/my_service.py
   class MyService(BaseService):
       async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
           # Your implementation here
           return {"result": "success"}
   ```

4. **Add tests**
   ```python
   # tests/test_my_service.py
   async def test_my_service():
       # Your tests here
       pass
   ```

### API Development Standards

- **FastAPI** for all HTTP APIs
- **Pydantic** for data validation
- **SQLAlchemy** for database operations
- **Redis** for caching and sessions
- **JWT** for authentication
- **OpenAPI 3.0** for documentation

### Code Quality

```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
pylint src/

# Run tests
pytest tests/

# Type checking
mypy src/
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `JWT_SECRET` | JWT signing secret | Required |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Enable debug mode | `false` |

### Agent-Specific Configuration

Each agent can be configured independently using environment variables:

```bash
# Master LINC
MASTER_LINC_PORT=8000

# Healthcare agents
DOCTOR_LINC_PORT=8010
NURSE_LINC_PORT=8011
PATIENT_LINC_PORT=8012

# Business agents
BIZ_LINC_PORT=8020
PAY_LINC_PORT=8021
```

## 📊 Monitoring and Observability

### Health Checks

All agents expose health check endpoints:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Metrics

Agents expose Prometheus metrics at `/metrics`:

- Request count and duration
- Error rates
- Resource usage
- Business metrics

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "logger": "masterlinc.orchestration",
  "message": "Request routed successfully",
  "correlation_id": "req-123-456",
  "agent": "doctorlinc",
  "endpoint": "/diagnose",
  "duration_ms": 250
}
```

## 🔒 Security

### Authentication Flow

1. User authenticates with Auth LINC
2. JWT token issued with role-based claims
3. Master LINC validates token for each request
4. Request routed to appropriate agent with user context

### Data Protection

- **Encryption at Rest**: AES-256 for sensitive data
- **Encryption in Transit**: TLS 1.3 for all communications
- **Field-Level Encryption**: PHI and PII data encrypted
- **Audit Logging**: All data access logged with user attribution

### Compliance

- **HIPAA Compliance**: Healthcare data protection
- **Saudi MOH Regulations**: Local healthcare compliance
- **GDPR**: European data protection (where applicable)
- **SOC 2 Type II**: Security controls certification

## 🧪 Testing

### Test Types

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Load testing
locust -f tests/load/locustfile.py
```

### Test Coverage

```bash
pytest --cov=src tests/
coverage html  # Generate HTML report
```

## 📚 Documentation

- [📋 Architecture Overview](docs/architecture/ARCHITECTURE.md)
- [🔧 Development Standards](docs/architecture/DEVELOPMENT_STANDARDS.md)
- [📊 System Diagrams](docs/architecture/DIAGRAMS.md)
- [🚀 Deployment Guide](docs/deployment/)
- [📖 API Documentation](docs/api/)
- [👥 User Guides](docs/user-guides/)

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Follow coding standards** (see [Development Standards](docs/architecture/DEVELOPMENT_STANDARDS.md))
4. **Add tests** for new functionality
5. **Commit changes** (`git commit -m 'Add amazing feature'`)
6. **Push to branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Commit Convention

We use [Conventional Commits](https://conventionalcommits.org/):

```
feat: add new patient registration endpoint
fix: resolve authentication token expiration issue
docs: update API documentation
test: add unit tests for orchestration service
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Fadil369/linc-agents/issues)
- **Discord**: [BrainSAIT Community](https://discord.gg/brainsait)
- **Email**: [support@brainsait.io](mailto:support@brainsait.io)

## 🙏 Acknowledgments

- **BrainSAIT Team** - Core development and architecture
- **Healthcare Partners** - Domain expertise and requirements
- **Open Source Community** - Tools and frameworks that make this possible

---

**Built with ❤️ by the BrainSAIT Team for the future of healthcare AI**