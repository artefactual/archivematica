package servercmd

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"time"

	"github.com/artefactual/archivematica/hack/ccp/internal/api/admin"
	"github.com/artefactual/archivematica/hack/ccp/internal/controller"
	"github.com/artefactual/archivematica/hack/ccp/internal/processing"
	"github.com/artefactual/archivematica/hack/ccp/internal/store"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/go-logr/logr"
	"github.com/gohugoio/hugo/watcher"
	"github.com/sevein/gearmin"
)

type Server struct {
	logger logr.Logger
	ctx    context.Context
	cancel context.CancelFunc
	config *Config

	// Data store.
	store store.Store

	// Embedded job server compatible with Gearman.
	gearman *gearmin.Server

	// Filesystem watcher.
	watcher *watcher.Batcher

	// Workflow processor.
	controller *controller.Controller

	// Admin API.
	admin *admin.Server
}

func NewServer(logger logr.Logger, config *Config) *Server {
	s := &Server{
		logger: logger,
		config: config,
	}

	s.ctx, s.cancel = context.WithCancel(context.Background())

	return s
}

func (s *Server) Run() error {
	s.logger.V(1).Info("Loading workflow.")
	var (
		wf  *workflow.Document
		err error
	)
	if path := s.config.workflow; path != "" {
		wf, err = workflow.LoadFromFile(path)
	} else {
		wf, err = workflow.Default()
	}
	if err != nil {
		return fmt.Errorf("error loading workflow: %v", err)
	}

	s.logger.V(1).Info("Creating database store.")
	s.store, err = store.New(s.logger.WithName("store"), s.config.db.driver, s.config.db.dsn)
	if err != nil {
		return fmt.Errorf("error creating database store: %v", err)
	}

	s.logger.V(1).Info("Cleaning up database.")
	{
		ctx, cancel := context.WithTimeout(s.ctx, time.Second*10)
		defer cancel()

		err = s.store.RemoveTransientData(ctx)
	}
	if err != nil {
		return fmt.Errorf("error cleaning up database: %v", err)
	}

	s.logger.V(1).Info("Creating shared directories.", "path", s.config.sharedDir)
	if err := createSharedDirs(s.config.sharedDir); err != nil {
		return fmt.Errorf("error creating shared directories: %v", err)
	}

	var (
		processingConfigsDir = filepath.Join(s.config.sharedDir, "sharedMicroServiceTasksConfigs/processingMCPConfigs")
		watchedDir           = filepath.Join(s.config.sharedDir, "watchedDirectories")
	)

	s.logger.V(1).Info("Creating default processing configurations.", "path", processingConfigsDir)
	if err := processing.InstallBuiltinConfigs(processingConfigsDir); err != nil {
		return fmt.Errorf("error creating default processing configurations: %v", err)
	}

	s.logger.V(1).Info("Creating Gearman job server.")
	s.gearman = gearmin.NewServer(gearmin.Config{ListenAddr: s.config.gearmin.addr})
	if err := s.gearman.Start(); err != nil {
		return fmt.Errorf("error creating Gearmin job server: %v", err)
	}

	s.logger.V(1).Info("Creating controller.")
	s.controller = controller.New(s.logger.WithName("controller"), s.store, s.gearman, wf, s.config.sharedDir, watchedDir)
	if err := s.controller.Run(); err != nil {
		return fmt.Errorf("error creating controller: %v", err)
	}

	s.logger.V(1).Info("Creating filesystem watchers.", "path", watchedDir)
	if s.watcher, err = watch(s.logger.WithName("watcher"), s.controller, wf, watchedDir); err != nil {
		return fmt.Errorf("error creating filesystem watchers: %v", err)
	}

	s.logger.V(1).Info("Creating admin API.")
	s.admin = admin.New(s.logger.WithName("api.admin"), s.config.api.admin, s.controller)
	if err := s.admin.Run(); err != nil {
		return fmt.Errorf("error creating admin API: %v", err)
	}

	s.logger.V(1).Info("Ready.")

	return nil
}

func (s *Server) Close() error {
	var errs error

	s.logger.Info("Shutting down...")

	s.cancel()

	if s.store != nil && s.store.Running() {
		errs = errors.Join(errs, s.store.Close())
	}

	if s.controller != nil {
		errs = errors.Join(errs, s.controller.Close())
	}

	if s.watcher != nil {
		s.watcher.Close()
	}

	if s.admin != nil {
		errs = errors.Join(errs, s.admin.Close())
	}

	s.gearman.Stop()

	return errs
}
