# BrainSAIT LINC Agent System Diagrams

## High-Level System Architecture

```mermaid
graph TB
    subgraph "External Systems"
        EXT1[Saudi MOH API]
        EXT2[NPHIES Platform]
        EXT3[Hospital HIS/EHR]
        EXT4[Third-party APIs]
    end

    subgraph "Load Balancer"
        LB[Nginx/HAProxy]
    end

    subgraph "Core Infrastructure"
        MASTER[Master LINC<br/>Port: 8000]
        AUTH[Auth LINC<br/>Port: 8001]
        DB[(PostgreSQL)]
        CACHE[(Redis)]
        MQ[Message Queue]
    end

    subgraph "Healthcare Agents"
        DOC[Doctor LINC<br/>Port: 8010]
        NURSE[Nurse LINC<br/>Port: 8011]
        PATIENT[Patient LINC<br/>Port: 8012]
        CARE[CareTeam LINC<br/>Port: 8013]
    end

    subgraph "Business Agents"
        BIZ[Business LINC<br/>Port: 8020]
        PAY[Payment LINC<br/>Port: 8021]
        INSIGHT[Insight LINC<br/>Port: 8022]
    end

    subgraph "Development Agents"
        DEV[Dev LINC<br/>Port: 8030]
        AUTO[Auto LINC<br/>Port: 8031]
        CODE[Code LINC<br/>Port: 8032]
    end

    subgraph "Content Agents"
        MEDIA[Media LINC<br/>Port: 8040]
        EDU[Education LINC<br/>Port: 8041]
        CHAT[Chat LINC<br/>Port: 8042]
    end

    subgraph "Identity Agent"
        OID[OpenID LINC<br/>Port: 8050]
    end

    subgraph "Web Interface"
        UI[Web UI<br/>Vite/Alpine.js]
        API[REST/GraphQL APIs]
    end

    subgraph "Mobile Apps"
        MOBILE[Mobile Apps<br/>React Native/Flutter]
    end

    EXT1 & EXT2 & EXT3 & EXT4 --> LB
    UI & MOBILE --> LB
    LB --> MASTER
    
    MASTER --> AUTH
    MASTER --> DOC & NURSE & PATIENT & CARE
    MASTER --> BIZ & PAY & INSIGHT
    MASTER --> DEV & AUTO & CODE
    MASTER --> MEDIA & EDU & CHAT
    MASTER --> OID

    AUTH --> DB
    DOC & NURSE & PATIENT & CARE --> DB
    BIZ & PAY & INSIGHT --> DB
    DEV & AUTO & CODE --> DB
    MEDIA & EDU & CHAT --> DB
    OID --> DB

    MASTER --> MQ
    DOC & NURSE & PATIENT & CARE --> MQ
    BIZ & PAY & INSIGHT --> MQ
    DEV & AUTO & CODE --> MQ
    MEDIA & EDU & CHAT --> MQ

    MASTER --> CACHE
    AUTH --> CACHE
    DOC & NURSE & PATIENT & CARE --> CACHE
```

## Agent Communication Flow

```mermaid
sequenceDiagram
    participant Client
    participant LB as Load Balancer
    participant Master as Master LINC
    participant Auth as Auth LINC
    participant Agent as Specialized Agent
    participant DB as Database
    participant Cache as Redis Cache

    Client->>LB: Request with JWT
    LB->>Master: Route to Master LINC
    Master->>Auth: Validate Token
    Auth->>Cache: Check Session
    Cache-->>Auth: Session Data
    Auth-->>Master: Token Valid
    
    Master->>Agent: Route to Appropriate Agent
    Agent->>DB: Query/Update Data
    DB-->>Agent: Data Response
    Agent->>Cache: Cache Result
    Agent-->>Master: Response
    Master-->>LB: Response
    LB-->>Client: Final Response
```

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Data Sources"
        PHI[Protected Health Info]
        FHIR[FHIR Resources]
        DOCS[Documents/Media]
        LOGS[System Logs]
    end

    subgraph "Data Processing"
        ETL[ETL Pipeline]
        VALID[Data Validation]
        ENCRYPT[Encryption Layer]
    end

    subgraph "Storage Layer"
        PG[(PostgreSQL<br/>Primary Data)]
        REDIS[(Redis<br/>Cache/Sessions)]
        FILES[File Storage<br/>S3/MinIO]
    end

    subgraph "Analytics"
        DW[Data Warehouse]
        BI[Business Intelligence]
        ML[ML Pipeline]
    end

    PHI --> ETL
    FHIR --> ETL
    DOCS --> ETL
    LOGS --> ETL

    ETL --> VALID
    VALID --> ENCRYPT
    ENCRYPT --> PG
    ENCRYPT --> FILES
    
    PG --> REDIS
    PG --> DW
    DW --> BI
    DW --> ML
