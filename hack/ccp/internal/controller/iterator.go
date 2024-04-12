package controller

import (
	"context"
	"errors"
	"fmt"
	"io"

	"github.com/go-logr/logr"
	"github.com/google/uuid"
	"github.com/sevein/gearmin"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

var errWait = errors.New("wait")

// Iterator carries a package through all its workflow.
type Iterator struct {
	logger logr.Logger

	gearman *gearmin.Server

	wf *workflow.Document

	p *Package

	startAt uuid.UUID

	chain *workflow.Chain

	waitCh chan waitSignal
}

func NewIterator(logger logr.Logger, gearman *gearmin.Server, wf *workflow.Document, p *Package) *Iterator {
	iter := &Iterator{
		logger:  logger,
		gearman: gearman,
		wf:      wf,
		p:       p,
		startAt: p.watchedAt.ChainID,
		waitCh:  make(chan waitSignal, 10),
	}

	return iter
}

func (i *Iterator) Process(ctx context.Context) error {
	next := i.startAt

	for {
		select {
		case <-ctx.Done():
			return nil
		default:
			n, err := i.runJob(ctx, next)
			if err == io.EOF {
				return nil
			}
			if err == errWait {
				nnn, waitErr := i.wait(ctx) // puts the loop on hold.
				if waitErr != nil {
					return waitErr
				}
				next = nnn
				continue
			}
			if err != nil {
				return err
			}
			next = n
		}
	}
}

// runJob processes a job given the identifier of a workflow chain or link.
func (i *Iterator) runJob(ctx context.Context, id uuid.UUID) (uuid.UUID, error) {
	if chain, ok := i.wf.Chains[id]; ok {
		i.logger.Info("Processing job.", "type", "chain", "id", id, "desc", chain.Description["en"])
		i.chain = chain
		return chain.LinkID, nil
	}

	wl, ok := i.wf.Links[id]
	i.logger.Info("Processing job.", "type", "link", "id", id, "desc", wl.Description, "manager", wl.Manager)
	if !ok {
		return uuid.Nil, fmt.Errorf("link %s couldn't be found", id)
	}
	if wl.End {
		return uuid.Nil, io.EOF
	}

	s, err := i.buildJob(wl)
	if err != nil {
		return uuid.Nil, fmt.Errorf("link %s couldn't be built: %v", id, err)
	}

	next, err := s.exec(ctx)
	if err != nil {
		if err == io.EOF {
			return uuid.Nil, err
		}
		return uuid.Nil, fmt.Errorf("link %s couldn't be executed: %v", id, err)
	}

	// Workflow needs to be reactivated by another watched directory.
	if next == uuid.Nil {
		return uuid.Nil, errWait
	}

	return next, nil
}

// buildJob configures a workflow job given the workflow chain link definition.
func (i *Iterator) buildJob(wl *workflow.Link) (j job, err error) {
	switch wl.Manager {

	// Decision jobs - handles workflow decision points.
	case "linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList":
		logger := i.logger.WithName("outputDecisionJob")
		j, err = newOutputDecisionJob(logger, i.p, wl)
	case "linkTaskManagerChoice":
		logger := i.logger.WithName("nextChainDecisionJob")
		j, err = newNextChainDecisionJob(logger, i.p, wl)
	case "linkTaskManagerReplacementDicFromChoice":
		logger := i.logger.WithName("updateContextDecisionJob")
		j, err = newUpdateContextDecisionJob(logger, i.p, wl)

	// Executable jobs - dispatched to the worker pool.
	case "linkTaskManagerDirectories":
		logger := i.logger.WithName("directoryClientScriptJob")
		j, err = newDirectoryClientScriptJob(logger, i.gearman, i.p, wl)
	case "linkTaskManagerFiles":
		logger := i.logger.WithName("filesClientScriptJob")
		j, err = newFilesClientScriptJob(logger, i.gearman, i.p, wl)
	case "linkTaskManagerGetMicroserviceGeneratedListInStdOut":
		logger := i.logger.WithName("outputClientScriptJob")
		j, err = newOutputClientScriptJob(logger, i.gearman, i.p, wl)

	// Local jobs - executed directly.
	case "linkTaskManagerSetUnitVariable":
		logger := i.logger.WithName("setUnitVarLinkJob")
		j, err = newSetUnitVarLinkJob(logger, i.p, wl)
	case "linkTaskManagerUnitVariableLinkPull":
		logger := i.logger.WithName("getUnitVarLinkJob")
		j, err = newGetUnitVarLinkJob(logger, i.p, wl)

	default:
		err = fmt.Errorf("unknown job manager: %q", wl.Manager)
	}

	if err != nil {
		return nil, err
	}

	return j, nil
}

func (i *Iterator) wait(ctx context.Context) (uuid.UUID, error) {
	i.logger.Info("Package is now on hold.")

	select {
	case <-ctx.Done():
		return uuid.Nil, ctx.Err()
	case s := <-i.waitCh:
		return s.next, nil
	}
}

type waitSignal struct {
	next uuid.UUID
}
