# Claude Code Team Agent Workflow Guide

**Version**: 1.0  
**Updated**: August 10, 2025  
**Audience**: Human users working with Claude Code and expert agents  
**Tools**: All 55 LTMC tools across Core, Phase3, and Unified categories  

## 🎯 Overview

This guide shows how you, as a human user, can work with Claude Code and its expert agents to leverage LTMC's 55 tools for maximum productivity. Whether you're building software, managing projects, or coordinating complex tasks, this workflow guide provides practical examples of how to use LTMC's advanced capabilities.

## 🤝 Your Team: Claude Code + Expert Agents

### **Primary Agents You'll Work With:**
- 🧠 **Claude Code**: Primary interface, coordination, planning
- 👨‍💻 **expert-coder**: Code implementation, pattern learning
- 🏗️ **software-architect**: System design, technical decisions
- 📋 **project-manager**: Task planning, resource allocation
- 🧪 **expert-tester**: Testing strategies, quality assurance
- 📝 **expert-documenter**: Documentation creation and maintenance

### **LTMC Power**: 55 Tools at Your Service
- **28 Core Tools**: Memory, chat, tasks, code patterns, caching
- **26 Phase3 Tools**: ML blueprints, team assignment, documentation sync
- **1 Unified Tool**: System-wide performance monitoring

---

## 🚀 Workflow 1: Building a Complete Feature with Your Team

### **Scenario**: You want to build an OAuth authentication system

#### **Step 1: Planning with Claude Code + project-manager**

**You**: *"I need to implement OAuth2 authentication for our web app"*

**Claude Code** coordinates with **project-manager** to:

```python
# 1. Create comprehensive task blueprint
mcp__ltmc__create_task_blueprint(
    title="OAuth2 Authentication System",
    description="Complete OAuth2 flow with JWT tokens, role-based access",
    complexity="high",
    estimated_duration_minutes=480,
    required_skills=["python", "oauth2", "jwt", "security", "fastapi"],
    priority_score=0.9,
    tags=["security", "authentication", "user-facing"]
)

# 2. Analyze complexity automatically
mcp__ltmc__analyze_task_complexity(
    title="OAuth2 Authentication System", 
    description="Complete OAuth2 flow with JWT tokens",
    required_skills=["python", "oauth2", "jwt", "security"]
)

# 3. Break down into manageable tasks
mcp__ltmc__decompose_task_blueprint(
    blueprint_id="bp_oauth_123",
    decomposition_strategy="feature_based"
)
```

**Result**: You get a detailed breakdown:
- OAuth2 provider integration (2 hours)
- JWT token management (1.5 hours)  
- Role-based access control (2 hours)
- Security middleware (1 hour)
- Testing suite (1.5 hours)

#### **Step 2: Team Assignment with ML Intelligence**

**project-manager** uses ML to assign optimal team members:

```python
# Smart team assignment based on skills and availability
mcp__ltmc__assign_task_to_team(
    blueprint_id="bp_oauth_123",
    available_members=[
        {"id": "expert-coder", "skills": ["python", "security"], "capacity": 0.9},
        {"id": "software-architect", "skills": ["system-design", "security"], "capacity": 0.7}
    ],
    project_id="web_app_auth",
    preferences={"prefer_security_expert": True}
)
```

**Result**: **expert-coder** assigned to implementation, **software-architect** for design review.

#### **Step 3: Learning from Experience with expert-coder**

**expert-coder** starts by checking past successful patterns:

```python
# Learn from previous successful implementations
mcp__ltmc__get_code_patterns(
    query="oauth2 jwt token authentication python",
    result_filter="pass",
    top_k=5
)

# Retrieve specific context about authentication
mcp__ltmc__ask_with_context(
    query="How should I implement secure JWT token validation?",
    conversation_id="oauth_implementation_session",
    top_k=3
)
```

**Result**: **expert-coder** finds 3 successful OAuth patterns from previous projects, avoiding common pitfalls.

#### **Step 4: Implementation with Pattern Learning**

As **expert-coder** works, every successful step is captured:

```python
# Log successful code patterns for future learning
mcp__ltmc__log_code_attempt(
    input_prompt="Implement JWT token validation middleware",
    generated_code="""
    def validate_jwt_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return {"valid": True, "user_id": payload["user_id"], "roles": payload.get("roles", [])}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    """,
    result="pass",
    tags=["security", "jwt", "authentication", "middleware", "python"]
)
```

**Benefit**: Future OAuth implementations will reference this successful pattern.

#### **Step 5: Documentation Sync with expert-documenter**

**expert-documenter** uses Phase3 tools to keep docs current:

