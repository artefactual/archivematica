package servercmd

import (
	"io"

	"github.com/artefactual/archivematica/hack/ccp/internal/rootcmd"
)

type Config struct {
	rootConfig *rootcmd.Config
	out        io.Writer
	sharedDir  string
}
