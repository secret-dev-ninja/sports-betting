CREATE OR REPLACE FUNCTION notify_odds_update() RETURNS TRIGGER AS $$
BEGIN
    -- For events table
    IF TG_TABLE_NAME = 'events' THEN
        PERFORM pg_notify('odds_update', json_build_object(
            'sport_id', NEW.sport_id,
            'event_id', NEW.event_id,
            'home_team', NEW.home_team,
            'away_team', NEW.away_team,
            'table_updated', TG_TABLE_NAME,
            'update_time', CURRENT_TIMESTAMP
        )::text);
    -- For other odds tables
    ELSE 
        PERFORM pg_notify('odds_update', json_build_object(
            'sport_id', e.sport_id,
            'event_id', e.event_id,
            'home_team', e.home_team,
            'away_team', e.away_team,
            'table_updated', TG_TABLE_NAME,
            'update_time', CURRENT_TIMESTAMP
        )::text)
        FROM periods p
        JOIN events e ON e.event_id = p.event_id
        WHERE p.period_id = NEW.period_id;
    END IF;
    
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