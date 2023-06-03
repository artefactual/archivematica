package servercmd

import (
	"context"
	"flag"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"syscall"

	"github.com/peterbourgon/ff/v3"
	"github.com/peterbourgon/ff/v3/ffcli"
	"github.com/peterbourgon/ff/v3/fftoml"

	"github.com/artefactual/archivematica/hack/ccp/internal/log"
	"github.com/artefactual/archivematica/hack/ccp/internal/rootcmd"
)

func New(rootConfig *rootcmd.Config, out io.Writer) *ffcli.Command {
	cfg := Config{
		rootConfig: rootConfig,
		out:        out,
	}

	fs := flag.NewFlagSet("ccp server", flag.ExitOnError)
	fs.String("config", "", "Configuration file in the TOML file format")
	fs.StringVar(&cfg.sharedDir, "shared-dir", "", "Shared directory")
	fs.StringVar(&cfg.workflow, "workflow", "", "Workflow document")

	rootConfig.RegisterFlags(fs)

	return &ffcli.Command{
		Name:       "server",
		ShortUsage: "ccp server [flags]",
		ShortHelp:  "Start server.",
		FlagSet:    fs,
		Options: []ff.Option{
			ff.WithEnvVarPrefix("CCP"),
			ff.WithEnvVarSplit("_"),
			ff.WithConfigFileFlag("config"),
			ff.WithConfigFileParser(fftoml.Parser),
		},
		Exec: cfg.Exec,
	}
}

func (c *Config) Exec(ctx context.Context, args []string) error {
	logger, err := log.Logger("ccp.server", c.rootConfig.Verbosity, c.rootConfig.Debug)
	if err != nil {
		return err
	}

	keys := []interface{}{
		"version", "TODO",
		"commit", "TODO",
		"pid", os.Getpid(),
		"go", runtime.Version(),
	}
	logger.Info("Starting...", keys...)

	if c.sharedDir == "" {
		configDir, err := os.UserConfigDir()
		if err != nil {
			return err
		}
		c.sharedDir = filepath.Join(configDir, "ccp", "shared")
	}

	ctx, stop := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer stop()

	s := NewServer(logger, c)
	if err := s.Run(); err != nil {
		s.Close()
		return err
	}

	<-ctx.Done()

	if err := s.Close(); err != nil {
		return err
	}

	return nil
}
