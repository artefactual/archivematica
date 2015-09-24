-- Add a new microservice chain to optionally store DIPs that currently
-- exist in the uploadedDIPs directory. Modify existing DIP upload links
-- to redirect to this chain after completion, allowing a DIP to be both
-- uploaded and copied to the DIP store.

-- Issue 8895


SET @uploadAtomTail = '651236d2-d77f-4ca7-bfe9-6332e96608ff' COLLATE utf8_unicode_ci;
SET @uploadCdmTail = 'f12ece2c-fb7e-44de-ba87-7e3c5b6feb74' COLLATE utf8_unicode_ci;
SET @uploadAtkTail = 'bb1f1ed8-6c92-46b9-bab6-3a37ffb665f1' COLLATE utf8_unicode_ci;
SET @storeStart = 'ed5d8475-3793-4fb0-a8df-94bd79b26a4c' COLLATE utf8_unicode_ci;

UPDATE MicroServiceChainLinks SET defaultNextChainLink=@storeStart WHERE pk IN (@uploadAtomTail, @uploadCdmTail, @uploadAtkTail);
UPDATE MicroServiceChainLinksExitCodes SET nextmicroservicechainlink = @storeStart where microServiceChainLink IN (@uploadAtomTail, @uploadCdmTail, @uploadAtkTail);
