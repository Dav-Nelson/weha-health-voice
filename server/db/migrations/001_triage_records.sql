CREATE TABLE IF NOT EXISTS triage_records (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) NOT NULL,
  language VARCHAR(10) DEFAULT 'en',
  fields JSONB NOT NULL DEFAULT '{}',
  urgency VARCHAR(20),
  matched_signs JSONB DEFAULT '[]',
  guidance TEXT,
  status VARCHAR(20) DEFAULT 'in_progress',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_triage_session ON triage_records(session_id);