```python
# Automatically sync documentation with code changes
mcp__ltmc__sync_documentation_with_code(
    file_path="/src/auth/oauth.py", 
    project_id="web_app_auth",
    force_update=False
)

# Validate documentation accuracy
mcp__ltmc__validate_documentation_consistency(
    file_path="/src/auth/oauth.py",
    project_id="web_app_auth" 
)

# Generate documentation from blueprint
mcp__ltmc__generate_blueprint_documentation(
    blueprint_id="bp_oauth_123",
    format="markdown",
    include_relationships=True
)
```

**Result**: Documentation stays current automatically, no manual updates needed.

#### **Step 6: Progress Tracking and Completion**

Throughout the project, progress is tracked:

```python
# Update task progress in real-time
mcp__ltmc__update_task_progress(
    assignment_id="assign_oauth_456",
    progress_percentage=75.0,
    status="in_progress", 
    actual_hours_worked=6.0,
    notes="OAuth2 flow complete, JWT integration 75% done"
)

# Store project insights for future reference
mcp__ltmc__store_memory(
    file_name="oauth_implementation_lessons.md",
    content="Key learnings: JWT secret rotation, role hierarchy design, error handling patterns",
    resource_type="document"
)
```

---

## 📊 Workflow 2: Managing Complex Multi-Team Projects

### **Scenario**: You're managing a team building a social media platform

#### **Step 1: Project Overview and Workload Management**

**You**: *"We have 5 developers working on user profiles, messaging, and content feeds"*

```python
# Get team workload overview
mcp__ltmc__get_team_workload_overview(
    team_members=[
        {"id": "alice", "name": "Alice Chen", "skills": ["react", "typescript"]},
        {"id": "bob", "name": "Bob Martinez", "skills": ["python", "fastapi", "databases"]},
        {"id": "carol", "name": "Carol Williams", "skills": ["devops", "kubernetes", "monitoring"]},
        {"id": "david", "name": "David Kim", "skills": ["mobile", "react-native"]},
        {"id": "eve", "name": "Eve Johnson", "skills": ["ui-design", "figma"]}
    ],
    project_id="social_media_platform"
)

# List all project blueprints with filtering
mcp__ltmc__list_project_blueprints(
    project_id="social_media_platform",
    min_complexity="medium",
    tags=["user-facing"],
    limit=10
)
```

**Result**: You see Alice is overloaded (120% capacity), Bob has availability, Carol needs more DevOps tasks.

#### **Step 2: Intelligent Task Dependencies**

```python
# Resolve optimal execution order
mcp__ltmc__resolve_blueprint_execution_order(
    blueprint_ids=["bp_user_profiles", "bp_messaging", "bp_content_feeds", "bp_notifications"]
)

# Add critical dependencies
mcp__ltmc__add_blueprint_dependency(
    dependent_blueprint_id="bp_messaging",
    prerequisite_blueprint_id="bp_user_profiles", 
    dependency_type="blocking",
    is_critical=True
)
```

**Result**: System determines user profiles must be built before messaging, prevents scheduling conflicts.

#### **Step 3: Real-Time Development Monitoring**

```python
# Start monitoring key files for changes
mcp__ltmc__start_real_time_sync(
    file_paths=["/src/users/", "/src/messaging/", "/src/content/"],
    project_id="social_media_platform"
)

# Monitor sync status
mcp__ltmc__get_sync_status(project_id="social_media_platform")

# Detect code changes automatically
mcp__ltmc__detect_code_changes(
    file_paths=["/src/users/profile.py", "/src/messaging/chat.py"],
    project_id="social_media_platform"
)
```

**Result**: You're automatically notified when code changes require documentation updates.

---

## 🧠 Workflow 3: Knowledge Management and Learning

### **Scenario**: You want your team to learn from mistakes and build institutional knowledge

#### **Step 1: Capturing Team Knowledge**

**You**: *"Our team keeps making the same database connection mistakes"*

```python
# Log common error patterns
mcp__ltmc__log_code_attempt(
    input_prompt="Fix database connection pool exhaustion",
    generated_code="""
    # WRONG - causes pool exhaustion
    for user in users:
        db = create_connection()  # Creates new connection each time
        process_user(db, user)
    
    # RIGHT - reuses connection pool  
    with get_db_connection() as db:
        for user in users:
            process_user(db, user)
    """,
    result="pass",
    tags=["database", "connection-pool", "common-mistake", "performance"]
)

# Store architectural decisions
mcp__ltmc__store_memory(
    file_name="database_architecture_decisions.md",
    content="Database Connection Patterns: Always use connection pooling, max 20 connections, timeout 30s",
    resource_type="document"
)
```

#### **Step 2: Creating Learning Resources**

