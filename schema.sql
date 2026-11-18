-- MySQL 8.0 DDL：把内存 StateStore / Tracer 换成持久化实现时使用
CREATE TABLE IF NOT EXISTS task (
  task_id        VARCHAR(64) PRIMARY KEY,
  question       TEXT NOT NULL,
  state          VARCHAR(32) NOT NULL,
  config_json    JSON,
  created_at     DOUBLE NOT NULL,
  updated_at     DOUBLE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS checkpoint (
  id               BIGINT AUTO_INCREMENT PRIMARY KEY,
  task_id          VARCHAR(64) NOT NULL,
  node_id          VARCHAR(64) NOT NULL,
  state            VARCHAR(32) NOT NULL,
  cursor_idx       INT NOT NULL,
  args_json        JSON,
  idempotency_key  VARCHAR(128) NOT NULL,
  result_ref       VARCHAR(128),
  ts               DOUBLE NOT NULL,
  INDEX idx_task (task_id, id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS execution_log (
  idempotency_key VARCHAR(128) PRIMARY KEY,
  task_id         VARCHAR(64) NOT NULL,
  node_id         VARCHAR(64) NOT NULL,
  executed_at     DOUBLE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS trace_event (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  task_id      VARCHAR(64) NOT NULL,
  node_id      VARCHAR(64),
  kind         VARCHAR(32) NOT NULL,
  payload_json JSON,
  tokens       INT DEFAULT 0,
  latency_ms   DOUBLE DEFAULT 0,
  cost_usd     DOUBLE DEFAULT 0,
  ts           DOUBLE NOT NULL,
  INDEX idx_task_ts (task_id, ts)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS eval_result (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  config_name   VARCHAR(64) NOT NULL,
  dataset_hash  VARCHAR(64) NOT NULL,
  metrics_json  JSON,
  seed          INT NOT NULL,
  created_at    DOUBLE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
