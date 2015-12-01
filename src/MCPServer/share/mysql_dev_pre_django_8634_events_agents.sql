-- Make Events and Agents many-to-many

-- Fix Agents & Events pk type
ALTER TABLE Agents MODIFY COLUMN pk integer AUTO_INCREMENT NOT NULL;
ALTER TABLE Events MODIFY COLUMN pk integer AUTO_INCREMENT NOT NULL;
