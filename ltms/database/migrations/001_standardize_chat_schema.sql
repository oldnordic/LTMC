
-- LTMC Graph Database Schema Standardization Migration
-- Fixes chat_messages table issue and standardizes schema
-- 
-- PROBLEM: graph_actions.py expects 'chat_messages' table but database has:
--   - chats (37 records)
--   - chat_history (126 records)  
--   - ChatHistory (2 records)
--
-- SOLUTION: Create consolidated 'chat_messages' VIEW from fragmented tables

-- Create consolidated chat_messages view from fragmented tables
CREATE VIEW IF NOT EXISTS chat_messages AS
SELECT 
    id,
    conversation_id,
    role,
    content,
    agent_name,
    source_tool,
    created_at as created_at
FROM chats

UNION ALL

SELECT 
    id + 10000 as id,  -- Offset to avoid ID conflicts
    conversation_id,
    role,
    content,
    agent_name,
    source_tool,
    timestamp as created_at
FROM chat_history

UNION ALL

SELECT 
    id + 20000 as id,  -- Offset to avoid ID conflicts  
    conversation_id,
    role,
    content,
    agent_name,
    source_tool,
    timestamp as created_at
FROM ChatHistory;

-- Create performance indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_chats_conversation
ON chats (conversation_id);

CREATE INDEX IF NOT EXISTS idx_chats_source_tool  
ON chats (source_tool);

CREATE INDEX IF NOT EXISTS idx_chats_created_at
ON chats (created_at);

CREATE INDEX IF NOT EXISTS idx_chat_history_conversation
ON chat_history (conversation_id);

CREATE INDEX IF NOT EXISTS idx_chat_history_source_tool
ON chat_history (source_tool);

CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp
ON chat_history (timestamp);

-- Verify migration completed successfully
SELECT 'Migration completed. Chat messages available: ' || COUNT(*) as status
FROM chat_messages;
