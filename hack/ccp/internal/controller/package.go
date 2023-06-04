package controller

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"sync"

	"github.com/artefactual/archivematica/hack/ccp/internal/processing"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/google/uuid"
)

type Package struct {
	path      string
	base      string
	name      string
	watchedAt *workflow.WatchedDirectory
	decision  chan uuid.UUID
	once      sync.Once
	driver    packageDriver
}

func NewPackage(path string, wd *workflow.WatchedDirectory) *Package {
	base, name := filepath.Split(path)
	return &Package{
		path:      path,
		base:      base,
		name:      name,
		watchedAt: wd,
		decision:  make(chan uuid.UUID),
	}
}

func (p Package) String() string {
	return p.name
}

func (p Package) PreconfiguredChoice(linkID uuid.UUID) (*processing.Choice, error) {
	f, err := os.Open(filepath.Join(p.path, "processingMCP.xml"))
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	// TODO: this could be cached if the file isn't going to change.
	choices, err := processing.ParseConfig(f)
	if err != nil {
		return nil, err
	}

	for _, choice := range choices {
		if choice.AppliesTo == linkID.String() {
			return &choice, nil
		}
	}

	return nil, nil
}

func (p *Package) ResolveDecision(decision uuid.UUID) error {
	select {
	case p.decision <- decision:
		return nil
	default:
		return errors.New("can't resolve")
	}
}

func (p *Package) AwaitDecision(ctx context.Context) (uuid.UUID, error) {
	for {
		select {
		case d := <-p.decision:
			return d, nil
		case <-ctx.Done():
			return uuid.Nil, ctx.Err()
		}
	}
}

type packageDriver interface {
	reload() error
}

type transfer struct{}

func (p *transfer) reload() error { return nil }

type dip struct{}

func (p *dip) reload() error { return nil }

type sip struct{}

func (p *sip) reload() error { return nil }
