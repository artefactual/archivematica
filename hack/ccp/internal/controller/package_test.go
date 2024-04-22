package controller

import (
	"testing"

	"github.com/elliotchance/orderedmap/v2"
	"gotest.tools/v3/assert"
)

func TestReplacements(t *testing.T) {
	pCtx := &packageContext{OrderedMap: orderedmap.NewOrderedMap[string, string]()}
	pCtx.Set("%path%", "/mnt/disk")
	pCtx.Set("%name%", `Dr. Evelyn "The Innovator" O'Neill: The Complete Digital Archives`)

	rm := replacementMapping(map[string]replacement{
		"%uuid%": "91354225-f28b-433c-8280-cf6a5edea2ff",
		"%job%":  `cool \\stuff`,
	}).update(pCtx)

	assert.Equal(t,
		rm.replaceValues(`%name% with path="%path%" and uuid="%uuid%" did: %job%`),
		`Dr. Evelyn \"The Innovator\" O'Neill: The Complete Digital Archives with path="/mnt/disk" and uuid="91354225-f28b-433c-8280-cf6a5edea2ff" did: cool \\\\\\\\stuff`,
	)
}
