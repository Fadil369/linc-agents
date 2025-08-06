# Agent Template

This template provides a standardized structure for creating new LINC agents.

## Quick Start

1. Copy this template to create a new agent:
   ```bash
   cp -r shared/templates/agent agents/mynewagent
   cd agents/mynewagent
   ```

2. Update the configuration files with your agent details

3. Implement your business logic in the services layer

4. Add appropriate tests

5. Update the README with your agent-specific documentation

## Template Structure

```
shared/templates/agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Environment configuration
│   │   └── logging.py          # Logging configuration
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   ├── auth.py             # Authentication handlers
│   │   └── domain.py           # Domain-specific handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py             # Base service class
│   │   └── domain_service.py   # Business logic services
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base model classes
│   │   ├── requests.py         # Request models
│   │   ├── responses.py        # Response models
│   │   └── database.py         # Database models
│   └── utils/
│       ├── __init__.py
│       ├── validators.py       # Input validation
│       ├── exceptions.py       # Custom exceptions
│       └── helpers.py          # Helper functions
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── test_services.py
│   └── integration/
│       └── test_handlers.py
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## Customization Checklist

- [ ] Update `src/config/settings.py` with agent-specific configuration
- [ ] Implement domain-specific handlers in `src/handlers/domain.py`
- [ ] Add business logic in `src/services/domain_service.py`
- [ ] Define data models in `src/models/`
- [ ] Add comprehensive tests in `tests/`
- [ ] Update `Dockerfile` with any agent-specific requirements
- [ ] Document your agent in `README.md`

## Best Practices

1. **Follow the established patterns** from existing agents
2. **Maintain consistency** with the coding standards
3. **Write comprehensive tests** for all functionality
4. **Document your API** using FastAPI's automatic documentation
5. **Implement proper error handling** and logging
6. **Follow security guidelines** for healthcare data
7. **Use type hints** throughout your code