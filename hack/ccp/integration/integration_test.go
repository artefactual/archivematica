package integration_test

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"testing"
	"time"

	"go.uber.org/goleak"
	"golang.org/x/exp/slices"
	"gotest.tools/v3/assert"
	"gotest.tools/v3/fs"

	"github.com/artefactual/archivematica/hack/ccp/internal/rootcmd"
	"github.com/artefactual/archivematica/hack/ccp/internal/servercmd"
)

var (
	enabled    = getEnvBool("ENABLED", "no")
	useCompose = getEnvBool("USE_COMPOSE", "no")
	useStdout  = getEnvBool("USE_STDOUT", "yes")
)

func getEnv(name, fallback string) string {
	const prefix = "CCP_INTEGRATION"
	v := os.Getenv(fmt.Sprintf("%s_%s", prefix, name))
	if v == "" {
		return fallback
	}
	return v
}

func getEnvBool(name, fallback string) bool {
	if v := getEnv(name, fallback); slices.Contains([]string{"yes", "1", "on", "true"}, v) {
		return true
	} else {
		return false
	}
}

func requireFlag(t *testing.T) {
	if !enabled {
		t.Skip("Skipping integration tests (CCP_INTEGRATION_ENABLED=no).")
	}
}

func TestMain(m *testing.M) {
	goleak.VerifyTestMain(m)
}

func TestServerCmd(t *testing.T) {
	t.Parallel()
	requireFlag(t)

	t.Run("xxxxxxxxxx", func(t *testing.T) {
		t.Parallel()

		ctx, cancel := context.WithCancel(context.Background())
		t.Cleanup(cancel)

		dsn := useMySQL(t)

		sharedDir := fs.NewDir(t, "servercmd")

		args := []string{
			"-v=10",
			"--debug",
			"--db.driver=mysql",
			"--db.dsn=" + dsn,
			"--api.admin.addr=:22300",
			"--shared-dir=" + sharedDir.Path(),
			"--gearmin.addr=:4730",
		}

		var stdout io.Writer = bytes.NewBuffer([]byte{})
		if useStdout {
			stdout = os.Stdout
		}

		cmd := servercmd.New(&rootcmd.Config{}, stdout)
		assert.NilError(t, cmd.Parse(args))

		done := make(chan error)
		go func() {
			done <- cmd.Exec(ctx, []string{})
		}()

		// Wait for application to start watching directories and other things to start.
		time.Sleep(time.Second / 2)

		// Server is likely running, but let's try to receive to see if it failed.
		select {
		case <-time.After(time.Second / 2):
		case err := <-done:
			assert.NilError(t, err)
		}

		// Submit transfers.
		for i := 0; i < 1; i++ {
			submitTransfer(t, sharedDir, fmt.Sprintf("Images-%d", i+1), "activeTransfers/standardTransfer")
		}

		// Wait for all processing to complete.
		time.Sleep(time.Second * 10)

		cancel()

		err := <-done
		assert.NilError(t, err)
	})
}

func submitTransfer(t *testing.T, sharedDir *fs.Dir, name, dest string) string {
	t.Helper()

	const dirMode = os.FileMode(0o777)
	const fileMode = os.FileMode(0o666)

	err := os.MkdirAll(filepath.Join(sharedDir.Path(), dest), dirMode)
	assert.NilError(t, err)

	transferDir := sharedDir.Join(filepath.Join("tmp", name))
	err = os.Mkdir(transferDir, dirMode)
	assert.NilError(t, err)

	// Write transfer contents.
	f, err := os.OpenFile(filepath.Join(transferDir, "foo.jpg"), os.O_RDWR|os.O_CREATE, fileMode)
	assert.NilError(t, err)
	_, err = f.Write([]byte("foobar"))
	assert.NilError(t, err)

	// Move to watched directory.
	watchedDir := filepath.Join(sharedDir.Path(), "watchedDirectories")
	newPath := filepath.Join(watchedDir, dest, name)
	err = os.Rename(transferDir, newPath)
	assert.NilError(t, err)

	return newPath
}
