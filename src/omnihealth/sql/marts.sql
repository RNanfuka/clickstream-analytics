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

-- A session-level sequence with strictly increasing timestamps. Equal-time events
-- cannot establish ordering; no item-level or marketing-attribution claim is made.
DROP VIEW IF EXISTS v_ordered_session_funnel;
CREATE VIEW v_ordered_session_funnel AS
WITH first_views AS (
    SELECT session_id, MIN(event_ts) AS view_at
    FROM event_facts WHERE event_type = 'view' GROUP BY session_id
), first_carts AS (
    SELECT e.session_id, MIN(e.event_ts) AS cart_at
    FROM event_facts e JOIN first_views v ON e.session_id = v.session_id
    WHERE e.event_type = 'addtocart' AND e.event_ts > v.view_at
    GROUP BY e.session_id
), first_purchases AS (
    SELECT e.session_id, MIN(e.event_ts) AS purchase_at
    FROM event_facts e JOIN first_carts c ON e.session_id = c.session_id
    WHERE e.event_type = 'transaction' AND e.event_ts > c.cart_at
    GROUP BY e.session_id
)
SELECT COUNT(*) AS total_sessions,
       COUNT(v.session_id) AS sessions_with_view,
       COUNT(c.session_id) AS sessions_with_later_cart,
       COUNT(p.session_id) AS sessions_with_later_purchase,
       ROUND(1.0 * COUNT(p.session_id) / NULLIF(COUNT(v.session_id), 0), 4)
           AS view_to_purchase_rate
FROM session_facts s
LEFT JOIN first_views v ON s.session_id = v.session_id
LEFT JOIN first_carts c ON s.session_id = c.session_id
LEFT JOIN first_purchases p ON s.session_id = p.session_id;

DROP VIEW IF EXISTS v_visitor_kpis;
CREATE VIEW v_visitor_kpis AS
SELECT visitor_id,
       COUNT(*) AS session_count,
       SUM(event_count) AS event_count,
       SUM(converted) AS converted_sessions,
       SUM(order_count) AS distinct_orders_within_sessions,
       MIN(session_start) AS first_observed_session,
       MAX(session_end) AS last_observed_event,
       CASE WHEN COUNT(*) > 1 THEN 'multiple_sessions' ELSE 'one_session' END
           AS observed_session_type
FROM session_facts
GROUP BY visitor_id
ORDER BY visitor_id;

DROP VIEW IF EXISTS v_session_engagement;
CREATE VIEW v_session_engagement AS
SELECT CASE WHEN event_count = 1 THEN '1 event'
            WHEN event_count <= 5 THEN '2-5 events'
            ELSE '6+ events' END AS engagement_band,
       COUNT(*) AS session_count,
       SUM(event_count) AS total_events,
       SUM(converted) AS converted_sessions,
       ROUND(1.0 * SUM(converted) / COUNT(*), 4) AS session_conversion_rate,
       ROUND(AVG(duration_seconds), 2) AS average_duration_seconds
FROM session_facts
GROUP BY engagement_band
ORDER BY MIN(event_count);

-- Session stages are NOT guaranteed to occur in a view > cart > purchase order.
DROP VIEW IF EXISTS v_session_stage_presence;
CREATE VIEW v_session_stage_presence AS
SELECT
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN view_events > 0 THEN 1 ELSE 0 END) AS sessions_with_view,
    SUM(CASE WHEN cart_events > 0 THEN 1 ELSE 0 END) AS sessions_with_cart,
    SUM(CASE WHEN transaction_events > 0 THEN 1 ELSE 0 END) AS sessions_with_transaction
FROM session_facts;
