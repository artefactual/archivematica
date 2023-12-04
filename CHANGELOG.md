# Changelog

## 1.6.0 onwards

This CHANGELOG is not longer maintained. Please visit the Archivematica wiki for
comprehensive [release notes](https://wiki.archivematica.org/Release_Notes).

## 1.5.0

* Dashboard: always show times in job detail view (<https://github.com/artefactual/archivematica/pull/459>)
* Update to PRONOM v84 ()
* Update to Fido 1.3.4 ()
* Update to Siegfried 1.5.0 (<https://github.com/artefactual/archivematica/pull/458>)
* Archival storage: fix AIP pagination (<https://github.com/artefactual/archivematica/pull/455>)
* Migration: make File.currentLocation nullable (<https://github.com/artefactual/archivematica/pull/454>)
* Dashboard: strip SS API key field, refs #9838 (<https://github.com/artefactual/archivematica/pull/453>)
* Reingest: Do not use formatversion.description to try and match a
  premis:formatRegistryKey entry (<https://github.com/artefactual/archivematica/pull/452>)
* Migration: Fix thumbnail normalization (<https://github.com/artefactual/archivematica/pull/451>)
* AIC fixes (<https://github.com/artefactual/archivematica/pull/450>)
* Dashboard: add gunicorn support (<https://github.com/artefactual/archivematica/pull/449>)
* FITS: Use models not databaseInterface (<https://github.com/artefactual/archivematica/pull/448>)
* Add inherit_notes opt to ArchivesSpace client, refs #9872 (<https://github.com/artefactual/archivematica/pull/447>)
* Storage Service: Add auth to redirect URLs (<https://github.com/artefactual/archivematica/pull/446>)
* Use Format description in premis:formatName (<https://github.com/artefactual/archivematica/pull/445>)
* METS: handle missing metadata entry in structMap (<https://github.com/artefactual/archivematica/pull/444>)
* ArchivesSpace: optional inheritance of notes (<https://github.com/artefactual/archivematica/pull/443>)
* ArchivesSpace: Update ArchivesSpace help text (<https://github.com/artefactual/archivematica/pull/442>)
* Migrations: Update file ID text (<https://github.com/artefactual/archivematica/pull/441>)
* METS: clean up empty metadata dir, refs #8427 (<https://github.com/artefactual/archivematica/pull/440>)
* dbsettings: use database instead of db (<https://github.com/artefactual/archivematica/pull/439>)
* Storage Service: Add API key support (<https://github.com/artefactual/archivematica/pull/438>)
* Rights: fix validation issue, refs #9703 (<https://github.com/artefactual/archivematica/pull/435>)
* Installer: Update storage service setup text (<https://github.com/artefactual/archivematica/pull/434>)
* ArchivesSpace: Location of originals is DIP UUID (<https://github.com/artefactual/archivematica/pull/430>)
* AgentArchives: Handle notes with no content (<https://github.com/artefactual-labs/agentarchives/pull/30>)
* Normalize: fix preservation file UUID to match path on disk (<https://github.com/artefactual/archivematica/pull/427>)
* Dashboard: Fix assumed block size (<https://github.com/artefactual/archivematica/pull/420>)
* ArchivesSpace/ATK DIP Upload Matching GUI improvements (<https://github.com/artefactual/archivematica/pull/419>)
* Store DIP after upload. refs #8995 (<https://github.com/artefactual/archivematica/pull/417>)
* Fix display of transfer rights (<https://github.com/artefactual/archivematica/pull/415>)
* ArchivesSpace DIP Upload: Do not publish location of originals note (<https://github.com/artefactual/archivematica/pull/412>)
* Use Django migrations (<https://github.com/artefactual/archivematica/pull/409>)
* METS: Handle empty rows in metadata.csv (<https://github.com/artefactual/archivematica/pull/404>)
* Don’t autodetect METS mappings (<https://github.com/artefactual/archivematica/pull/403>)
* Auth: Check auth is True, not just truthy (<https://github.com/artefactual/archivematica/pull/385>)
* unitTransfer: tempPath is already a unicode string (<https://github.com/artefactual/archivematica/pull/381>)
* Prepare for move to Django migrations (<https://github.com/artefactual/archivematica/pull/376>)
* ArchivesSpace DIP Upload: Fix copying singlepart notes when creating DOs (<https://github.com/artefactual/archivematica/pull/373>)
* base64: escape invalid UTF-8 characters before encoding (<https://github.com/artefactual/archivematica/pull/367>)
* Make name of database configurable (<https://github.com/artefactual/archivematica/pull/331>)
* Archival Storage: Fix AIP data pagination (<https://github.com/artefactual/archivematica/pull/322>)
* ArchivesSpace DIP Upload enhancements (<https://github.com/artefactual/archivematica/pull/308>)
* Add MySQL Connection Pooling (improve database performance) (<https://github.com/artefactual/archivematica/pull/305>)
* Logging improvements (<https://github.com/artefactual/archivematica/pull/303>)
* change uuid used in determing file format (<https://github.com/artefactual/archivematica/pull/302>)
* Logging: silence verbose libraries in client script logs (<https://github.com/artefactual/archivematica/pull/298>)
* Django ORM fixes (<https://github.com/artefactual/archivematica/pull/296>)
* ArchivesSpace: find_by_field uses new endpoint (<https://github.com/artefactual/archivematica/pull/295>)
* Update fpr-admin commit (disable FPRules) (<https://github.com/artefactual/archivematica/pull/294>)
* filesystem_ajax: return proper exit codes on error (<https://github.com/artefactual/archivematica/pull/292>)
* Backlog search: allow custom error handling (<https://github.com/artefactual/archivematica/pull/290>)
* Decouple renderBacklogSearchForm from originals_browser (<https://github.com/artefactual/archivematica/pull/289>)
* Upload-ArchivesSpace: Only send ArchivesSpace formats (<https://github.com/artefactual/archivematica/pull/286>)
* ArchivesSpace.find_by_field fixes (<https://github.com/artefactual/archivematica/pull/285>)
* copy_to_arrange: "objects" shouldn't be dragged onto arrange root (<https://github.com/artefactual/archivematica/pull/282>)
* Rename endpoint, s/ransfer/transfer (<https://github.com/artefactual/archivematica/pull/275>)
* Make `filepath` parameter to /filesystem/delete/ APIs mandatory (<https://github.com/artefactual/archivematica/pull/270>)
* arrange_contents: fix calling without the `path` parameter (<https://github.com/artefactual/archivematica/pull/268>)
* Initialize Django in MCP client scripts ref. #8879 (<https://github.com/artefactual/archivematica/pull/267>)
* /ingest/backlog/: don’t redirect to self (<https://github.com/artefactual/archivematica/pull/266>)
* Fix FPRClient tests (<https://github.com/artefactual/archivematica/pull/263>)
* Removed vendored requests library (<https://github.com/artefactual/archivematica/pull/262>)
* Add identifier search to ArchivesSpace/ATK upload (<https://github.com/artefactual/archivematica/pull/261>)
* ArchivesSpaceClient: dispatch on resource type properly (<https://github.com/artefactual/archivematica/pull/260>)
* filesystem_ajax: don't try to JSON encode an exception (<https://github.com/artefactual/archivematica/pull/259>)
* ArchivesSpace: Automate matching GUI (<https://github.com/artefactual/archivematica/pull/258>)
* AIP re-ingest (<https://github.com/artefactual/archivematica/pull/257>)
* Tests: Use an in-memory database (<https://github.com/artefactual/archivematica/pull/256>)
* Specify python2 in shebangs.  Python version choice respects path. <https://github.com/artefactual/archivematica/pull/255>
* Jobs: Always show arguments (<https://github.com/artefactual/archivematica/pull/254>)
* Dashboard logs: use GroupWriteRotatingFileHandler (<https://github.com/artefactual/archivematica/pull/253>)
* Fix archival storage display of deletion requests (<https://github.com/artefactual/archivematica/pull/251>)
* Dependencies: Improve SSL dependencies (<https://github.com/artefactual/archivematica/pull/250>)
* templatetags: fix active tag when unhandled exception raised (<https://github.com/artefactual/archivematica/pull/248>)
* MCPServer: Log all exceptions, use ReplacementDict.replace (<https://github.com/artefactual/archivematica/pull/247>)
* ArchivesSpace integration (<https://github.com/artefactual/archivematica/pull/185>)
* Hierarchical DIP support (<https://github.com/artefactual/archivematica/pull/130>)
* Update to Django 1.7 (<https://github.com/artefactual/archivematica/pull/124>)

## 1.4.1

* Fix "active" templatetag when Django handles an uncaught exception
* Fix updating AIP records after marking files as deleted in archival storage (#8533)
* Fix querying for deleted AIPs (#8533)
* Fix marking AIPs as stored after deletion is rejected (#8533)
* MCPServer: log all exceptions (#8509)
* MCPServer: remove duplicate ReplacementDict code (#8509)
* Dashboard: use GroupWriteRotatingFileHandler to ensure group-writeability of
  rotated logs (#8587)

## 1.4.0

* Remove unused Elasticsearch backup code (#8076)
* Improve performance of indexing AIP by saving uncompressed METS (#7424)
* Index MODS identifiers in Elasticsearch (#7424)
* Track file events in transfer METS using amdSecs (#7714)
* Add a new "processed structMap" which captures the transfer's final state (#7714)
* Use the Storage Service, not Elasticsearch, to look up file metadata in SIP
  arrange (#7714)
* Improve Dublin Core namespacing for metadata generated from metadata.csv and
  from template (#8007)
* Display additional metadata (number of files, size) from the storage service (#7853)
* Accession IDs associate with Transfers again (#7442)
* Remove Elasticsearch tool that is now maintained in archivematica-devtools
* Log exceptions in start_transfer (#8117)
* Archivist's Toolkit upload: use SQL placeholders instead of string
  interpolation (#7771)
* Fail SIP if checksum verification fails (#8825)
* Move logs to /var/archivematica/sharedDirectory; separate dashboard logs into
  its own file (#6647)
* Handle linking_agent as an integer, not a foreign key, in Django models (#8230)
* Index MODS identifiers in the aips/aipfile index (#8266)
* Fix bag transfer names (#8229)
* DSpace transfer type accepts either files or folders
* Include the contents of bag-info.txt in AIP METS as <transfer_metata> (#8177)
* Enable autodetection of date fields when indexing METS contents (#8181)
* Add support for searching on the contents of transfer_metadata in archival
  storage (#8181)
* Add support for searching date ranges in archival storage (#8181)
* Improve text in stderr from Transcribe microservice (#7051)
* Add preliminary support for Siegfried as an identification tool (#8287)
* Ignore non-Unicode data contained in metadata.csv files (#7277)
* Fix blank Keyword ("term") queries in archival storage and transfer backlog (#8292)
* Fix default value of "query type" dropdown in archival storage and transfer
  backlog (#8292)
* Allow DIP choices to be preconfigured (#7321)
* Search: restrict nested fields searched when using string searches (#8338)
* Elasticsearch: fix exception handling (#4757)
* Search: replace "term" queries with "multi_match" queries (#8343)
* taskStandard: refactor stdout/stderr string writing (#8404)
* Advanced search: improve handling of queries with conditions other than "or" (#8401)
* Buildscripts: touch a file to indicate mysql_dev has been run
* METS Rights: fix model attribute name, XML generation (#8425)
* verifyMD5: fix group type, hardcode "checksum" filename (#8415)
* verifyMD5: fix event UUID (#8424)
* verifyMD5: event type string is now "fixity check", not "fixity" (#8443)
* createEventsForGroup: fix SQL query
* SQL: use placeholders instead of interpolating values into SQL statements (#4901)
* Remove client-specific Archivist's Toolkit upload script
* Remove unused code
* xml2obj: Fix handling of METS files containing sourceMD elements (#8431)
