# BrainSAIT LINC Agent Development Standards

## Code Quality Standards

### Python Standards (Backend)

#### Formatting and Style
- **PEP 8** compliance for all Python code
- **Black** for automatic code formatting (line length: 88)
- **isort** for import organization
- **Flake8** for linting with the following configuration:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = __pycache__, .git, .venv, node_modules
```

#### Type Annotations
- All functions must have type annotations
- Use `from __future__ import annotations` for forward references
- Example:
```python
from __future__ import annotations
from typing import Optional, Dict, List

def process_patient_data(
    patient_id: str, 
    data: Dict[str, Any], 
    options: Optional[List[str]] = None
) -> PatientResponse:
    """Process patient data with validation."""
    ...
```

#### Documentation Standards
- **Google-style docstrings** for all public functions and classes
- Include examples for complex functions
- Document all parameters, returns, and exceptions

```python
def calculate_medication_dosage(
    weight: float, 
    age: int, 
    medication: str
) -> MedicationDosage:
    """Calculate appropriate medication dosage based on patient parameters.
    
    Args:
        weight: Patient weight in kilograms
        age: Patient age in years
        medication: Medication name from approved list
        
    Returns:
        MedicationDosage object with calculated dosage and frequency
        
    Raises:
        ValueError: If weight or age is invalid
        MedicationNotFoundError: If medication is not in approved list
        
    Example:
        >>> dosage = calculate_medication_dosage(70.5, 45, "amoxicillin")
        >>> print(f"{dosage.amount}mg every {dosage.frequency} hours")
    """
```

### TypeScript/JavaScript Standards (Frontend)

#### Formatting and Style
- **ESLint** with TypeScript support
- **Prettier** for code formatting
- **Strict TypeScript** configuration

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

#### Interface Definitions
- All API responses must have TypeScript interfaces
- Use branded types for IDs to prevent mixing

```typescript
type PatientId = string & { readonly brand: unique symbol };
type DoctorId = string & { readonly brand: unique symbol };

