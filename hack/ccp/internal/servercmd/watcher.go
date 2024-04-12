package servercmd

import (
	"errors"
	"os"
	"path/filepath"
	"time"

	"github.com/go-logr/logr"
	"github.com/gohugoio/hugo/watcher"

	"github.com/artefactual/archivematica/hack/ccp/internal/controller"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

func watch(logger logr.Logger, ctrl *controller.Controller, wf *workflow.Document, path string) (*watcher.Batcher, error) {
	w, err := watcher.New(500*time.Millisecond, 700*time.Millisecond, false)
	if err != nil {
		return nil, err
	}

	var errs error
	for _, wd := range wf.WatchedDirectories {
		wdPath := filepath.Join(path, wd.Path)
		info, err := os.Stat(wdPath)
		if err != nil {
			errs = errors.Join(errs, err)
			continue
		}
		if !info.IsDir() {
			errs = errors.Join(errs, errors.New("not a directory"))
			continue
		}
		logger.V(2).Info("Watching directory.", "path", wdPath)
		if err := w.Add(wdPath); err != nil {
			errs = errors.Join(errs, err)
			continue
		}
	}
	if errs != nil {
		return nil, errs
	}

	go func() {
		for {
			select {
			case evs := <-w.Events:
				ctrl.HandleWatchedDirEvents(evs)
			case err := <-w.Errors():
				if err != nil {
					logger.V(1).Info("Error while watching.", "err", err)
				}
				return
			}
		}
	}()

	return w, nil
}
