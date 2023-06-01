CREATE OR REPLACE FUNCTION check_timing_enabled() RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT timing_enabled FROM trackers WHERE tracker_id = 
        (SELECT tracker_id FROM tracker_records WHERE record_id = NEW.record_id)) = FALSE THEN
        RAISE EXCEPTION 'Cannot insert timing record for a tracker without timing enabled';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER timing_insert_trigger
BEFORE INSERT ON timing_records
FOR EACH ROW
EXECUTE PROCEDURE check_timing_enabled();

CREATE OR REPLACE FUNCTION update_tracker(session_id_in VARCHAR, tracker_id_in INTEGER, alias_in VARCHAR, description_in TEXT)
RETURNS VOID AS $$
DECLARE
    user_id INTEGER;
BEGIN
    -- 获取session_id对应的用户id
    SELECT user_id INTO user_id FROM users WHERE session_id = session_id_in;

    -- 如果用户id与追踪器的所有者匹配，则更新追踪器
    IF EXISTS (SELECT 1 FROM trackers WHERE tracker_id = tracker_id_in AND user_id = user_id) THEN
        UPDATE trackers SET alias = alias_in, description = description_in WHERE tracker_id = tracker_id_in;
    ELSE
        RAISE EXCEPTION 'User does not own the tracker.';
    END IF;
END;
$$ LANGUAGE plpgsql;
