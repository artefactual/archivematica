package integration_test

import (
	"encoding/json"
	"fmt"
	"testing"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/google/uuid"
	"gotest.tools/v3/assert"
)

func TestWorkflowBuilder(t *testing.T) {
	wb := &WorkflowBuilder{}

	wb.Add(
		NewChain(L("Chain")).
			WithWatchedDirectory(&workflow.WatchedDirectory{
				OnlyDirs: true,
				UnitType: "Transfer",
				Path:     "/activeTransfers/standardTransfer",
			}).
			WithLinks(
				NamedLink("l1").
					Description(L("Link 1")).
					Group(L("Foobar")).
					Status(0, "Completed successfully", "l2").
					Fallback("Failed", "l2"),
				NamedLink("l2").
					Description(L("Link 2")).
					Group(L("Foobar")).
					Status(0, "Completed successfully", "").
					Fallback("Failed", "").
					Terminator(),
			),
	)

	// TODO: lazy evaluation of link references, e.g. l1 -> l2, etc...

	doc, err := wb.Build()
	assert.NilError(t, err)

	blob, err := json.MarshalIndent(doc, "", "  ")
	assert.NilError(t, err)

	fmt.Println(string(blob))
}

type WorkflowBuilder struct {
	doc         *workflow.Document
	namedChains map[string]uuid.UUID
	namedLinks  map[string]uuid.UUID
}

func (wb *WorkflowBuilder) Add(c *Chain) {
	if wb.doc == nil {
		wb.doc = &workflow.Document{
			Chains:             map[uuid.UUID]*workflow.Chain{},
			Links:              map[uuid.UUID]*workflow.Link{},
			WatchedDirectories: []*workflow.WatchedDirectory{},
		}
		wb.namedChains = make(map[string]uuid.UUID)
		wb.namedLinks = make(map[string]uuid.UUID)
	}

	if c.wd != nil {
		wb.doc.WatchedDirectories = append(wb.doc.WatchedDirectories, c.wd)
	}

	wb.doc.Chains[c.cn.ID] = c.cn

	for _, ln := range c.lns {
		wb.doc.Links[ln.ID] = ln
	}
}

func (wb *WorkflowBuilder) Build() (*workflow.Document, error) {
	return wb.doc, nil
}

type Chain struct {
	cn  *workflow.Chain
	wd  *workflow.WatchedDirectory
	lns []*workflow.Link
}

func NewChain(d workflow.I18nField) *Chain {
	return &Chain{
		cn: &workflow.Chain{
			ID:          uuid.New(),
			Description: d,
		},
	}
}

func (c *Chain) WithWatchedDirectory(wd *workflow.WatchedDirectory) *Chain {
	wd.ChainID = c.cn.ID
	c.wd = wd
	return c
}

func (c *Chain) WithLinks(links ...*Link) *Chain {
	for i, item := range links {
		wl := item.Build()
		wl.ID = uuid.New()

		if i == 0 {
			c.cn.LinkID = wl.ID
		}

		c.lns = append(c.lns, wl)
	}
	return c
}

var L = Label

func Label(value string) workflow.I18nField {
	return Labels("en", value)
}

func Labels(keyvals ...string) workflow.I18nField {
	f := workflow.I18nField{}

	if len(keyvals)%2 != 0 {
		panic("NewLabel must receive an even number of parameters.")
	}
	for i := 0; i < len(keyvals); i += 2 {
		k := keyvals[i]
		v := keyvals[i+1]
		f[k] = v
	}

	return f
}

type Link struct {
	name string
	ln   *workflow.Link
}

func NamedLink(name string) *Link {
	return &Link{
		name: name,
		ln:   &workflow.Link{},
	}
}

func (l *Link) Description(v workflow.I18nField) *Link {
	l.ln.Description = v
	return l
}

func (l *Link) Group(v workflow.I18nField) *Link {
	l.ln.Group = v
	return l
}

func (l *Link) Status(items ...interface{}) *Link {
	cs := map[int]workflow.LinkExitCode{}

	if len(items)%3 != 0 {
		panic("Number of parameters must be a multiple of three.")
	}
	for i := 0; i < len(items); i += 3 {
		v := items[i]
		code, ok := v.(int)
		if !ok {
			panic("Exit code must be an integer.")
		}

		v = items[i+1]
		status, ok := v.(string)
		if !ok {
			panic("Status must be a string.")
		}

		var id *uuid.UUID
		v = items[i+2]
		_, ok = v.(string)
		if !ok {
			panic("Target must be a string.")
		}

		cs[code] = workflow.LinkExitCode{
			JobStatus: status,
			LinkID:    id,
		}
	}

	l.ln.ExitCodes = cs

	return l
}

func (l *Link) Fallback(s, d string) *Link {
	l.ln.FallbackJobStatus = s
	return l
}

func (l *Link) Terminator() *Link {
	l.ln.End = true
	return l
}

func (l *Link) Build() *workflow.Link {
	return l.ln
}
