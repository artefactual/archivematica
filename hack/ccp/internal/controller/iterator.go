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

type chain struct {
	doc *workflow.Chain
	ctx *packageContext
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
			i.chain = &chain{doc: ch}
			if pCtx, err := loadContext(ctx, i.p); err != nil {
				return fmt.Errorf("load context: %v", err)
			} else {
				i.chain.ctx = pCtx
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
		if err == errWait {
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

// runJob processes a job given the identifier of a workflow chain or link.
func (i *iterator) runJob(ctx context.Context, id uuid.UUID) (uuid.UUID, error) {
	wl, ok := i.wf.Links[id]
	i.logger.Info("Processing job.", "type", "link", "linkID", id, "desc", wl.Description, "manager", wl.Manager)
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
func (i *iterator) buildJob(wl *workflow.Link) (*job, error) {
	j, err := newJob(i.logger.WithName("job"), i.chain, i.p, i.gearman, wl)
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
