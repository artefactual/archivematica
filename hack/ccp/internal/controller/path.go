package controller

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
)

// uuidFromPath returns the UUID if it's the suffix of the path.
func uuidFromPath(path string) uuid.UUID {
	path = strings.TrimRight(path, string(os.PathSeparator))
	if len(path) < 36 {
		return uuid.Nil
	}
	id, err := uuid.Parse(path[len(path)-36:])
	if err != nil {
		return uuid.Nil
	}
	return id
}

// joinPath is like filepath.Join but appends the ending separator when the last
// element provided is an empty string.
func joinPath(elem ...string) string {
	if len(elem) == 0 {
		return ""
	}
	ret := filepath.Join(elem...)
	if elem[len(elem)-1] == "" {
		ret += string(os.PathSeparator)
	}

	return ret
}
