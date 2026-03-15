# Keyword Expansion System - Architecture

## System Overview

```mermaid
graph TB
    subgraph Input
        A[Seed Keywords<br/>YAML Config]
    end
    
    subgraph "Keyword Expander"
        B[Main Orchestrator]
        B --> C[DataForSEO Client]
        B --> D[SerpAPI Client]
        B --> E[Google Trends Client]
    end
    
    subgraph "External APIs"
        C --> F[DataForSEO<br/>Autocomplete API]
        D --> G[SerpAPI<br/>PAA + Related]
        E --> H[Google Trends<br/>Rising Queries]
    end
    
    subgraph "Processing Pipeline"
        F --> I[Keyword Collector]
        G --> I
        H --> I
        I --> J[Normalizer]
        J --> K[Deduplicator]
        K --> L[Enrichment Engine]
    end
    
    subgraph Storage
        L --> M[(SQLite DB)]
        M --> N[Query Interface]
    end
    
    subgraph Output
        N --> O[JSON Export]
        N --> P[CSV Export]
        N --> Q[Summary Report]
    end
    
    style A fill:#e3f2fd
    style O fill:#c8e6c9
    style P fill:#c8e6c9
    style Q fill:#c8e6c9
    style B fill:#fff9c4
    style M fill:#f3e5f5
```

---

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Expander
    participant APIs
    participant DB
    
    User->>CLI: python expand_keywords.py
    CLI->>Expander: Load config + seed keywords
    
    loop For each seed keyword
        Expander->>APIs: Request autocomplete
        APIs-->>Expander: Return suggestions
        Expander->>APIs: Request PAA
        APIs-->>Expander: Return questions
        Expander->>APIs: Request trends
        APIs-->>Expander: Return rising queries
    end
    
    Expander->>Expander: Normalize keywords
    Expander->>Expander: Deduplicate
    Expander->>DB: Store keywords
    DB-->>Expander: Confirm write
    Expander->>CLI: Generate output files
    CLI-->>User: Success (400 keywords found)
```

---

## Component Architecture

```mermaid
graph LR
    subgraph "Core Components"
        A[keyword_expander.py<br/>Main Orchestrator]
        B[normalizer.py<br/>Text Processing]
        C[deduplicator.py<br/>Duplicate Removal]
    end
    
    subgraph "API Clients"
        D[dataforseo_client.py]
        E[serpapi_client.py]
        F[trends_client.py]
    end
    
    subgraph "Utilities"
        G[db_manager.py<br/>SQLite Operations]
        H[config_loader.py<br/>YAML Parsing]
        I[logger.py<br/>Logging Setup]
        J[retry_handler.py<br/>Error Recovery]
    end
    
    A --> D
    A --> E
    A --> F
    A --> B
    A --> C
    A --> G
    A --> H
    
    D --> J
    E --> J
    F --> J
    
    G --> I
    
    style A fill:#ffeb3b
    style G fill:#ff9800
