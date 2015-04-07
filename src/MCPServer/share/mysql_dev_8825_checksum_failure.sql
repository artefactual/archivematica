-- Verify PREMIS checksums - set default link to "email fail report",
-- rather than continuing to the next microservice
UPDATE MicroServiceChainLinks
	SET defaultNextChainLink='7d728c39-395f-4892-8193-92f086c0546f'
	WHERE pk='88807d68-062e-4d1a-a2d5-2d198c88d8ca';
