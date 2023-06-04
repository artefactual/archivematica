// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.18.0

package mysql

import (
	"database/sql"
	"time"

	uuid "github.com/google/uuid"
)

type Access struct {
	ID         int32
	SIPID      uuid.UUID
	Resource   string
	Target     string
	Status     string
	Statuscode sql.NullInt32
	Exitcode   sql.NullInt32
	CreatedAt  time.Time
	UpdatedAt  time.Time
}

type Agent struct {
	ID                   int32
	Agentidentifiertype  sql.NullString
	Agentidentifiervalue sql.NullString
	Agentname            sql.NullString
	Agenttype            string
}

type ArchivesSpaceDIPObjectResourcePairing_row struct {
	ID         int32
	Dipuuid    uuid.UUID
	Fileuuid   uuid.UUID
	Resourceid string
}

type AuthGroupPermission struct {
	ID           int32
	GroupID      int32
	PermissionID int32
}

type AuthUserGroup struct {
	ID      int32
	UserID  int32
	GroupID int32
}

type AuthUserUserPermission struct {
	ID           int32
	UserID       int32
	PermissionID int32
}

type Dashboardsetting struct {
	ID           int32
	Name         string
	Value        string
	Lastmodified time.Time
	Scope        string
}

type Derivation struct {
	ID               int32
	Derivedfileuuid  uuid.UUID
	Relatedeventuuid uuid.UUID
	Sourcefileuuid   uuid.UUID
}

type DirectoriesIdentifier struct {
	ID           int32
	DirectoryID  string
	IdentifierID int32
}

type Directory struct {
	Directoryuuid    uuid.UUID
	Originallocation []byte
	Currentlocation  sql.NullString
	Enteredsystem    time.Time
	SIPID            uuid.UUID
	Transferuuid     uuid.UUID
}

type DjangoMigration struct {
	ID      int32
	App     string
	Name    string
	Applied time.Time
}

type Dublincore_row struct {
	ID                          int32
	Metadataappliestoidentifier sql.NullString
	Title                       string
	Ispartof                    string
	Creator                     string
	Subject                     string
	Description                 string
	Publisher                   string
	Contributor                 string
	Date                        string
	Type                        string
	Format                      string
	Identifier                  string
	Source                      string
	Relation                    string
	Language                    string
	Coverage                    string
	Rights                      string
	Metadataappliestotype       string
	Status                      string
}

type Event struct {
	ID                     int32
	Eventidentifieruuid    uuid.UUID
	Eventtype              string
	Eventdatetime          time.Time
	Eventdetail            string
	Eventoutcome           string
	Eventoutcomedetailnote string
	Fileuuid               uuid.UUID
}

type EventsAgent struct {
	ID      int32
	EventID int32
	AgentID int32
}

type File struct {
	Fileuuid         uuid.UUID
	Originallocation []byte
	Currentlocation  sql.NullString
	Filegrpuse       string
	Filegrpuuid      uuid.UUID
	Checksum         string
	Filesize         sql.NullInt64
	Label            string
	Enteredsystem    time.Time
	Removedtime      sql.NullTime
	SIPID            uuid.UUID
	Transferuuid     uuid.UUID
	Checksumtype     string
	Modificationtime sql.NullTime
}

type FilesIdentifier struct {
	ID           int32
	FileID       string
	IdentifierID int32
}

type Filesid struct {
	ID                 int32
	Formatname         string
	Formatversion      string
	Formatregistryname string
	Formatregistrykey  string
	Fileuuid           uuid.UUID
}

type Filesidentifiedid struct {
	ID       int32
	Fileuuid uuid.UUID
	Fileid   string
}

type Identifier struct {
	ID    int32
	Type  sql.NullString
	Value sql.NullString
}

type Job struct {
	ID                       uuid.UUID
	Type                     string
	CreatedAt                time.Time
	Createdtimedec           string
	Directory                string
	SIPID                    uuid.UUID
	Unittype                 string
	Currentstep              int32
	Microservicegroup        string
	Hidden                   bool
	Subjobof                 string
	Microservicechainlinkspk sql.NullString
}

type Metadataappliestotype struct {
	ID           string
	Description  string
	Replaces     sql.NullString
	Lastmodified time.Time
}

type Report struct {
	ID             int32
	Unittype       string
	Unitname       string
	Unitidentifier string
	Content        string
	Created        time.Time
}

type RightsStatementCopyrightDocumentationIdentifier_row struct {
	ID                                    int32
	Copyrightdocumentationidentifiertype  string
	Copyrightdocumentationidentifiervalue string
	Copyrightdocumentationidentifierrole  sql.NullString
	Fkrightsstatementcopyrightinformation int32
}

type RightsStatementCopyrightNote_row struct {
	ID                                    int32
	Copyrightnote                         string
	Fkrightsstatementcopyrightinformation int32
}

type RightsStatementCopyright_row struct {
	ID                               int32
	Copyrightstatus                  string
	Copyrightjurisdiction            string
	Copyrightstatusdeterminationdate sql.NullString
	Copyrightapplicablestartdate     sql.NullString
	Copyrightapplicableenddate       sql.NullString
	Copyrightapplicableenddateopen   bool
	Fkrightsstatement                int32
}

