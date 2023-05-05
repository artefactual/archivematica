package servercmd

import (
	"context"
	"flag"
	"io"
	"os"
	"path/filepath"
	"runtime"

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

	configDir, err := os.UserConfigDir()
	if err != nil {
		return err
	}
	c.sharedDir = filepath.Join(configDir, "ccp", "shared")

	s := NewServer(logger, c)
	s.Run(ctx)
	s.Close()

	return nil
}
