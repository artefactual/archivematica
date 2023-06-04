package integration_test

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/artefactual/archivematica/hack/ccp/internal/rootcmd"
	"github.com/artefactual/archivematica/hack/ccp/internal/servercmd"
	"go.uber.org/goleak"
	"gotest.tools/v3/assert"
	"gotest.tools/v3/fs"
)

func TestMain(m *testing.M) {
	goleak.VerifyTestMain(m)
}

func TestServerCmd(t *testing.T) {
	t.Parallel()

	t.Run("xxxxxxxxxx", func(t *testing.T) {
		t.Parallel()

		ctx, cancel := context.WithCancel(context.Background())
		t.Cleanup(cancel)

		sharedDir := fs.NewDir(t, "servercmd")

		args := []string{
			"-v=10",
			"--debug",
			"--shared-dir=" + sharedDir.Path(),
		}

		cmd := servercmd.New(&rootcmd.Config{}, bytes.NewBuffer([]byte{}))
		assert.NilError(t, cmd.Parse(args))

		var err error
		done := make(chan struct{})
		go func() {
			err = cmd.Exec(ctx, []string{})
			done <- struct{}{}
		}()

		// Wait for application to start watching directories.
		time.Sleep(time.Millisecond * 100)

		// Server is running!

		// Submit transfers.
		for i := 0; i < 1; i++ {
			submitTransfer(t, sharedDir, fmt.Sprintf("Images-%d", i+1), "activeTransfers/standardTransfer")
		}

		// Wait for all processing to complete.
		time.Sleep(time.Second * 3)

		cancel()
		<-done

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