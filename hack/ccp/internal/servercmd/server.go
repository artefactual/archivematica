package servercmd

import (
	"context"
	"os"
	"path/filepath"
	"time"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/go-logr/logr"
	"github.com/gohugoio/hugo/watcher"
)

type Server struct {
	logger  logr.Logger
	config  *Config
	batcher *watcher.Batcher
}

func NewServer(logger logr.Logger, config *Config) *Server {
	return &Server{
		logger: logger,
		config: config,
	}
}

func (s *Server) Run(ctx context.Context) error {
	s.logger.V(1).Info("Loading workflow.")
	wf, err := workflow.Default()
	if err != nil {
		return err
	}

	s.logger.V(1).Info("Creating shared directories.", "path", s.config.sharedDir)
	if err := createSharedDirs(s.config.sharedDir); err != nil {
		return err
	}

	watchedDirs := filepath.Join(s.config.sharedDir, "watchedDirectories")
	s.logger.V(1).Info("Setting up filesystem watchers.", "path", watchedDirs)
	s.batcher, err = watcher.New(time.Second, time.Second, false)
	if err != nil {
		return err
	}
	for _, wd := range wf.WatchedDirectories {
		wdPath := filepath.Join(watchedDirs, wd.Path)
		info, err := os.Stat(wdPath)
		if err != nil {
			continue
		}
		if !info.IsDir() {
			continue
		}
		if err := s.batcher.Add(wdPath); err != nil {
			continue
		}
	}

	return nil
}

func (s *Server) Close() error {
	if s.batcher != nil {
		s.batcher.Close()
	}

	return nil
}
