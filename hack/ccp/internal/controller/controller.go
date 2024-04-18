package controller

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
	"github.com/go-logr/logr"
	"github.com/sevein/gearmin"
	"golang.org/x/sync/errgroup"

	"github.com/artefactual/archivematica/hack/ccp/internal/store"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

const maxConcurrentPackages = 2

type Controller struct {
	logger logr.Logger

	store store.Store

	// Embedded job server compatible with Gearman.
	gearman *gearmin.Server

	// wf is the workflow document.
	wf *workflow.Document

	sharedDir string

	watchedDir string

	// activePackages is the list of active packages.
	activePackages []*Package

	// queuedPackages is the list of queued packages, FIFO style.
	queuedPackages []*Package

	// sync.Mutex protects the internal Package slices.
	mu sync.Mutex

	// group is a collection of goroutines used for processing packages.
	group *errgroup.Group

	// groupCtx is the context associated to the errgroup.
	groupCtx context.Context

	// groupCancel tells active goroutines in the errgroup to abandon.
	groupCancel context.CancelFunc

	// closeOnce guarantees that the closing procedure runs only once.
	closeOnce sync.Once
}

func New(logger logr.Logger, store store.Store, gearman *gearmin.Server, wf *workflow.Document, sharedDir, watchedDir string) *Controller {
	c := &Controller{
		logger:         logger,
		store:          store,
		gearman:        gearman,
		wf:             wf,
		sharedDir:      sharedDir,
		watchedDir:     watchedDir,
		activePackages: []*Package{},
		queuedPackages: []*Package{},
	}

	c.groupCtx, c.groupCancel = context.WithCancel(context.Background())
	c.group, _ = errgroup.WithContext(c.groupCtx)
	c.group.SetLimit(10)

	return c
}

// Run tries to start processing queued transfers.
func (c *Controller) Run() error {
	go func() {
		ticker := time.NewTicker(time.Second / 4)
		defer ticker.Stop()

		for {
			select {
			case <-ticker.C:
				c.pick()
			case <-c.groupCtx.Done():
				return
			}
		}
	}()

	return nil
}

func (c *Controller) HandleWatchedDirEvents(evs []fsnotify.Event) {
	for _, ev := range evs {
		if ev.Op&fsnotify.Create == fsnotify.Create {
			if err := c.handle(ev.Name); err != nil {
				c.logger.Info("Failed to handle event.", "err", err, "path", ev.Name)
			}
		}
	}
}

func (c *Controller) handle(path string) error {
	rel, err := filepath.Rel(c.watchedDir, path)
	if err != nil {
		return err
	}

	dir, _ := filepath.Split(rel)
	dir = trim(dir)

	var match bool
	for _, wd := range c.wf.WatchedDirectories {
		if trim(wd.Path) == dir {
			match = true
			c.logger.V(2).Info("Identified new package.", "path", path, "type", wd.UnitType)
			c.queue(path, wd)
			c.pick()
			break
		}
	}
	if !match {
		return fmt.Errorf("unmatched event")
	}

	return nil
}

func (c *Controller) queue(path string, wd *workflow.WatchedDirectory) {
	ctx, cancel := context.WithTimeout(c.groupCtx, time.Minute)
	defer cancel()

	logger := c.logger.WithName("package").WithValues("wd", wd.Path, "path", path)
	p, err := NewPackage(ctx, logger, c.store, path, c.sharedDir, wd)
	if err != nil {
		logger.Error(err, "Failed to create new package.")
		return
	}

	c.mu.Lock()
	c.queuedPackages = append(c.queuedPackages, p)
	c.mu.Unlock()
}

func (c *Controller) pick() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if len(c.activePackages) == maxConcurrentPackages {
		c.logger.V(2).Info("Not accepting new packages at this time.", "active", len(c.activePackages), "max", maxConcurrentPackages)
		return
	}

	var current *Package
	if len(c.queuedPackages) > 0 {
		current = c.queuedPackages[0]
		c.activePackages = append(c.activePackages, current)
		c.queuedPackages = c.queuedPackages[1:]
	}

	if current == nil {
		return
	}

	c.group.Go(func() error {
		logger := c.logger.V(2).WithValues("package", current)

		defer c.deactivate(current)

		logger.Info("Processing started.")
		err := NewIterator(logger, c.gearman, c.wf, current).Process(c.groupCtx) // Block.
		if err != nil {
			logger.Info("Processing failed.", "err", err)
		} else {
			logger.Info("Processing completed successfully")
		}

		return err
	})
}

// deactivate removes a package from the activePackages queue.
func (c *Controller) deactivate(p *Package) {
	c.mu.Lock()
	defer c.mu.Unlock()

	for i, item := range c.activePackages {
		if item.id == p.id {
			c.activePackages = append(c.activePackages[:i], c.activePackages[i+1:]...)
			break
		}
	}
}

// Active lists all active packages.
func (c *Controller) Active() []string {
	c.mu.Lock()
	defer c.mu.Unlock()

	ret := make([]string, len(c.activePackages))
	for i, item := range c.activePackages {
		ret[i] = item.String()
	}

	return ret
}

// Decisions lists awaiting decisions for all active packages.
func (c *Controller) Decisions() []string {
	c.mu.Lock()
	defer c.mu.Unlock()

	ret := []string{}

	for _, item := range c.activePackages {
		opts := item.Decision()
		ln := len(opts)
		if ln == 0 {
			continue
		}
		ret = append(ret, fmt.Sprintf("package %s has an awaiting decision with %d options available", item, ln))

	}

	return ret
}

func (c *Controller) Close() error {
	var err error

	c.closeOnce.Do(func() {
		c.groupCancel()
		err = c.group.Wait()
	})

	return err
}

func trim(path string) string {
	return strings.Trim(path, string(filepath.Separator))
}
