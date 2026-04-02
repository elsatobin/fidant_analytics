-- CreateTable: pre-computed daily usage aggregates
-- dateKey uses VARCHAR(10) to match daily_usage_events.date_key format "YYYY-MM-DD"
-- cachedAt is used to determine staleness for today's entry (TTL-based invalidation)
CREATE TABLE "daily_usage_cache" (
    "id"          SERIAL       NOT NULL,
    "user_id"     INTEGER      NOT NULL,
    "date_key"    VARCHAR(10)  NOT NULL,
    "committed"   INTEGER      NOT NULL DEFAULT 0,
    "daily_limit" INTEGER      NOT NULL,
    "cached_at"   TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "daily_usage_cache_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "uq_cache_user_date" UNIQUE ("user_id", "date_key"),
    CONSTRAINT "daily_usage_cache_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
