package servercmd

import (
	"io"

	"github.com/artefactual/archivematica/hack/ccp/internal/api/admin"
	"github.com/artefactual/archivematica/hack/ccp/internal/rootcmd"
)

type Config struct {
	rootConfig *rootcmd.Config
	out        io.Writer
	sharedDir  string
	workflow   string
	db         databaseConfig
	api        apiConfig
	gearmin    gearminConfig
}

type databaseConfig struct {
	driver string
	dsn    string
}

type apiConfig struct {
	admin admin.Config
}

type gearminConfig struct {
	addr string
}