type RightsStatementLicenseDocumentationIdentifier_row struct {
	ID                                  int32
	Licensedocumentationidentifiertype  string
	Licensedocumentationidentifiervalue string
	Licensedocumentationidentifierrole  sql.NullString
	Fkrightsstatementlicense            int32
}

type RightsStatementLicenseNote_row struct {
	ID                       int32
	Licensenote              string
	Fkrightsstatementlicense int32
}

type RightsStatementLicense_row struct {
	ID                           int32
	Licenseterms                 sql.NullString
	Licenseapplicablestartdate   sql.NullString
	Licenseapplicableenddate     sql.NullString
	Licenseapplicableenddateopen bool
	Fkrightsstatement            int32
}

type RightsStatementLinkingAgentIdentifier_row struct {
	ID                          int32
	Linkingagentidentifiertype  string
	Linkingagentidentifiervalue string
	Fkrightsstatement           int32
}

type RightsStatementOtherRightsDocumentationIdentifier_row struct {
	ID                                      int32
	Otherrightsdocumentationidentifiertype  string
	Otherrightsdocumentationidentifiervalue string
	Otherrightsdocumentationidentifierrole  sql.NullString
	Fkrightsstatementotherrightsinformation int32
}

type RightsStatementOtherRightsInformation_row struct {
	ID                               int32
	Otherrightsbasis                 string
	Otherrightsapplicablestartdate   sql.NullString
	Otherrightsapplicableenddate     sql.NullString
	Otherrightsapplicableenddateopen bool
	Fkrightsstatement                int32
}

type RightsStatementOtherRightsNote_row struct {
	ID                                      int32
	Otherrightsnote                         string
	Fkrightsstatementotherrightsinformation int32
}

type RightsStatementRightsGrantedNote_row struct {
	ID                             int32
	Rightsgrantednote              string
	Fkrightsstatementrightsgranted int32
}

type RightsStatementRightsGrantedRestriction_row struct {
	ID                             int32
	Restriction                    string
	Fkrightsstatementrightsgranted int32
}

type RightsStatementRightsGranted_row struct {
	ID                int32
	Act               string
	Startdate         sql.NullString
	Enddate           sql.NullString
	Enddateopen       bool
	Fkrightsstatement int32
}

type RightsStatementStatuteDocumentationIdentifier_row struct {
	ID                                  int32
	Statutedocumentationidentifiertype  string
	Statutedocumentationidentifiervalue string
	Statutedocumentationidentifierrole  sql.NullString
	Fkrightsstatementstatuteinformation int32
}

type RightsStatementStatuteInformationNote_row struct {
	ID                                  int32
	Statutenote                         string
	Fkrightsstatementstatuteinformation int32
}

type RightsStatementStatuteInformation_row struct {
	ID                                  int32
	Statutejurisdiction                 string
	Statutecitation                     string
	Statuteinformationdeterminationdate sql.NullString
	Statuteapplicablestartdate          sql.NullString
	Statuteapplicableenddate            sql.NullString
	Statuteapplicableenddateopen        bool
	Fkrightsstatement                   int32
}

type RightsStatement_row struct {
	ID                             int32
	Metadataappliestoidentifier    string
	Rightsstatementidentifiertype  string
	Rightsstatementidentifiervalue string
	Fkagent                        int32
	Rightsbasis                    string
	Metadataappliestotype          string
	Status                         string
}

type Sip struct {
	SIPID       uuid.UUID
	CreatedAt   time.Time
	Currentpath sql.NullString
	Hidden      bool
	Aipfilename sql.NullString
	Siptype     string
	Diruuids    bool
	CompletedAt sql.NullTime
	Status      int32
}

type SipsIdentifier struct {
	ID           int32
	SipID        string
	IdentifierID int32
}

type Task struct {
	Taskuuid  uuid.UUID
	CreatedAt time.Time
	Fileuuid  uuid.UUID
	Filename  string
	Exec      string
	Arguments string
	Starttime sql.NullTime
	Endtime   sql.NullTime
	Client    string
	Stdout    string
	Stderror  string
	Exitcode  sql.NullInt64
	ID        uuid.UUID
}

type Taxonomy struct {
	ID        string
	CreatedAt sql.NullTime
	Name      string
	Type      string
}

type Taxonomyterm struct {
	ID           string
	CreatedAt    sql.NullTime
	Term         string
	Taxonomyuuid uuid.UUID
}

type Transfer struct {
	Transferuuid               uuid.UUID
	Currentlocation            string
	Type                       string
	Accessionid                string
	Sourceofacquisition        string
	Typeoftransfer             string
	Description                string
	Notes                      string
	Hidden                     bool
	Transfermetadatasetrowuuid uuid.UUID
	Diruuids                   bool
	AccessSystemID             string
	CompletedAt                sql.NullTime
	Status                     int32
}