```

## Security Architecture

```mermaid
graph TB
    subgraph "External Layer"
        WAF[Web Application Firewall]
        DDoS[DDoS Protection]
    end

    subgraph "Authentication Layer"
        MFA[Multi-Factor Auth]
        JWT[JWT Tokens]
        RBAC[Role-Based Access]
    end

    subgraph "Application Layer"
        API[API Gateway]
        AGENTS[LINC Agents]
        AUDIT[Audit Logging]
    end

    subgraph "Data Layer"
        ENC[Field Encryption]
        HASH[Password Hashing]
        BACKUP[Encrypted Backups]
    end

    subgraph "Infrastructure Layer"
        TLS[TLS 1.3]
        VPN[VPN Access]
        FW[Firewall Rules]
    end

    WAF --> MFA
    DDoS --> MFA
    MFA --> JWT
    JWT --> RBAC
    RBAC --> API
    API --> AGENTS
    AGENTS --> AUDIT
    AGENTS --> ENC
    ENC --> HASH
    HASH --> BACKUP
    
    TLS --> API
    VPN --> AGENTS
    FW --> AGENTS
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Kubernetes Cluster"
            subgraph "Master Namespace"
                MASTER_POD[Master LINC Pod]
                AUTH_POD[Auth LINC Pod]
            end
            
            subgraph "Healthcare Namespace"
                DOC_POD[Doctor LINC Pod]
                NURSE_POD[Nurse LINC Pod]
                PATIENT_POD[Patient LINC Pod]
            end
            
            subgraph "Business Namespace"
                BIZ_POD[Business LINC Pod]
                PAY_POD[Payment LINC Pod]
            end
            
            subgraph "Storage"
                PVC[Persistent Volume Claims]
                SECRETS[Kubernetes Secrets]
            end
        end
        
        subgraph "External Services"
            RDS[(AWS RDS PostgreSQL)]
            ELASTICACHE[(AWS ElastiCache Redis)]
            S3[(AWS S3 Storage)]
        end
    end

    subgraph "Monitoring"
        PROM[Prometheus]
        GRAFANA[Grafana]
        ELK[ELK Stack]
    end

    MASTER_POD --> RDS
    AUTH_POD --> RDS
    DOC_POD --> RDS
    NURSE_POD --> ELASTICACHE
    PATIENT_POD --> S3
    
    MASTER_POD --> PROM
    AUTH_POD --> PROM
    DOC_POD --> ELK
```

## Agent Lifecycle Management

```mermaid
stateDiagram-v2
    [*] --> Initializing
    Initializing --> Registering
    Registering --> HealthCheck
    HealthCheck --> Ready
    Ready --> Processing
    Processing --> Ready
    Ready --> Scaling
    Scaling --> Ready
    Ready --> Maintenance
    Maintenance --> Ready
    Ready --> Shutting_Down
    Processing --> Error
    Error --> Recovering
    Recovering --> Ready
    Recovering --> Failed
    Failed --> [*]
    Shutting_Down --> [*]
    
    note right of Initializing
        Load configuration
        Initialize dependencies
    end note
    
    note right of Registering
        Register with Master LINC
        Announce capabilities
    end note
    
    note right of HealthCheck
        Database connectivity
        External service checks
    end note
```