dev (1.5.0)
===========

* Fix "active" templatetag when Django handles an uncaught exception
* Fix updating AIP records after marking files as deleted in archival storage (#8533)
* Fix querying for deleted AIPs (#8533)
* Fix marking AIPs as stored after deletion is rejected (#8533)
* MCPServer: log all exceptions (#8509)
* MCPServer: remove duplicate ReplacementDict code (#8509)
* Dashboard: use GroupWriteRotatingFileHandler to ensure group-writeability of rotated logs (#8587)
* Dashboard: always show arguments in job detail view
* Tests: Use an in-memory database
* Specify python2 in shebangs.  Python version choice respects path.

1.4.0
=====

* Remove unused Elasticsearch backup code (#8076)
* Improve performance of indexing AIP by saving uncompressed METS (#7424)
* Index MODS identifiers in Elasticsearch (#7424)
* Track file events in transfer METS using amdSecs (#7714)
* Add a new "processed structMap" which captures the transfer's final state (#7714)
* Use the Storage Service, not Elasticsearch, to look up file metadata in SIP arrange (#7714)
* Improve Dublin Core namespacing for metadata generated from metadata.csv and from template (#8007)
* Display additional metadata (number of files, size) from the storage service (#7853)
* Accession IDs associate with Transfers again (#7442)
* Remove Elasticsearch tool that is now maintained in archivematica-devtools
* Log exceptions in start_transfer (#8117)
* Archivist's Toolkit upload: use SQL placeholders instead of string interpolation (#7771)
* Fail SIP if checksum verification fails (#8825)
* Move logs to /var/archivematica/sharedDirectory; separate dashboard logs into its own file (#6647)
* Handle linking_agent as an integer, not a foreign key, in Django models (#8230)
* Index MODS identifiers in the aips/aipfile index (#8266)
* Fix bag transfer names (#8229)
* DSpace transfer type accepts either files or folders
* Include the contents of bag-info.txt in AIP METS as <transfer_metata> (#8177)
* Enable autodetection of date fields when indexing METS contents (#8181)
* Add support for searching on the contents of transfer_metadata in archival storage (#8181)
* Add support for searching date ranges in archival storage (#8181)
* Improve text in stderr from Transcribe microservice (#7051)
* Add preliminary support for Siegfried as an identification tool (#8287)
* Ignore non-Unicode data contained in metadata.csv files (#7277)
* Fix blank Keyword ("term") queries in archival storage and transfer backlog (#8292)
* Fix default value of "query type" dropdown in archival storage and transfer backlog (#8292)
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
