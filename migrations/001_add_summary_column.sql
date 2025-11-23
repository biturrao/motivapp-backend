-- Migration: Add summary column to user_profiles table
-- Date: 2025-11-20
-- Description: Adds a summary column to cache AI-generated profile summaries

-- Add the summary column
ALTER TABLE user_profiles 
ADD COLUMN summary TEXT NULL;

-- Add comment to document the column
COMMENT ON COLUMN user_profiles.summary IS 'Cached AI-generated profile summary to reduce token usage';