interface PatientResponse {
  id: PatientId;
  name: string;
  dateOfBirth: Date;
  medicalRecordNumber: string;
}
```

## Agent Development Framework

### Standard Agent Structure

```
agents/[agent-name]/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Environment configuration
│   │   └── logging.py          # Logging configuration
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   ├── auth.py             # Authentication handlers
│   │   └── [domain].py         # Domain-specific handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py             # Base service class
│   │   └── [domain]_service.py # Business logic services
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base model classes
│   │   ├── requests.py         # Request models
│   │   ├── responses.py        # Response models
│   │   └── database.py         # Database models
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py       # Input validation
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── helpers.py          # Helper functions
│   └── __init__.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
└── README.md
```

### Base Agent Implementation

#### main.py Template
```python
"""[Agent Name] LINC Agent - [Brief Description]"""
from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .config.logging import setup_logging
from .handlers import health, auth
from .utils.exceptions import setup_exception_handlers

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level)
    
    app = FastAPI(
        title=f"{settings.agent_name} LINC Agent",
        description=settings.agent_description,
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
```

#### Base Service Class
```python
"""Base service class for all LINC agents."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Base service class with common functionality."""
    
    def __init__(
        self, 
        db_session: AsyncSession,
        redis_client: Redis,
        settings: Optional[Any] = None
    ):
        self.db = db_session
        self.redis = redis_client
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for this service."""
        try:
            # Check database connectivity
            await self.db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        try:
            # Check Redis connectivity
            await self.redis.ping()
            cache_status = "healthy"
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            cache_status = "unhealthy"
        
        return {
            "service": self.__class__.__name__,
            "database": db_status,
            "cache": cache_status,
            "status": "healthy" if db_status == "healthy" and cache_status == "healthy" else "unhealthy"
        }
    
    @abstractmethod
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service-specific request."""
        pass
```

## Testing Standards

### Unit Testing
- **pytest** with async support
- Minimum 80% code coverage
- Mock external dependencies
- Test both success and failure scenarios

```python
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from ..main import app
from ..services.patient_service import PatientService

@pytest.mark.asyncio
async def test_patient_service_get_patient():
    """Test patient retrieval service."""
    # Arrange
    mock_db = AsyncMock()
    mock_redis = AsyncMock()
    service = PatientService(mock_db, mock_redis)
    
    expected_patient = {
        "id": "patient-123",
        "name": "John Doe",
        "dateOfBirth": "1990-01-01"
    }
    mock_db.execute.return_value.scalar.return_value = expected_patient
    
    # Act
    result = await service.get_patient("patient-123")
    
    # Assert
    assert result == expected_patient
    mock_db.execute.assert_called_once()
```

### Integration Testing
- Test complete request/response cycles
- Use test database and Redis instances
- Test authentication and authorization flows

### Load Testing
- **Locust** for performance testing
- Test concurrent user scenarios
- Validate response times under load

## Security Standards

### Authentication and Authorization
- All endpoints except health checks require authentication
- Use JWT tokens with 15-minute expiration
- Implement refresh token rotation
- Role-based access control (RBAC)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Extract and validate user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return user_id
```

### Data Protection
- Encrypt all PHI fields in database
- Use parameterized queries to prevent SQL injection
- Validate all input data
- Implement rate limiting

### Audit Logging
- Log all data access and modifications
- Include user ID, timestamp, and action
- Structured logging with correlation IDs

```python
import structlog

audit_logger = structlog.get_logger("audit")

async def log_patient_access(user_id: str, patient_id: str, action: str):
    """Log patient data access for audit purposes."""
    audit_logger.info(
        "patient_data_access",
        user_id=user_id,
        patient_id=patient_id,
        action=action,
        timestamp=datetime.utcnow().isoformat(),
        correlation_id=get_correlation_id()
    )
```

## Performance Standards

### Response Time Requirements
- Health checks: < 100ms
- Simple queries: < 500ms
- Complex operations: < 2s
- Bulk operations: < 10s

### Caching Strategy
- Cache frequently accessed data in Redis
- Use appropriate TTL values
- Implement cache invalidation strategies

```python
import json
from typing import Optional

async def get_cached_patient(
    redis_client: Redis, 
    patient_id: str
) -> Optional[Dict[str, Any]]:
    """Get patient data from cache."""
    cache_key = f"patient:{patient_id}"
    cached_data = await redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    return None

async def cache_patient(
    redis_client: Redis, 
    patient_id: str, 
    patient_data: Dict[str, Any],
    ttl: int = 300
) -> None:
    """Cache patient data."""
    cache_key = f"patient:{patient_id}"
    await redis_client.setex(
        cache_key, 
        ttl, 
        json.dumps(patient_data, default=str)
    )
```

## Database Standards

### Schema Design
- Use appropriate data types
- Define foreign key constraints
- Create indexes for frequently queried columns
- Use schemas to organize related tables

### Migration Management
- Use Alembic for database migrations
- Version all schema changes
- Include rollback procedures
- Test migrations on staging environment

### Connection Management
- Use connection pooling
- Implement proper connection lifecycle
- Handle connection failures gracefully

## API Standards

### RESTful Design
- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Implement proper status codes
- Use consistent URL patterns
- Version APIs using URL versioning

### Request/Response Format
- Use JSON for all API communication
- Implement consistent error response format
- Include request validation
- Use pagination for list endpoints

```python
from pydantic import BaseModel
from typing import List, Optional

class PaginatedResponse(BaseModel):
    """Standard pagination response."""
    data: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: str
```

### OpenAPI Documentation
- Use FastAPI automatic documentation
- Include examples for all endpoints
- Document all parameters and responses
- Add authentication requirements

## Deployment Standards

### Docker Configuration
- Use multi-stage builds for optimization
- Include health checks in Dockerfile
- Use non-root user for security
- Minimize image size

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN adduser --disabled-password --gecos '' appuser
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "src.main"]
```

### Environment Configuration
- Use environment variables for all configuration
- Provide sensible defaults
- Validate configuration on startup
- Document all environment variables

## Monitoring and Logging

### Structured Logging
- Use JSON format for all logs
- Include correlation IDs
- Log at appropriate levels
- Avoid logging sensitive data

### Metrics Collection
- Expose Prometheus metrics
- Track response times, error rates, and throughput
- Monitor resource usage
- Set up alerting thresholds

### Health Checks
- Implement comprehensive health checks
- Check database connectivity
- Verify external service dependencies
- Return detailed health status

---

These standards ensure consistency, security, and maintainability across all BrainSAIT LINC agents while supporting the healthcare-grade requirements of the platform.