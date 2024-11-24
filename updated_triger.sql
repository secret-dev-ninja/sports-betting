CREATE OR REPLACE FUNCTION notify_odds_update() RETURNS TRIGGER AS $$
DECLARE
    result_json JSON;
BEGIN
    -- Build the JSON structure
    SELECT json_build_object(
        'sport_id', e.sport_id,
        'event_id', e.event_id,
        'home_team', e.home_team,
        'away_team', e.away_team,
        'table_updated', TG_TABLE_NAME,
        'update_time', CURRENT_TIMESTAMP,
        'data', json_agg(
            json_build_object(
                p.period_id::text, -- Use period_id as the key
                json_build_object(
                    'total', (
                        SELECT json_agg(row_to_json(tl))
                        FROM totals tl
                        WHERE tl.period_id = p.period_id
                    ),
                    'money_lines', (
                        SELECT json_agg(row_to_json(ml))
                        FROM money_lines ml
                        WHERE ml.period_id = p.period_id
                    ),
                    'spread', (
                        SELECT json_agg(row_to_json(sp))
                        FROM spreads sp
                        WHERE sp.period_id = p.period_id
                    )
                )
            )
        )
    )
    INTO result_json
    FROM events e
    JOIN periods p ON p.event_id = e.event_id
    WHERE e.event_id = NEW.event_id;

    -- Notify with the generated JSON
    PERFORM pg_notify('odds_update', result_json::text);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate triggers
DROP TRIGGER IF EXISTS odds_update_trigger ON events;
DROP TRIGGER IF EXISTS odds_update_trigger ON periods;
DROP TRIGGER IF EXISTS odds_update_trigger ON money_lines;
DROP TRIGGER IF EXISTS odds_update_trigger ON spreads;
DROP TRIGGER IF EXISTS odds_update_trigger ON totals;
DROP TRIGGER IF EXISTS odds_update_trigger ON team_totals;

CREATE TRIGGER odds_update_trigger AFTER INSERT OR UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION notify_odds_update();

CREATE TRIGGER odds_update_trigger AFTER INSERT ON money_lines
    FOR EACH ROW EXECUTE FUNCTION notify_odds_update();
    
CREATE TRIGGER odds_update_trigger AFTER INSERT ON spreads
    FOR EACH ROW EXECUTE FUNCTION notify_odds_update();
    
CREATE TRIGGER odds_update_trigger AFTER INSERT ON totals
    FOR EACH ROW EXECUTE FUNCTION notify_odds_update();
    
CREATE TRIGGER odds_update_trigger AFTER INSERT ON team_totals
    FOR EACH ROW EXECUTE FUNCTION notify_odds_update();