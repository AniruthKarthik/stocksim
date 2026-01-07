-- Fix for existing game_sessions table to remove the unique constraint
DO $$ 
BEGIN 
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'game_sessions_portfolio_id_key') THEN
        ALTER TABLE game_sessions DROP CONSTRAINT game_sessions_portfolio_id_key;
    END IF;
END $$;
