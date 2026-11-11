-- Source: RetailRocket retail clickstream only.
-- Conversions below mean transaction-event sessions; NOT healthcare conversions,
-- campaign-attributed conversions, pharmaceutical sales or clinical outcomes.
DROP VIEW IF EXISTS v_daily_events;
CREATE VIEW v_daily_events AS
SELECT
    event_date,
    COUNT(*) AS event_count,
    COUNT(DISTINCT visitor_id) AS unique_visitors,
    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS views,
    SUM(CASE WHEN event_type = 'addtocart' THEN 1 ELSE 0 END) AS cart_adds,
    SUM(CASE WHEN event_type = 'transaction' THEN 1 ELSE 0 END) AS transaction_events
FROM event_facts
GROUP BY event_date;

DROP VIEW IF EXISTS v_daily_session_kpis;
CREATE VIEW v_daily_session_kpis AS
SELECT
    substr(session_start, 1, 10) AS session_date,
    COUNT(*) AS session_count,
    SUM(converted) AS converted_sessions,
    ROUND(1.0 * SUM(converted) / NULLIF(COUNT(*), 0), 4) AS session_conversion_rate,
    SUM(order_count) AS distinct_orders_within_sessions
FROM session_facts
GROUP BY substr(session_start, 1, 10);

DROP VIEW IF EXISTS v_overall_kpis;
CREATE VIEW v_overall_kpis AS
SELECT
    COUNT(*) AS session_count,
    SUM(converted) AS converted_sessions,
    ROUND(1.0 * SUM(converted) / NULLIF(COUNT(*), 0), 4) AS session_conversion_rate,
    SUM(order_count) AS distinct_orders_within_sessions,
    ROUND(AVG(duration_seconds), 2) AS average_session_duration_seconds
FROM session_facts;

-- Session stages are NOT guaranteed to occur in a view > cart > purchase order.
DROP VIEW IF EXISTS v_session_stage_presence;
CREATE VIEW v_session_stage_presence AS
SELECT
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN view_events > 0 THEN 1 ELSE 0 END) AS sessions_with_view,
    SUM(CASE WHEN cart_events > 0 THEN 1 ELSE 0 END) AS sessions_with_cart,
    SUM(CASE WHEN transaction_events > 0 THEN 1 ELSE 0 END) AS sessions_with_transaction
FROM session_facts;
