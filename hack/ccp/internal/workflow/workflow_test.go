package workflow_test

import (
	"testing"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/google/uuid"
	"gotest.tools/v3/assert"
)

func TestDecodeWorkflow(t *testing.T) {
	amflow, err := workflow.Default()
	assert.NilError(t, err)

	link := amflow.Links[uuid.MustParse("002716a1-ae29-4f36-98ab-0d97192669c4")]
	config := link.Config.(workflow.LinkStandardTaskConfig)
	assert.Equal(t, config.Execute, "moveSIP_v0.0")
}
