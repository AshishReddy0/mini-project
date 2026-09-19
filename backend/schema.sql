-- Database Schema for Study Companion Platform (PostgreSQL)
-- Generated from SQLAlchemy ORM Models

-- Enable UUID extension (PostgreSQL 13+ includes gen_random_uuid by default, uuid-ossp for compatibility)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- CUSTOM ENUM TYPES
-- ==========================================

-- Enum for Generated Content Types
DO $$ BEGIN
    CREATE TYPE content_type_enum AS ENUM ('revision', 'exam', 'quiz', 'logic_flow');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Enum for Chat Message Roles
DO $$ BEGIN
    CREATE TYPE chat_role_enum AS ENUM ('user', 'assistant');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ==========================================
-- TRIGGER FUNCTION FOR UPDATED_AT
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';


-- ==========================================
-- 1. USERS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- ==========================================
-- 2. WORKSPACES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    roadmap_json JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id);

DROP TRIGGER IF EXISTS trigger_workspaces_updated_at ON workspaces;
CREATE TRIGGER trigger_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ==========================================
-- 3. DOCUMENTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_workspace_id ON documents(workspace_id);


-- ==========================================
-- 4. EXTRACTED_TEXT TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS extracted_text (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL DEFAULT '',
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_extracted_text_document_id ON extracted_text(document_id);


-- ==========================================
-- 5. GENERATED_CONTENT TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    content_type content_type_enum NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_generated_content_workspace_id ON generated_content(workspace_id);
CREATE INDEX IF NOT EXISTS idx_generated_content_type ON generated_content(content_type);


-- ==========================================
-- 6. CHAT_HISTORY TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    role chat_role_enum NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_history_workspace_id ON chat_history(workspace_id);


-- ==========================================
-- 7. CONCEPT_NODES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS concept_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    unit_ref VARCHAR(255),
    difficulty VARCHAR(50) NOT NULL DEFAULT 'medium',
    order_hint INTEGER NOT NULL DEFAULT 0,
    sub_points JSON,
    answer_cache TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_concept_nodes_workspace_id ON concept_nodes(workspace_id);


-- ==========================================
-- 8. CONCEPT_EDGES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS concept_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_node_id UUID NOT NULL REFERENCES concept_nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES concept_nodes(id) ON DELETE CASCADE,
    relation VARCHAR(50) NOT NULL DEFAULT 'prerequisite'
);

CREATE INDEX IF NOT EXISTS idx_concept_edges_from_node ON concept_edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_concept_edges_to_node ON concept_edges(to_node_id);


-- ==========================================
-- 9. NODE_MASTERIES TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS node_masteries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES concept_nodes(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'locked',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_score INTEGER,
    feedback TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_node_masteries_user_id ON node_masteries(user_id);
CREATE INDEX IF NOT EXISTS idx_node_masteries_node_id ON node_masteries(node_id);

DROP TRIGGER IF EXISTS trigger_node_masteries_updated_at ON node_masteries;
CREATE TRIGGER trigger_node_masteries_updated_at
    BEFORE UPDATE ON node_masteries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