type Transfermetadatafield struct {
	ID                 string
	CreatedAt          sql.NullTime
	Fieldlabel         string
	Fieldname          string
	Fieldtype          string
	Sortorder          int32
	Optiontaxonomyuuid uuid.UUID
}

type Transfermetadatafieldvalue struct {
	ID         string
	CreatedAt  time.Time
	Fieldvalue string
	Fielduuid  uuid.UUID
	Setuuid    uuid.UUID
}

type Transfermetadataset struct {
	ID              string
	CreatedAt       time.Time
	Createdbyuserid int32
}

type Unitvariable struct {
	ID                    string
	Unittype              sql.NullString
	Unituuid              uuid.UUID
	Variable              sql.NullString
	Variablevalue         sql.NullString
	CreatedAt             time.Time
	UpdatedAt             time.Time
	Microservicechainlink sql.NullString
}

type auth_group_row struct {
	ID   int32
	Name string
}

type auth_permission_row struct {
	ID            int32
	Name          string
	ContentTypeID int32
	Codename      string
}

type auth_user_row struct {
	ID          int32
	Password    string
	LastLogin   sql.NullTime
	IsSuperuser bool
	Username    string
	FirstName   string
	LastName    string
	Email       string
	IsStaff     bool
	IsActive    bool
	DateJoined  time.Time
}

type django_content_type_row struct {
	ID       int32
	AppLabel string
	Model    string
}

type django_session_row struct {
	SessionKey  string
	SessionData string
	ExpireDate  time.Time
}

type fpr_format_row struct {
	ID          int32
	UUID        uuid.UUID
	Description string
	Slug        string
	GroupID     sql.NullString
}

type fpr_formatgroup_row struct {
	ID          int32
	UUID        uuid.UUID
	Description string
	Slug        string
}

type fpr_formatversion_row struct {
	ID                 int32
	Enabled            bool
	Lastmodified       time.Time
	UUID               uuid.UUID
	Version            sql.NullString
	PronomID           sql.NullString
	Description        sql.NullString
	AccessFormat       bool
	PreservationFormat bool
	Slug               string
	FormatID           sql.NullString
	ReplacesID         sql.NullString
}

type fpr_fpcommand_row struct {
	ID                    int32
	Enabled               bool
	Lastmodified          time.Time
	UUID                  uuid.UUID
	Description           string
	Command               string
	ScriptType            string
	OutputLocation        sql.NullString
	CommandUsage          string
	EventDetailCommandID  sql.NullString
	OutputFormatID        sql.NullString
	ReplacesID            sql.NullString
	ToolID                sql.NullString
	VerificationCommandID sql.NullString
}

type fpr_fprule_row struct {
	ID            int32
	Enabled       bool
	Lastmodified  time.Time
	UUID          uuid.UUID
	Purpose       string
	CountAttempts int32
	CountOkay     int32
	CountNotOkay  int32
	CommandID     string
	FormatID      string
	ReplacesID    sql.NullString
}

type fpr_fptool_row struct {
	ID          int32
	UUID        uuid.UUID
	Description string
	Version     string
	Enabled     bool
	Slug        string
}

type fpr_idcommand_row struct {
	ID           int32
	Enabled      bool
	Lastmodified time.Time
	UUID         uuid.UUID
	Description  string
	Config       string
	Script       string
	ScriptType   string
	ReplacesID   sql.NullString
	ToolID       sql.NullString
}

type fpr_idrule_row struct {
	ID            int32
	Enabled       bool
	Lastmodified  time.Time
	UUID          uuid.UUID
	CommandOutput string
	CommandID     string
	FormatID      string
	ReplacesID    sql.NullString
}

type fpr_idtool_row struct {
	ID          int32
	UUID        uuid.UUID
	Description string
	Version     string
	Enabled     bool
	Slug        string
}

type main_archivesspacedigitalobject_row struct {
	ID         int32
	Resourceid string
	Label      string
	Title      string
	Started    bool
	Remoteid   string
	SipID      sql.NullString
}

type main_fpcommandoutput_row struct {
	ID       int32
	Content  sql.NullString
	Fileuuid uuid.UUID
	Ruleuuid uuid.UUID
}

type main_levelofdescription_row struct {
	ID        string
	Name      string
	Sortorder int32
}

type main_siparrange_row struct {
	ID                 int32
	OriginalPath       sql.NullString
	ArrangePath        []byte
	FileUuid           uuid.UUID
	TransferUuid       uuid.UUID
	SipCreated         bool
	AipCreated         bool
	LevelOfDescription string
	SipID              sql.NullString
}

type main_siparrangeaccessmapping_row struct {
	ID          int32
	ArrangePath string
	System      string
	Identifier  string
}

type main_userprofile_row struct {
	ID           int32
	AgentID      int32
	UserID       int32
	SystemEmails bool
}

type tastypie_apiaccess_row struct {
	ID            int32
	Identifier    string
	Url           string
	RequestMethod string
	Accessed      int32
}

type tastypie_apikey_row struct {
	ID      int32
	Key     string
	Created time.Time
	UserID  int32
}