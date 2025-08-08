Modular Project Structure: LTMCThe AI must generate the project with this exact file and directory structure to enforce modularity and separation of concerns. Each file must adhere to the 300-line limit./ltmc_project/
├── ltms/                           # Main application package
│   ├── api/                        # API Layer
│   │   ├── __init__.py
│   │   ├── endpoints.py            # Defines FastAPI routes and calls services.
│   │   └── dependencies.py         # Common dependencies for routes (e.g., get_db).
│   │
│   ├── core/                       # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py               # Loads settings from .env using Pydantic's BaseSettings.
│   │   └── lifecycle.py            # Manages startup/shutdown events.
│   │
│   ├── database/                   # Data Access Layer for SQLite
│   │   ├── __init__.py
│   │   ├── connection.py           # Manages the SQLite database connection.
│   │   ├── schema.py               # Defines and creates the database tables.
│   │   └── dal.py                  # Data Access Logic: functions for all DB operations.
│   │
│   ├── models/                     # Pydantic models
│   │   ├── __init__.py
│   │   └── schemas.py              # All Pydantic models for API requests/responses.
│   │
│   ├── services/                   # Service Layer
│   │   ├── __init__.py
│   │   ├── embedding_service.py    # Handles text -> vector conversion.
│   │   ├── resource_service.py     # Business logic for adding and managing resources.
│   │   ├── context_service.py      # Business logic for retrieving context.
│   │   └── chunking_service.py     # Logic for splitting text into chunks.
│   │
│   ├── vector_store/               # Data Access Layer for FAISS
│   │   ├── __init__.py
│   │   └── faiss_store.py          # Wrapper for all FAISS index operations (add, search, save, load).
│   │
│   └── main.py                     # Main application entry point.
│
├── .env                            # Environment variables (e.g., MODEL_NAME, DB_PATH).
├── requirements.txt                # Project dependencies.
└── run.py                          # Simple script to start the Uvicorn server.