```python
# Link related concepts in knowledge graph
mcp__ltmc__link_resources(
    source_id="database_patterns_doc",
    target_id="performance_optimization_guide", 
    relation="implements"
)

# Query knowledge graph for related information
mcp__ltmc__query_graph(
    entity="database_connection_pool",
    relation_type="causes_issues_with"
)

# Auto-link similar documents
mcp__ltmc__auto_link_documents(
    documents=[
        {"id": "db_perf_guide", "content": "Database performance optimization..."},
        {"id": "connection_patterns", "content": "Connection pool best practices..."}
    ]
)
```

**Result**: Your team builds a knowledge graph of connected concepts, making knowledge discovery easier.

#### **Step 3: Proactive Learning and Pattern Analysis**

```python
# Analyze patterns to identify improvement areas
mcp__ltmc__analyze_code_patterns(
    function_name="database_connection",
    tags=["performance", "database"]
)

# Get statistics on team coding patterns
mcp__ltmc__get_code_statistics()

# Smart query routing for complex questions
mcp__ltmc__route_query(
    query="What are the best practices for handling database migrations in production?"
)
```

**Result**: System identifies that 60% of database issues are connection-related, suggests focused training.

---

## 🔄 Workflow 4: Continuous Integration and Quality

### **Scenario**: You want to maintain code quality as your team grows

#### **Step 1: Blueprint-Code Consistency**

```python
# Create blueprints from existing code
mcp__ltmc__create_blueprint_from_code(
    file_path="/src/payment/stripe_integration.py",
    project_id="ecommerce_platform"
)

# Validate that code matches blueprint
mcp__ltmc__validate_blueprint_consistency(
    blueprint_id="bp_payment_system",
    file_path="/src/payment/stripe_integration.py"
)

# Update blueprints when code changes
mcp__ltmc__update_blueprint_structure(
    blueprint_id="bp_payment_system",
    file_path="/src/payment/stripe_integration.py"
)
```

#### **Step 2: Documentation Quality Gates**

```python
# Get documentation consistency score
mcp__ltmc__get_documentation_consistency_score(
    file_path="/src/payment/stripe_integration.py",
    project_id="ecommerce_platform"
)

# Detect documentation drift 
mcp__ltmc__detect_documentation_drift(
    file_path="/src/payment/stripe_integration.py",
    project_id="ecommerce_platform"
)
```

**Result**: System flags when documentation falls below 80% consistency, preventing outdated docs.

#### **Step 3: Performance Monitoring**

```python
# Monitor system performance
mcp__ltmc__get_performance_report()

# Get task management metrics
mcp__ltmc__get_taskmaster_performance_metrics()

# Monitor cache performance
mcp__ltmc__redis_cache_stats()
```

---

## 💡 Workflow 5: Daily Development Habits

### **Morning Routine**: Starting Your Development Day

```python
# 1. Restore context from previous session
mcp__ltmc__retrieve_memory(
    query="yesterday progress status current priorities",
    conversation_id="daily_dev_session",
    top_k=5
)

# 2. Check your assigned tasks
mcp__ltmc__list_todos(status="pending", limit=10)

# 3. Review team workload
mcp__ltmc__get_team_workload_overview(
    team_members=your_team, 
    project_id="current_project"
)
```

### **During Development**: Continuous Learning

```python
# Before implementing something new, check patterns
mcp__ltmc__get_code_patterns(
    query="react component state management hooks",
    result_filter="pass",
    top_k=3
)

# Log your successful implementations
mcp__ltmc__log_code_attempt(
    input_prompt="Custom React hook for API data fetching",
    generated_code="const useApiData = (url) => { ... }",
    result="pass", 
    tags=["react", "hooks", "api", "custom-hook"]
)

# Store insights and decisions
mcp__ltmc__store_memory(
    file_name="react_patterns_learned.md",
    content="useCallback vs useMemo: useCallback for functions, useMemo for expensive computations"
)
```

### **End of Day**: Knowledge Capture

```python
# Log important conversations
mcp__ltmc__log_chat(
    content="Team discussion about microservices architecture trade-offs",
    conversation_id="architecture_decisions",
    role="system"
)

# Complete finished tasks
mcp__ltmc__complete_todo(todo_id=123)

# Store day's learnings
mcp__ltmc__store_memory(
    file_name="daily_insights_$(date +%Y%m%d).md",
    content="Key decisions and learnings from today's work"
)
```

---

## 🎯 Advanced Use Cases

### **Use Case 1: Onboarding New Team Members**

```python
# Create comprehensive onboarding blueprint
mcp__ltmc__create_task_blueprint(
    title="New Developer Onboarding",
    description="Complete onboarding checklist with codebase familiarization",
    required_skills=["general", "learning"],
    tags=["onboarding", "team-building"]
)

# Assign onboarding buddy using ML
mcp__ltmc__assign_task_to_team(
    blueprint_id="bp_onboarding_new_dev",
    available_members=senior_team_members,
    preferences={"prefer_mentoring_experience": True}
)

# Provide contextual learning resources
mcp__ltmc__ask_with_context(
    query="What should a new developer know about our architecture?",
    conversation_id="onboarding_context"
)
```

