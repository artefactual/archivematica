package wb_test

import (
	"encoding/json"
	"fmt"
	"testing"

	"gotest.tools/v3/assert"

	"github.com/artefactual/archivematica/hack/ccp/integration/wb"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

func TestWorkflowBuilder(t *testing.T) {
	w := wb.New().
		Chain(
			wb.L("Chain"),
			func(c *wb.Chain) {
				c.
					WithWatchedDirectory(
						&workflow.WatchedDirectory{
							OnlyDirs: true,
							UnitType: "Transfer",
							Path:     "/activeTransfers/standardTransfer",
						},
					).
					WithLink(
						wb.L("Link 2"),
						func(l *wb.Link) {
							l.
								Config(workflow.LinkStandardTaskConfig{
									Manager:   "linkTaskManagerDirectories",
									Execute:   "command",
									Arguments: "--help",
								}).
								Group(wb.L("Group")).
								Status(0, "Completed successfully", "").
								Fallback("Failed", "").
								Terminator()
						},
					).
					WithLink(
						wb.L("Link 1"),
						func(l *wb.Link) {
							l.
								Config(workflow.LinkStandardTaskConfig{
									Manager:   "linkTaskManagerDirectories",
									Execute:   "command",
									Arguments: "--help",
								}).
								Group(wb.L("Group")).
								Status(0, "Completed successfully", "Link 2").
								Fallback("Failed", "Link 2")
						},
					)
			},
		)

	doc, err := w.Build()
	assert.NilError(t, err)

	blob, err := json.MarshalIndent(doc, "", "  ")
	assert.NilError(t, err)

	fmt.Println(string(blob))
}
