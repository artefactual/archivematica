package servercmd

import (
	"errors"
	"fmt"
	"path/filepath"

	"github.com/artefactual/archivematica/hack/ccp/internal/controller"
	"github.com/artefactual/archivematica/hack/ccp/internal/processing"
	"github.com/artefactual/archivematica/hack/ccp/internal/scheduler"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/go-logr/logr"
	"github.com/gohugoio/hugo/watcher"
)

type Server struct {
	logger     logr.Logger
	config     *Config
	controller *controller.Controller
	watcher    *watcher.Batcher
	scheduler  *scheduler.Server
}

func NewServer(logger logr.Logger, config *Config) *Server {
	return &Server{
		logger: logger,
		config: config,
	}
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
	s.controller = controller.New(s.logger.WithName("controller"), wf, s.config.sharedDir, watchedDir)
	if err := s.controller.Run(); err != nil {
		return fmt.Errorf("error creating controller: %v", err)
	}

	s.logger.V(1).Info("Creating filesystem watchers.", "path", watchedDir)
	if s.watcher, err = watch(s.logger.WithName("watcher"), s.controller, wf, watchedDir); err != nil {
		return fmt.Errorf("error creating filesystem watchers: %v", err)
	}

	s.logger.V(1).Info("Creating scheduler.")
	s.scheduler = scheduler.New(s.logger.WithName("scheduler"))
	if err := s.scheduler.Run(); err != nil {
		return fmt.Errorf("error creating scheduler: %v", err)
	}

	return nil
}

func (s *Server) Close() error {
	var errs error

	if s.controller != nil {
		errs = errors.Join(errs, s.controller.Close())
	}

	if s.watcher != nil {
		s.watcher.Close()
	}

	if s.scheduler != nil {
		errs = errors.Join(errs, s.scheduler.Close())
	}

	return errs
}
