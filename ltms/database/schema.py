"""Database schema module for LTMC."""

import sqlite3


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables if they don't exist.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    # Create Resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Create ResourceChunks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ResourceChunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER,
            chunk_text TEXT NOT NULL,
            vector_id INTEGER UNIQUE NOT NULL,
            FOREIGN KEY (resource_id) REFERENCES Resources (id)
        )
    """)
    
    # Create ChatHistory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ChatHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            agent_name TEXT,
            metadata TEXT,
            source_tool TEXT
        )
    """)
    
    # Create ContextLinks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ContextLinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            chunk_id INTEGER,
            FOREIGN KEY (message_id) REFERENCES ChatHistory (id),
            FOREIGN KEY (chunk_id) REFERENCES ResourceChunks (id)
        )
    """)

    # Create Summaries table (for auto-summary ingestion)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER,
            doc_id TEXT,
            summary_text TEXT NOT NULL,
            model TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (resource_id) REFERENCES Resources (id)
        )
    """)
    
    # Create todos table (lowercase to match code expectations)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            completed BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)
    
    # Create CodePatterns table for code pattern learning
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CodePatterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            function_name TEXT,
            file_name TEXT,
            module_name TEXT,
            input_prompt TEXT NOT NULL,
            generated_code TEXT NOT NULL,
            result TEXT CHECK(result IN ('pass', 'fail', 'partial')) NOT NULL,
            execution_time_ms INTEGER,
            error_message TEXT,
            tags TEXT,
            created_at TEXT NOT NULL,
            vector_id INTEGER UNIQUE,
            FOREIGN KEY (vector_id) REFERENCES ResourceChunks (id)
        )
    """)
    
    # Create CodePatternContext table for additional context
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CodePatternContext (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_id INTEGER,
            context_type TEXT NOT NULL,
            context_data TEXT NOT NULL,
            FOREIGN KEY (pattern_id) REFERENCES CodePatterns (id)
        )
    """)
    
    # Create VectorIdSequence table for managing vector IDs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS VectorIdSequence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_vector_id INTEGER DEFAULT 0
        )
    """)
    
    # Initialize vector ID sequence if empty
    cursor.execute("INSERT OR IGNORE INTO VectorIdSequence (id, last_vector_id) VALUES (1, 0)")

    # =====================================
    # ADVANCED ML & ORCHESTRATION TABLES
    # =====================================
    
    # Create TaskBlueprints table for blueprint management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TaskBlueprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blueprint_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            complexity TEXT NOT NULL,
            complexity_score REAL NOT NULL,
            project_id TEXT,
            estimated_duration_minutes INTEGER DEFAULT 30,
            required_skills TEXT,  -- JSON array
            priority_score REAL DEFAULT 0.5,
            resource_requirements TEXT,  -- JSON object
            tags TEXT,  -- JSON array
            status TEXT DEFAULT 'draft',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create TaskDependencies table for dependency management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TaskDependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dependent_blueprint_id TEXT NOT NULL,
            prerequisite_blueprint_id TEXT NOT NULL,
            dependency_type TEXT DEFAULT 'blocking',
            is_critical BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (dependent_blueprint_id) REFERENCES TaskBlueprints (blueprint_id),
            FOREIGN KEY (prerequisite_blueprint_id) REFERENCES TaskBlueprints (blueprint_id),
            UNIQUE(dependent_blueprint_id, prerequisite_blueprint_id)
        )
    """)
    
    # Create TeamMembers table for team assignment
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TeamMembers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            skills TEXT,  -- JSON array
            capacity REAL DEFAULT 1.0,
            current_workload REAL DEFAULT 0.0,
            availability_status TEXT DEFAULT 'available',
            project_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create TaskAssignments table for task assignment tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TaskAssignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT UNIQUE NOT NULL,
            blueprint_id TEXT NOT NULL,
            member_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            assigned_at TEXT NOT NULL,
            status TEXT DEFAULT 'assigned',
            progress_percentage REAL DEFAULT 0.0,
            actual_hours_worked REAL DEFAULT 0.0,
            notes TEXT,
            completed_at TEXT,
            FOREIGN KEY (blueprint_id) REFERENCES TaskBlueprints (blueprint_id),
            FOREIGN KEY (member_id) REFERENCES TeamMembers (member_id)
        )
    """)
    
    # Create DocumentationSync table for documentation synchronization
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DocumentationSync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_id TEXT UNIQUE NOT NULL,
            file_path TEXT NOT NULL,
            project_id TEXT NOT NULL,
            sync_type TEXT NOT NULL,  -- 'code_to_docs', 'docs_to_code', 'bidirectional'
            consistency_score REAL,
            last_sync_at TEXT NOT NULL,
            drift_detected BOOLEAN DEFAULT 0,
            auto_sync_enabled BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create BlueprintCodeLinks table for blueprint-code relationships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS BlueprintCodeLinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blueprint_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            project_id TEXT NOT NULL,
            link_type TEXT NOT NULL,  -- 'implements', 'defines', 'uses'
            consistency_status TEXT DEFAULT 'unknown',
            last_validated_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (blueprint_id) REFERENCES TaskBlueprints (blueprint_id)
        )
    """)
    
    # Create RealtimeSync table for real-time file monitoring
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RealtimeSync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_session_id TEXT UNIQUE NOT NULL,
            project_id TEXT NOT NULL,
            monitored_paths TEXT NOT NULL,  -- JSON array
            sync_status TEXT DEFAULT 'active',
            last_activity_at TEXT NOT NULL,
            changes_detected INTEGER DEFAULT 0,
            auto_sync_enabled BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Create PerformanceMetrics table for system analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PerformanceMetrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_id TEXT UNIQUE NOT NULL,
            metric_type TEXT NOT NULL,  -- 'tool_usage', 'response_time', 'success_rate'
            project_id TEXT,
            component_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            unit TEXT,
            timestamp TEXT NOT NULL,
            metadata TEXT  -- JSON object
        )
    """)

    # Add source_tool column to existing ChatHistory tables (migration)
    try:
        cursor.execute("ALTER TABLE ChatHistory ADD COLUMN source_tool TEXT")
        conn.commit()
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            # Re-raise if it's not a duplicate column error
            raise
        # Column already exists, continue

    # =====================================
    # MINDGRAPH INTELLIGENCE TRACKING TABLES
    # =====================================
    
    # Create MindGraph_Agents table for tracking AI agents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MindGraph_Agents (
            agent_id TEXT PRIMARY KEY,
            agent_name TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_active_at TEXT,
            session_count INTEGER DEFAULT 0,
            total_changes INTEGER DEFAULT 0,
            metadata TEXT  -- JSON object
        )
    """)
    
    # Create MindGraph_Changes table for tracking changes made by agents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MindGraph_Changes (
            change_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            change_type TEXT NOT NULL,
            file_path TEXT,
            lines_changed INTEGER,
            change_summary TEXT NOT NULL,
            change_details TEXT,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            conversation_id TEXT,
            impact_score REAL DEFAULT 0.0,
            metadata TEXT,  -- JSON object
            FOREIGN KEY (agent_id) REFERENCES MindGraph_Agents (agent_id)
        )
    """)
    
    # Create MindGraph_Reasons table for tracking reasoning chains
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MindGraph_Reasons (
            reason_id TEXT PRIMARY KEY,
            reason_type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            priority_level INTEGER DEFAULT 1,
            confidence_score REAL DEFAULT 1.0,
            context TEXT,  -- JSON object
            reasoning_chain_id TEXT,
            metadata TEXT  -- JSON object
        )
    """)
    
    # Create MindGraph_Relationships table for linking changes to reasons
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MindGraph_Relationships (
            relationship_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 1.0,
            confidence REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            metadata TEXT  -- JSON object
        )
    """)
    
    conn.commit()
