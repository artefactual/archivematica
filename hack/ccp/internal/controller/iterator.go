package controller

import (
	"context"
	"errors"
	"fmt"
	"io"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/go-logr/logr"
	"github.com/google/uuid"
)

var errWait = errors.New("wait")

// Iterator carries a package through all its workflow.
type Iterator struct {
	logger logr.Logger

	wf *workflow.Document

	p *Package

	startAt uuid.UUID

	chain *workflow.Chain

	waitCh chan waitSignal
}

func NewIterator(logger logr.Logger, wf *workflow.Document, p *Package) *Iterator {
	iter := &Iterator{
		logger:  logger,
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

	// Executable jobs - dispatched to the worker pool.
	case "linkTaskManagerDirectories":
		j, err = newStandardTask(i.logger, i.p, wl)
	case "linkTaskManagerFiles":
		j, err = newStandardTask(i.logger, i.p, wl)
	case "linkTaskManagerGetMicroserviceGeneratedListInStdOut":
		j, err = newStandardTask(i.logger, i.p, wl)

	// Decision jobs - handles workflow decision points.
	case "linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList":
		panic("X")
	case "linkTaskManagerChoice":
		j, err = newChainChoice(i.logger, i.p, wl)
	case "linkTaskManagerReplacementDicFromChoice":
		j, err = newChoiceReplacementDict(i.logger, i.p, wl)

	// Local jobs - executed directly.
	case "linkTaskManagerSetUnitVariable":
		j, err = newSetUnitVariable(i.logger, i.p, wl)
	case "linkTaskManagerUnitVariableLinkPull":
		j, err = newGetUnitVariable(i.logger, i.p, wl)

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
