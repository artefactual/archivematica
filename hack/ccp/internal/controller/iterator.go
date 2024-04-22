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

// A chain is used to carry local state.
//
// In Archivematica the workflow is structured around chains and links.
// A chain is a sequence of links used to accomplish a broader task or set of
// tasks, carrying local state relevant only for the duration of the chain.
// The output of a chain is placed in a watched directory to trigger the next
// chain.
//
// In MCPServer, `chain.jobChain` is implemented as an iterator, simplifying
// the process of moving through the jobs in a chain. When a chain completes,
// the queue manager checks the queues for ay work awaiting to be processed,
// which could be related to other packages.
//
// In a3m, chains and watched directories were removed, but it's hard to do it
// without introducing backward-incompatible changes given the reliance on it
// in some edge cases like reingest, etc.
type chain struct {
	wc      *workflow.Chain // The chain link in the workflow.
	pCtx    *packageContext // Local state.
	choices any             // TODO: see `generated_choices` in `chain.py`.
}

// iterator carries a package through all its workflow.
type iterator struct {
	logger logr.Logger

	gearman *gearmin.Server

	wf *workflow.Document

	p *Package

	startAt uuid.UUID

	chain *chain

	waitCh chan waitSignal
}

func NewIterator(logger logr.Logger, gearman *gearmin.Server, wf *workflow.Document, p *Package) *iterator {
	iter := &iterator{
		logger:  logger,
		gearman: gearman,
		wf:      wf,
		p:       p,
		startAt: p.watchedAt.ChainID,
		waitCh:  make(chan waitSignal, 10),
	}

	return iter
}

func (i *iterator) Process(ctx context.Context) error {
	next := i.startAt

	for {
		if err := ctx.Err(); err != nil {
			return err
		}

		// If we're starting a new chain.
		if ch, ok := i.wf.Chains[next]; ok {
			i.logger.Info("Starting new chain.", "id", ch.ID, "desc", ch.Description)
			i.chain = &chain{wc: ch}
			if pCtx, err := loadContext(ctx, i.p); err != nil {
				return fmt.Errorf("load context: %v", err)
			} else {
				i.chain.pCtx = pCtx
			}
			next = ch.LinkID
			continue
		}

		if i.chain == nil {
			return fmt.Errorf("can't process a job without a chain")
		}

		n, err := i.runJob(ctx, next)
		if err == io.EOF {
			return nil
		}
		if errors.Is(err, errWait) {
			choice, waitErr := i.wait(ctx) // puts the loop on hold.
			if waitErr != nil {
				return fmt.Errorf("wait: %v", waitErr)
			}
			next = choice
			continue
		}
		if err != nil {
			return fmt.Errorf("run job: %v", err)
		}
		next = n
	}
}

// runJob runs a job given the identifier of a workflow chain or link.
func (i *iterator) runJob(ctx context.Context, id uuid.UUID) (uuid.UUID, error) {
	wl, ok := i.wf.Links[id]

	logger := i.logger.WithName("job").WithValues("type", "link", "linkID", id, "desc", wl.Description, "manager", wl.Manager)
	logger.Info("Running job.")

	if !ok {
		return uuid.Nil, fmt.Errorf("link %s couldn't be found", id)
	}
	if wl.End {
		return uuid.Nil, io.EOF
	}

	s, err := i.buildJob(wl, logger)
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
func (i *iterator) buildJob(wl *workflow.Link, logger logr.Logger) (*job, error) {
	j, err := newJob(logger, i.chain, i.p, i.gearman, wl)
	if err != nil {
		return nil, fmt.Errorf("build job: %v", err)
	}

	return j, nil
}

func (i *iterator) wait(ctx context.Context) (uuid.UUID, error) {
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