```

---

## File Structure

```
SEO_1/
├── config/
│   ├── seed_keywords.yaml       # Input: List of seed keywords
│   └── settings.yaml            # Pipeline configuration
│
├── src/
│   ├── __init__.py
│   ├── keyword_expander.py      # Main orchestrator
│   ├── api_clients/
│   │   ├── __init__.py
│   │   ├── dataforseo_client.py # DataForSEO integration
│   │   ├── serpapi_client.py    # SerpAPI integration
│   │   └── trends_client.py     # Google Trends wrapper
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── normalizer.py        # Keyword normalization
│   │   └── deduplicator.py      # Duplicate detection
│   └── utils/
│       ├── __init__.py
│       ├── db_manager.py        # SQLite operations
│       ├── config_loader.py     # YAML config parser
│       ├── logger.py            # Logging setup
│       └── retry_handler.py     # Retry logic
│
├── output/
│   ├── expanded_keywords.json   # Main output
│   ├── keywords.db              # SQLite database
│   └── summary_report.txt       # Run summary
│
├── tests/
│   ├── test_normalizer.py
│   ├── test_deduplicator.py
│   └── test_api_clients.py
│
├── logs/
│   └── keyword_expansion.log    # Application logs
│
├── .env                         # API keys (NOT in git)
├── .gitignore
├── requirements.txt             # Python dependencies
├── README.md                    # Setup guide
├── todo.md                      # Development checklist
├── implementation_plan.md       # Technical spec
├── architecture.md              # This file
└── expand_keywords.py           # CLI entry point
```

---

## Database Schema

```mermaid
erDiagram
    KEYWORDS {
        int id PK
        string keyword UK
        int search_volume
        string competition
        string source
        string seed_keyword
        datetime discovered_at
        json metadata
    }
    
    RUN_HISTORY {
        int id PK
        datetime run_at
        int keywords_found
        float api_cost
        int runtime_seconds
        string status
    }
    
    API_ERRORS {
        int id PK
        datetime error_at
        string api_name
        string error_message
        string seed_keyword
    }
    
    KEYWORDS ||--o{ RUN_HISTORY : "discovered_in"
    KEYWORDS ||--o{ API_ERRORS : "failed_for"
```

---

## Error Handling Flow

```mermaid
graph TD
    A[API Request] --> B{Success?}
    B -->|Yes| C[Parse Response]
    B -->|No| D{Retry Count < 3?}
    D -->|Yes| E[Wait Exponential Backoff]
    E --> A
    D -->|No| F{Critical API?}
    F -->|Yes| G[Alert User + Halt]
    F -->|No| H[Log Error + Continue]
    C --> I[Process Keywords]
    H --> I
    
    style G fill:#f44336
    style H fill:#ff9800
    style I fill:#4caf50
```

---

## API Rate Limiting Strategy

```mermaid
graph LR
    A[Request Queue] --> B{Rate Limiter}
    B -->|Within Limit| C[Execute Request]
    B -->|Over Limit| D[Sleep 1 Second]
    D --> B
    C --> E[Update Counter]
    E --> F{More Requests?}
    F -->|Yes| A
    F -->|No| G[Complete]
    
    style B fill:#ffeb3b
    style D fill:#ff9800
```

**Rate Limits:**
- DataForSEO: 2000/min → We cap at 50/min (safe margin)
- SerpAPI: 100/hour → We cap at 20/hour
- Google Trends: ~400/hour → We cap at 100/hour + 2s delays

---

## Monitoring Dashboard (Future)

```mermaid
graph TB
    subgraph Metrics
        A[Keywords Found]
        B[API Success Rate]
        C[Cost Per Run]
        D[Runtime]
    end
    
    subgraph Alerts
        E[Zero Keywords Returned]
        F[API Failure Rate >10%]
        G[Cost Exceeds $1]
    end
    
    A --> H[Weekly Email Report]
    B --> H
    C --> H
    D --> H
    
    E --> I[Immediate Email Alert]
    F --> I
    G --> I
    
    style I fill:#f44336
    style H fill:#4caf50
```

---

## Deployment Architecture (Weekly Automation)

```mermaid
graph LR
    A[Cron Job<br/>Every Monday 9am] --> B[expand_keywords.py]
    B --> C[Run Pipeline]
    C --> D{Success?}
    D -->|Yes| E[Update keywords.db]
    D -->|No| F[Send Alert Email]
    E --> G[Export JSON]
    G --> H[Upload to Cloud Storage<br/>Optional]
    F --> I[Retry in 1 Hour]
    
    style A fill:#2196f3
    style E fill:#4caf50
    style F fill:#f44336
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Language** | Python 3.9+ | Core implementation |
| **APIs** | DataForSEO, SerpAPI | Keyword data sources |
| **Database** | SQLite | Keyword storage |
| **Config** | YAML | Configuration files |
| **HTTP** | `requests` | API calls |
| **Trends** | `pytrends` | Google Trends wrapper |
| **Retry** | `tenacity` | Exponential backoff |
| **Logging** | Built-in `logging` | Error tracking |
| **Testing** | `pytest` | Unit/integration tests |
| **CLI** | `argparse` | Command-line interface |

**Total Dependencies:** 6 packages (~15MB)

---

## Security Architecture

```mermaid
graph TD
    A[API Keys] --> B[.env File]
    B --> C[python-dotenv]
    C --> D[Environment Variables]
    D --> E[API Clients]
    
    F[.gitignore] --> B
    
    G[Logs] --> H{Contains Keys?}
    H -->|Yes| I[Redact Before Write]
    H -->|No| J[Write Normally]
    
    style B fill:#f44336
    style F fill:#4caf50
    style I fill:#ff9800
```

**Security Measures:**
1. API keys never hardcoded
2. `.env` file in `.gitignore`
3. Logs redact sensitive data
4. No PII stored in database

---

## Scalability Considerations

**Current Design (Step 1):**
- Handles: 10 seed keywords → 300-500 results
- Runtime: 3-5 minutes
- Storage: ~1MB database

**Future Scale (Steps 2-5):**
- Handles: 50 seeds → 2000+ keywords
- Runtime: 15-20 minutes
- Storage: ~10MB database

**Bottlenecks:**
- API rate limits (solved by throttling)
- SQLite write speed (fine until 100k+ keywords)

**When to Upgrade:**
- If seeds >100 → Switch to PostgreSQL
- If runtime >30 min → Parallelize API calls
- If cost >$10/run → Implement smarter caching

---

This architecture supports the current Step 1 requirements while remaining flexible for Steps 2-5 expansion (intent classification, SERP analysis, clustering, prioritization).
