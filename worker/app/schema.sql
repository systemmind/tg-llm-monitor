CREATE TABLE IF NOT EXISTS tg_message_classifications (
  id BIGSERIAL PRIMARY KEY,
  chat_id BIGINT NOT NULL,
  message_id BIGINT NOT NULL,
  msg_date TIMESTAMPTZ NULL,
  sender_id BIGINT NULL,
  chat_title TEXT NULL,
  chat_username TEXT NULL,

  matched_by_keywords BOOLEAN NOT NULL DEFAULT FALSE,
  matched_filters TEXT[] NOT NULL DEFAULT '{}',

  text TEXT NOT NULL,

  llm_match BOOLEAN NOT NULL,
  llm_score REAL NULL,
  llm_reason TEXT NULL,
  llm_raw JSONB NULL,

  stream_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_tgmc_created_at ON tg_message_classifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tgmc_llm_match ON tg_message_classifications(llm_match);