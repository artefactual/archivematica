package main

import (
	"slices"
)

const (
	goVersion           = "1.22.1"
	golangciLintVersion = "v1.57.1"
)

type CCP struct {
	// Project source directory.
	// This will become useful once pulling from remote becomes available.
	//
	// +private
	Source *Directory
}

func New() *CCP {
	source := projectDir()

	return &CCP{
		Source: source,
	}
}

// paths to exclude from all contexts
var excludes = []string{
	"hack",
}

func exclude(paths ...string) []string {
	return append(slices.Clone(excludes), paths...)
}

func projectDir() *Directory {
	dir := dag.CurrentModule().Source().Directory("../../")
	for _, exclude := range excludes {
		dir = dir.WithoutDirectory(exclude)
	}
	return dir
}
