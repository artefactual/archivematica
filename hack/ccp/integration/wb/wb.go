package wb

import (
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"

	"github.com/google/uuid"
)

type WorkflowBuilder struct {
	doc         *workflow.Document
	namedChains map[string]*Chain
	namedLinks  map[string]*Link
}

func New() *WorkflowBuilder {
	wb := WorkflowBuilder{}
	wb.doc = &workflow.Document{
		Chains:             map[uuid.UUID]*workflow.Chain{},
		Links:              map[uuid.UUID]*workflow.Link{},
		WatchedDirectories: []*workflow.WatchedDirectory{},
	}
	wb.namedChains = make(map[string]*Chain)
	wb.namedLinks = make(map[string]*Link)
	return &wb
}

func (wb *WorkflowBuilder) Chain(desc workflow.I18nField, opts func(c *Chain)) *WorkflowBuilder {
	c := &Chain{
		b: wb,
		cn: &workflow.Chain{
			ID:          uuid.New(),
			Description: desc,
		},
	}

	// Invoke user-provided options callback with chain customizations.
	opts(c)

	if c.wd != nil {
		wb.doc.WatchedDirectories = append(wb.doc.WatchedDirectories, c.wd)
	}

	wb.doc.Chains[c.cn.ID] = c.cn
	wb.namedChains[c.cn.Description.String()] = c

	return wb
}

func (wb *WorkflowBuilder) Build() (*workflow.Document, error) {
	return wb.doc, nil
}

func (wb *WorkflowBuilder) findID(desc string) uuid.UUID {
	if c := wb.findChain(desc); c != nil {
		return c.cn.ID
	}
	if l := wb.findLink(desc); l != nil {
		return l.ln.ID
	}
	return uuid.Nil
}

func (wb *WorkflowBuilder) findChain(desc string) *Chain {
	c, ok := wb.namedChains[desc]
	if !ok {
		return nil
	}
	return c
}

func (wb *WorkflowBuilder) findLink(desc string) *Link {
	l, ok := wb.namedLinks[desc]
	if !ok {
		return nil
	}
	return l
}

type Chain struct {
	b   *WorkflowBuilder
	cn  *workflow.Chain
	wd  *workflow.WatchedDirectory
	lns []*Link
}

func (c *Chain) WithWatchedDirectory(wd *workflow.WatchedDirectory) *Chain {
	wd.ChainID = c.cn.ID
	c.wd = wd
	return c
}

func (c *Chain) WithLink(desc workflow.I18nField, opts func(l *Link)) *Chain {
	l := &Link{
		b: c.b,
		ln: &workflow.Link{
			ID:          uuid.New(),
			Description: desc,
		},
	}

	// Invoke user-provided options callback with chain customizations.
	opts(l)

	if l.ln.Config == nil {
		panic("config is required")
	}

	if len(c.lns) == 0 {
		c.cn.LinkID = l.ln.ID
	}

	c.b.doc.Links[l.ln.ID] = l.ln
	c.b.namedLinks[l.ln.Description.String()] = l

	return c
}

type Link struct {
	b  *WorkflowBuilder
	ln *workflow.Link
}

func (l *Link) Description(v workflow.I18nField) *Link {
	l.ln.Description = v
	return l
}

func (l *Link) Group(v workflow.I18nField) *Link {
	l.ln.Group = v
	return l
}

func (l *Link) Config(val any) *Link {
	switch cfg := val.(type) {
	case workflow.LinkMicroServiceChainChoice:
		l.ln.Config = cfg
		cfg.Model = "MicroServiceChainChoice"
		cfg.Manager = "linkTaskManagerChoice"
	case workflow.LinkMicroServiceChoiceReplacementDic:
		l.ln.Config = cfg
		cfg.Model = "MicroServiceChoiceReplacementDic"
		cfg.Manager = "linkTaskManagerReplacementDicFromChoice"
	case workflow.LinkStandardTaskConfig:
		l.ln.Config = cfg
		cfg.Model = "StandardTaskConfig"
		switch cfg.Manager {
		case "linkTaskManagerDirectories":
		case "linkTaskManagerFiles":
		case "linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList":
		case "linkTaskManagerGetMicroserviceGeneratedListInStdOut":
		case "":
			panic("@manager is empty")
		default:
			panic("@manager not supported: " + cfg.Manager)
		}
	case workflow.LinkTaskConfigSetUnitVariable:
		l.ln.Config = cfg
		cfg.Model = "TaskConfigSetUnitVariable"
		cfg.Manager = "linkTaskManagerSetUnitVariable"
	case workflow.LinkTaskConfigUnitVariableLinkPull:
		l.ln.Config = cfg
		cfg.Model = "TaskConfigUnitVariableLinkPull"
		cfg.Manager = "linkTaskManagerUnitVariableLinkPull"
	default:
		panic("config type is not supported")
	}
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

		var linkID *uuid.UUID
		v = items[i+2]
		target, ok := v.(string)
		if !ok {
			panic("Target must be a string.")
		}
		if v != "" {
			id := l.b.findID(target)
			if id == uuid.Nil {
				panic("Target must point to a known chain or link.... " + target)
			}
			linkID = &id
		}

		cs[code] = workflow.LinkExitCode{
			JobStatus: status,
			LinkID:    linkID,
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

var L = Labels

func Labels(keyvals ...string) workflow.I18nField {
	f := workflow.I18nField{}

	if len(keyvals) == 1 {
		keyvals = []string{"en", keyvals[0]}
	}

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
