-- Continue processing if a file fails to be identified, like
-- other identification services
-- Fixes #7603
--
-- Metadata
UPDATE MicroServiceChainLinks SET defaultNextChainLink='04493ab2-6cad-400d-8832-06941f121a96' WHERE pk='b2444a6e-c626-4487-9abc-1556dd89a8ae';
-- Submission documentation
UPDATE MicroServiceChainLinks SET defaultNextChainLink='33d7ac55-291c-43ae-bb42-f599ef428325' WHERE pk='1dce8e21-7263-4cc4-aa59-968d9793b5f2';
