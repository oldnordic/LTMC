# MCP Protocol Debugging Plan

## Problem Statement
FastMCP binary builds successfully but fails to connect to Claude Code MCP client. Root cause hypothesis: Protocol incompatibility between FastMCP implementation and standard MCP protocol expected by Claude Code.

## Investigation Approach
This plan follows proper debugging methodology: Research → Test → Analyze → Implement based on evidence.

## Phase 1: Protocol Investigation

### 1.1 Official MCP Protocol Research
- **Objective**: Understand the exact MCP protocol specification that Claude Code expects
- **Tasks**:
  - Research official MCP protocol documentation
  - Document JSON-RPC message format requirements
  - Identify stdio transport implementation standards
  - Map out MCP handshake and initialization sequence
- **Deliverable**: MCP_PROTOCOL_SPECIFICATION.md

### 1.2 FastMCP vs Standard MCP Comparison
- **Objective**: Identify specific differences between implementations
- **Tasks**:
  - Compare FastMCP JSON-RPC message structure vs official MCP
  - Analyze tool registration schema differences
  - Document initialization sequence variations
  - Identify stdio communication pattern differences
- **Deliverable**: PROTOCOL_COMPARISON_ANALYSIS.md

### 1.3 Claude Code MCP Client Analysis
- **Objective**: Understand what exactly Claude Code expects from stdio MCP servers
- **Tasks**:
  - Analyze Claude Code MCP documentation for stdio requirements
  - Document expected message exchange patterns
  - Identify authentication and handshake requirements
- **Deliverable**: CLAUDE_CODE_MCP_REQUIREMENTS.md

## Phase 2: Testing and Validation

### 2.1 Minimal Official MCP Test Server
- **Objective**: Test hypothesis that official MCP SDK works with Claude Code
- **Tasks**:
  - Create minimal MCP server using official Python SDK
  - Implement basic ping/hello tool for connectivity testing
  - Configure for stdio transport
  - Test binary creation with PyInstaller
- **Deliverable**: test_official_mcp_server.py + binary

### 2.2 Connectivity Validation
- **Objective**: Confirm official MCP SDK compatibility with Claude Code
- **Tasks**:
  - Test minimal official MCP server with Claude Code
  - Document successful connection and tool invocation
  - Compare behavior with current FastMCP binary failure
  - Log exact message exchanges for analysis
- **Deliverable**: CONNECTIVITY_TEST_RESULTS.md

### 2.3 Behavioral Comparison
- **Objective**: Document exact differences between working and non-working implementations
- **Tasks**:
  - Compare message logs from official MCP vs FastMCP
  - Identify point of connection failure in FastMCP
  - Document successful handshake sequence from official MCP
  - Map failure points in current binary
- **Deliverable**: BEHAVIORAL_ANALYSIS.md

## Phase 3: Root Cause Analysis

### 3.1 Protocol Difference Documentation
- **Objective**: Identify specific incompatibilities causing connection failure
- **Tasks**:
  - List exact JSON-RPC format differences
  - Document schema registration variations
  - Identify handshake sequence discrepancies
  - Map stdio transport implementation differences
- **Deliverable**: ROOT_CAUSE_ANALYSIS.md

### 3.2 Solution Feasibility Assessment
- **Objective**: Determine best path forward based on findings
- **Options to Evaluate**:
  1. **FastMCP Compatibility Fix**: Modify FastMCP to match standard MCP protocol
  2. **Migration to Official SDK**: Replace FastMCP with official MCP Python SDK
  3. **Hybrid Approach**: Use official SDK with FastMCP-inspired optimizations
- **Evaluation Criteria**:
  - Technical feasibility and complexity
  - Maintenance burden
  - Performance implications
  - Tool compatibility preservation
- **Deliverable**: SOLUTION_RECOMMENDATIONS.md

## Phase 4: Implementation

### 4.1 Solution Implementation
- **Objective**: Implement chosen solution based on investigation findings
- **Tasks**: (To be determined based on Phase 3 findings)
- **Deliverable**: Working MCP binary with proper Claude Code compatibility

### 4.2 Binary Rebuild and Testing
- **Objective**: Create production-ready binary with correct protocol
- **Tasks**:
  - Rebuild binary with chosen implementation
  - Preserve 55-tool functionality
  - Maintain performance optimizations where possible
  - Test comprehensive tool functionality
- **Deliverable**: ltmc binary with Claude Code compatibility

### 4.3 Final Validation
- **Objective**: Confirm complete solution
- **Tasks**:
  - Test all 55 tools via Claude Code MCP client
  - Validate connection stability
  - Document performance characteristics
  - Create deployment instructions
- **Deliverable**: FINAL_VALIDATION_REPORT.md

## Success Criteria
- [ ] Binary connects successfully to Claude Code MCP client
- [ ] All 55 LTMC tools are accessible via MCP protocol
- [ ] Connection is stable and reliable
- [ ] Performance is acceptable (ideally maintaining lazy loading benefits)
- [ ] Solution is maintainable and follows MCP standards

## Risk Mitigation
- **Risk**: Official MCP SDK incompatible with lazy loading
  - **Mitigation**: Evaluate lazy loading implementation within official SDK constraints
- **Risk**: Complete rewrite required
  - **Mitigation**: Gradual migration strategy preserving working components
- **Risk**: Performance degradation
  - **Mitigation**: Performance testing at each phase to identify optimizations

## Timeline
- **Phase 1**: Protocol Investigation (1-2 days)
- **Phase 2**: Testing and Validation (1 day)
- **Phase 3**: Root Cause Analysis (0.5 days)
- **Phase 4**: Implementation (2-3 days)

## Documentation Standard
All deliverables will be stored in `/home/feanor/Projects/lmtc/docs/debugging/` with clear naming conventions and cross-references for traceability.