DROP table IF EXISTS atk_collection;

CREATE TABLE atk_collection (
  resourceid INT(10),
  title varchar(255),
  dateExpression varchar(255)
);

INSERT INTO atk_collection (resourceid,title,dateExpression) VALUES (31,"Foundation for Child Development records","1898, 1902, 1907, 1909-1910, 1912-1998, bulk 1960-1998");
INSERT INTO atk_collection (resourceid,title,dateExpression) VALUES (827,"John D. Rockefeller papers","Bulk, 1879-1894 1855-1942 (bulk 1879-1894)");
INSERT INTO atk_collection (resourceid,title,dateExpression) VALUES (18983, "Ford Foundation records, Peace & Social Justice Program (PSJ), Human Rights and International Cooperation (HRIC), Office Files of Alan Jenkins","1995-2001");
INSERT INTO atk_collection (resourceid,title,dateExpression) VALUES (19020,"Dorothy I. Parker papers","1932-1985");
INSERT INTO atk_collection (resourceid,title,dateExpression) VALUES (19157,"Ford Foundation records, International Division, Office Files of Elinor Barber","1967-1981");

DROP TABLE IF EXISTS atk_description;

CREATE TABLE atk_description (
  resourceComponentId INT(10),
  parentResourceComponentId INT(10),
  persistentID varchar(255),
  resourceLevel VARCHAR(50),
  dateExpression VARCHAR(255),
  title varchar(255)
);

INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (61857,  null, 'ref1825', 'series', '', 'Audio-Visual Materials');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (61858, null, 'ref1770', 'series', '1954-1974', 'Reprints');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (62573, null, 'ref1069', 'series', '1911, 1946-1996 bulk 1960-1996', 'Grant Programs');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (62686, null, 'ref953', 'series', '1964-1992, 1996', 'Financial Records');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (62687, null, 'ref661', 'series', '1898-1998', 'Annual Reports');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (63451, null, 'ref11', 'series', '1950-1996', 'Administration');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (62833, 63451, 'ref640', 'subseries', "1975-1996", "Administration - President's Files, Barbara Blum");
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (62992, 63451, 'ref495', 'subseries', '1951-1996', 'Administration - Council');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (62993, 63451, 'ref377', 'subseries', '1950-1992, 1996', 'Administration - Committees');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (63107, 63451, 'ref14', 'subseries', '1951-1996', 'Administration - Board of Directors Meetings');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (63263, 63107, 'ref205', 'file', 'March 16, 1964', '');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (3264, 63107, 'ref204', 'file', 'October 22, 1963', '');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (63265, 63107, 'ref203', 'file', 'May 28, 1963', '');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (63266, 63107, 'ref202', 'file', 'April 23, 1963', 'Annual Meeting');
INSERT INTO atk_description (resourceComponentId, parentResourceComponentId, persistentID, resourceLevel, dateExpression, title) VALUES (63295, 63107, 'ref173', 'file', 'May 16, 1951, May 16, 1951', '');

