
-- =========================================
-- 1. DOCUMENTS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    owner_sub TEXT NOT NULL,
    allowed_groups TEXT[] NOT NULL,
    s3_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'processing', 'ready', 'failed', 'retired')
    ),
    current_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS documents_acl_idx
ON documents (tenant_id, status);


-- =========================================
-- 2. FEEDBACK TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN -1 AND 1),
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =========================================
-- 3. AUDIT EVENTS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS audit_tenant_time
ON audit_events (tenant_id, created_at DESC);


-- =========================================
-- 4. APPROVALS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    requester TEXT NOT NULL,
    question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    reviewer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS approvals_tenant_idx
ON approvals (tenant_id, status);


-- =========================================
-- 5. CHAT MESSAGES TABLE
-- =========================================

-- Persistent short-term conversation memory (Aurora, no local database).

CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    conversation_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chat_messages_session_idx
ON chat_messages (tenant_id, conversation_id, id DESC);
