package rootcmd

import (
	"context"
	"flag"

	"github.com/peterbourgon/ff/v3/ffcli"
)

func New() (*ffcli.Command, *Config) {
	var cfg Config

	fs := flag.NewFlagSet("ccp", flag.ExitOnError)
	cfg.RegisterFlags(fs)

	return &ffcli.Command{
		Name:       "ccp",
		ShortUsage: "ccp [flags] <subcommand> [flags] [<arg>...]",
		FlagSet:    fs,
		Exec:       cfg.Exec,
	}, &cfg
}

func (c *Config) RegisterFlags(fs *flag.FlagSet) {
	fs.IntVar(&c.Verbosity, "v", 0, "Logging verbosity (zero is the lowest)")
	fs.BoolVar(&c.Debug, "debug", false, "Enable debug mode")
}

func (c *Config) Exec(context.Context, []string) error {
	return flag.ErrHelp
}
