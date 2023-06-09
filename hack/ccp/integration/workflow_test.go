package integration_test

import (
	"testing"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"gotest.tools/v3/assert"
)

/*
Draft design of what the workflow builder could be, useful for authoring small test-oriented workflows.
It should not require to define identifiers unless it's strictly required.

// Create a chain builder.
c1 := &ChainBuilder{}

// Optional attach a watched directory to it, which is pretty common actually.
c1.WithWatchedDirectory(...)

// Start chaining workflow links sequentially.
c1.WithLink(l1,	l2, l3, l4)

b := &WorkflowBuilder{}
b.Add(c1)

// This should return a *workflow.Document.
b.Marshal()
*/
type WorkflowBuilder struct {
	t *testing.T
}

func (wb *WorkflowBuilder) Add(c *Chain) {
}

func (wb *WorkflowBuilder) Marshal() *workflow.Document {
	doc, err := workflow.Default()
	assert.NilError(wb.t, err)

	return doc
}

type Chain struct {
	wd *workflow.WatchedDirectory
}

func (c *Chain) WithWatchedDirectory(wd *workflow.WatchedDirectory) {
}

func TestWorkflowBuilder(t *testing.T) {
	wb := &WorkflowBuilder{t}

	c1 := &Chain{}
	c1.WithWatchedDirectory(&workflow.WatchedDirectory{})

	wb.Marshal()
}