### **Use Case 2: Technical Debt Management**

```python
# Track technical debt patterns
mcp__ltmc__analyze_code_patterns(
    tags=["technical-debt", "refactoring"]
)

# Create debt reduction blueprints
mcp__ltmc__create_task_blueprint(
    title="Refactor Legacy Authentication Module", 
    description="Modernize auth system, improve test coverage",
    complexity="medium",
    tags=["technical-debt", "security", "refactoring"]
)

# Monitor progress and impact
mcp__ltmc__update_task_progress(
    assignment_id="debt_reduction_auth",
    progress_percentage=40.0,
    notes="Reduced complexity from 15 to 8 cyclomatic complexity"
)
```

### **Use Case 3: Cross-Team Coordination**

```python
# Query cross-team dependencies
mcp__ltmc__query_graph(
    entity="user_authentication_service",
    relation_type="depends_on"
)

# Coordinate shared component updates
mcp__ltmc__get_document_relationships(
    doc_id="shared_components_spec"
)

# Real-time synchronization across teams
mcp__ltmc__start_real_time_sync(
    file_paths=["/shared/", "/common/", "/api-contracts/"],
    project_id="multi_team_platform"
)
```

---

## 📊 Benefits You'll Experience

### **For You as a Human Developer:**
- 🧠 **Never lose context** - All conversations, decisions, and learnings are preserved
- 📈 **Accelerated learning** - Learn from past successful patterns and avoid repeated mistakes  
- 🎯 **Smarter task planning** - ML-driven complexity analysis and optimal team assignment
- 📝 **Always-current documentation** - Automated sync between code and docs
- 🔍 **Intelligent knowledge discovery** - Find related information through knowledge graphs

### **For Your Development Team:**
- 🤝 **Seamless collaboration** - Shared memory and context across all team members
- ⚡ **Faster onboarding** - New team members have instant access to institutional knowledge
- 📊 **Data-driven decisions** - Performance metrics and pattern analysis guide improvements
- 🔄 **Continuous improvement** - System learns from each project to optimize future work
- 🛡️ **Quality gates** - Automated consistency checks prevent technical debt

### **For Your Projects:**
- 🎯 **Higher success rates** - ML blueprint analysis improves estimation accuracy
- 📚 **Knowledge preservation** - No more lost tribal knowledge when team members leave  
- 🔧 **Reduced maintenance** - Automated documentation sync reduces maintenance overhead
- 📈 **Scalable processes** - Workflows that work for 2 people also work for 20 people
- 💡 **Innovation acceleration** - More time for creative work, less time on repetitive tasks

---

## 🚀 Getting Started Today

### **1. Basic Setup (5 minutes)**
```bash
# Ensure LTMC server is running
./start_server.sh

# Verify all 55 tools are available  
curl http://localhost:5050/health
```

### **2. First Workflow (15 minutes)**
```python
# Store your current project context
mcp__ltmc__store_memory(
    file_name="my_project_overview.md",
    content="Current project: [description], Goals: [goals], Team: [team members]"
)

# Create your first task blueprint
mcp__ltmc__create_task_blueprint(
    title="Learn LTMC Integration",
    description="Integrate LTMC tools into daily development workflow"
)
```

### **3. Daily Habits (Ongoing)**
- Start each day by retrieving yesterday's context
- Log successful code patterns as you work
- End each day by storing key insights and learnings
- Use task blueprints for anything that takes more than 1 hour

### **4. Team Integration (1 week)**
- Onboard your team members to LTMC workflows
- Establish shared conventions for tagging and organization
- Set up real-time synchronization for shared codebases
- Create team knowledge graphs for your domain expertise

---

## 📞 Support and Resources

### **If You Need Help:**
- 📖 **Complete Tool Reference**: `/docs/guides/COMPLETE_55_TOOLS_REFERENCE.md`
- 🔧 **API Documentation**: `/docs/api/API_REFERENCE.md` 
- 🏗️ **Architecture Guide**: `/docs/architecture/SYSTEM_ARCHITECTURE.md`
- 💬 **Community Support**: GitHub Issues and Discussions

### **Next Steps:**
- 📚 Explore advanced Phase3 tools for complex project management
- 🔗 Set up knowledge graphs for your specific domain
- 📊 Configure performance monitoring and alerts
- 🤖 Customize ML blueprint analysis for your team's patterns

---

**Ready to transform your development workflow?** Start with a simple memory storage and task blueprint, then gradually adopt more advanced features as your team grows comfortable with the system.

**Remember**: LTMC learns from every interaction, so the more you use it, the more valuable it becomes for your entire team! 🚀