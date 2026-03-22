CREATE TABLE IF NOT EXISTS planner_tracks(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  label TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  data JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_planner_tracks_default ON planner_tracks(is_default) WHERE is_default;

CREATE TABLE IF NOT EXISTS planner_scenarios(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  label TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0,
  is_live BOOLEAN NOT NULL DEFAULT FALSE,
  data JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_planner_scenarios_live ON planner_scenarios(is_live) WHERE is_live;

CREATE TABLE IF NOT EXISTS planner_events(
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,

  track_id UUID NOT NULL
    REFERENCES planner_tracks(id) 
    ON UPDATE CASCADE 
    ON DELETE RESTRICT, -- prevent track deletion if events are present

  scenario_id UUID 
    REFERENCES planner_scenarios(id) 
    ON UPDATE CASCADE 
    ON DELETE CASCADE, -- if scenario is deleted, delete all events

  label TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,

  people VARCHAR[] NOT NULL DEFAULT ARRAY[]::VARCHAR[],
  tags VARCHAR[] NOT NULL DEFAULT ARRAY[]::VARCHAR[],
  task_types TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  data JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  creation_order SERIAL NOT NULL
);
