package python_test

import (
	"testing"

	"gotest.tools/v3/assert"

	"github.com/artefactual/archivematica/hack/ccp/internal/python"
)

const literal = `{'filterSubDir':'objects/attachments', "1": "2"}`

func TestEvalMap(t *testing.T) {
	dict, err := python.EvalMap(literal)

	assert.NilError(t, err)
	assert.DeepEqual(t, dict, map[string]string{
		"filterSubDir": "objects/attachments",
		"1":            "2",
	})
}

func BenchmarkEvalMap(b *testing.B) {
	for i := 0; i < b.N; i++ {
		python.EvalMap(literal)
	}
}
