package servercmd

import (
	"context"
	"errors"
	"fmt"
	"path/filepath"
	"time"

	"github.com/artefactual/archivematica/hack/ccp/internal/api/admin"
	"github.com/artefactual/archivematica/hack/ccp/internal/api/scheduler"
	"github.com/artefactual/archivematica/hack/ccp/internal/controller"
	"github.com/artefactual/archivematica/hack/ccp/internal/processing"
	"github.com/artefactual/archivematica/hack/ccp/internal/store"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/go-logr/logr"
	"github.com/gohugoio/hugo/watcher"
)

type Server struct {
	logger     logr.Logger
	ctx        context.Context
	cancel     context.CancelFunc
	config     *Config
	store      store.Store
	controller *controller.Controller
	watcher    *watcher.Batcher
	admin      *admin.Server
	scheduler  *scheduler.Server
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
	s.store, err = store.Create(s.logger.WithName("store"), s.config.db.driver, s.config.db.dsn)
	if err != nil {
		return fmt.Errorf("error creating database store: %v", err)
	}

	s.logger.V(1).Info("Cleaning up database.")
	{
		ctx, cancel := context.WithTimeout(s.ctx, time.Second*10)
		defer cancel()

		err = errors.Join(err, s.store.CleanUpActiveTasks(ctx))
		err = errors.Join(err, s.store.CleanUpActiveTransfers(ctx))
		err = errors.Join(err, s.store.CleanUpAwaitingJobs(ctx))
		err = errors.Join(err, s.store.CleanUpActiveSIPs(ctx))
		err = errors.Join(err, s.store.CleanUpActiveJobs(ctx))
	}
	if err != nil {
		return fmt.Errorf("error cleaning up database: %v", err)
	}

	s.logger.V(1).Info("Creating shared directories.", "path", s.config.sharedDir)
	if err := createSharedDirs(s.config.sharedDir); err != nil {
		return fmt.Errorf("error creating shared directories: %v", err)
	}

	processingConfigsDir := filepath.Join(s.config.sharedDir, "sharedMicroServiceTasksConfigs/processingMCPConfigs")
	s.logger.V(1).Info("Creating default processing configurations.", "path", processingConfigsDir)
	if err := processing.InstallBuiltinConfigs(processingConfigsDir); err != nil {
		return fmt.Errorf("error creating default processing configurations: %v", err)
	}

	watchedDir := filepath.Join(s.config.sharedDir, "watchedDirectories")

	s.logger.V(1).Info("Creating controller.")
	s.controller = controller.New(s.logger.WithName("controller"), s.store, wf, s.config.sharedDir, watchedDir)
	if err := s.controller.Run(); err != nil {
		return fmt.Errorf("error creating controller: %v", err)
	}

	s.logger.V(1).Info("Creating filesystem watchers.", "path", watchedDir)
	if s.watcher, err = watch(s.logger.WithName("watcher"), s.controller, wf, watchedDir); err != nil {
		return fmt.Errorf("error creating filesystem watchers: %v", err)
	}

	s.logger.V(1).Info("Creating admin API.")
	s.admin = admin.New(s.logger.WithName("api.admin"))
	if err := s.admin.Run(); err != nil {
		return fmt.Errorf("error creating admin API: %v", err)
	}

	s.logger.V(1).Info("Creating scheduler API.")
	s.scheduler = scheduler.New(s.logger.WithName("api.scheduler"))
	if err := s.scheduler.Run(); err != nil {
		return fmt.Errorf("error creating scheduler API: %v", err)
	}

	s.logger.V(1).Info("Ready.")

	return nil
}

func (s *Server) Close() error {
	var errs error

	s.logger.Info("Shutting down...", "store", s.store)

	s.cancel()

	if s.store.Running() {
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

	if s.scheduler != nil {
		errs = errors.Join(errs, s.scheduler.Close())
	}

	return errs
}
