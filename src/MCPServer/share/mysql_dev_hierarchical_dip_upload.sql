-- Set AtoM DIP upload defaults
INSERT INTO DashboardSettings (name, value) VALUES ('dip_upload_atom_url', 'http://localhost/atom');
INSERT INTO DashboardSettings (name, value) VALUES ('dip_upload_atom_email', 'demo@example.com');
INSERT INTO DashboardSettings (name, value) VALUES ('dip_upload_atom_password', 'demo');
INSERT INTO DashboardSettings (name, value) VALUES ('dip_upload_atom_version', '2');
UPDATE StandardTasksConfigs SET arguments='--url=\"http://localhost/atom/index.php\" \\\r\n--email=\"demo@example.com\" \\\r\n--password=\"demo\" \\\r\n--uuid=\"%SIPUUID%\" \\\r\n--rsync-target=\"/tmp\" --version=2' WHERE pk='ee80b69b-6128-4e31-9db4-ef90aa677c87';

-- New LevelOfDescription table will be created by syncdb automatically, since it is a new table
-- Update SIPArrange table, since syncdb will not modify an existing table
ALTER TABLE main_siparrange ADD sip_id varchar(36) COLLATE utf8_unicode_ci DEFAULT NULL AFTER transfer_uuid, ADD level_of_description varchar(2014) COLLATE utf8_unicode_ci NOT NULL AFTER sip_id;
ALTER TABLE main_siparrange ADD FOREIGN KEY (sip_id) REFERENCES SIPs(sipUUID);
