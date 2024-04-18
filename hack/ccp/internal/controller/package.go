package controller

import (
	"context"
	"errors"
	"fmt"
	"io/fs"
	"iter"
	"maps"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/elliotchance/orderedmap/v2"
	"github.com/go-logr/logr"
	"github.com/google/uuid"

	"github.com/artefactual/archivematica/hack/ccp/internal/python"
	"github.com/artefactual/archivematica/hack/ccp/internal/store"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

// A Package can be a Transfer, a SIP, or a DIP.
type Package struct {
	logger logr.Logger

	// Datastore.
	store store.Store

	// Path of the shared directory.
	sharedDir string

	// The underlying package type.
	unit

	// Identifier, populated by hydrate().
	id uuid.UUID

	// Current path, populated by hydrate().
	path string

	// Whether the package was submitted as a directory.
	isDir bool

	// Watched directory workflow document.
	watchedAt *workflow.WatchedDirectory

	// User decisinon manager
	decision decision
}

func NewPackage(ctx context.Context, logger logr.Logger, store store.Store, path, sharedDir string, wd *workflow.WatchedDirectory) (*Package, error) {
	fi, err := os.Stat(path)
	if err != nil {
		return nil, fmt.Errorf("stat: %v", err)
	}

	p := &Package{
		logger:    logger,
		store:     store,
		path:      path,
		isDir:     fi.IsDir(),
		sharedDir: sharedDir,
		watchedAt: wd,
	}

	switch {
	case wd.UnitType == "Transfer":
		p.unit = &Transfer{pkg: p}
	case wd.UnitType == "SIP" && p.isDir:
		p.unit = &SIP{pkg: p}
	case wd.UnitType == "DIP" && p.isDir:
		p.unit = &DIP{pkg: p}
	default:
		return nil, fmt.Errorf("unexpected type given for file %q (dir: %t)", path, p.isDir)
	}

	if err := p.hydrate(ctx, path, wd.Path); err != nil {
		return nil, fmt.Errorf("hydrate: %v", err)
	}

	return p, nil
}

// Path returns the real (no share dir vars) path to the package.
func (p *Package) Path() string {
	return strings.Replace(p.path, "%sharedPath%", p.sharedDir, 1)
}

func (p *Package) UpdatePath(path string) {
	p.path = strings.Replace(p.path, "%sharedPath%", p.sharedDir, 1)
}

// PathForDB returns the path to the package, as stored in the database.
func (p *Package) PathForDB() string {
	return strings.Replace(p.path, p.sharedDir, "%sharedPath%", 1)
}

// Name returns the package name derived from its dirname.
func (p *Package) Name() string {
	name := filepath.Base(filepath.Clean(p.Path()))
	return strings.Replace(name, "-"+p.id.String(), "", 1)
}

// String implements fmt.Stringer.
func (p *Package) String() string {
	return p.Name()
}

func (p *Package) PreconfiguredChoice(linkID uuid.UUID) (*workflow.Choice, error) {
	li := linkID.String()

	// TODO: automate "Approve standard transfer" until we can submit decisions.
	if li == "0c94e6b5-4714-4bec-82c8-e187e0c04d77" {
		return &workflow.Choice{
			AppliesTo: "0c94e6b5-4714-4bec-82c8-e187e0c04d77",
			GoToChain: "b4567e89-9fea-4256-99f5-a88987026488",
		}, nil
	}

	f, err := os.Open(filepath.Join(p.path, "processingMCP.xml"))
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	// TODO: this could be cached if the file isn't going to change.
	choices, err := workflow.ParseConfig(f)
	if err != nil {
		return nil, err
	}

	var match *workflow.Choice
	for _, choice := range choices {
		if choice.AppliesTo == li {
			match = &choice
			break
		}
	}

	// Resort to automated config.
	// TODO: allow user to choose the system processing config to use.
	if match == nil {
		for _, choice := range workflow.AutomatedConfig.Choices.Choices {
			if choice.AppliesTo == li {
				match = &choice
				break
			}
		}
	}

	return match, nil
}

// Decide resolves an awaiting decision.
func (p *Package) Decide(opt option) error {
	return p.decision.resolve(opt)
}

// AwaitDecision builds a new decision and waits for its resolution.
func (p *Package) AwaitDecision(ctx context.Context, opts []option) (option, error) {
	p.decision.build(opts...)

	for {
		select {
		case d := <-p.decision.recv:
			return d, nil
		case <-ctx.Done():
			return option(""), ctx.Err()
		}
	}
}

// Decision provides the current awaiting decision.
func (p *Package) Decision() []option {
	return p.decision.decision()
}

// Files iterates over all files associated with the package or that should be
// associated with a package, i.e. it first yields files based on database
// records verified to exist on the filesystem, then yields additional files
// found through filesystem traversal that meet specified filters.
//
// Parameters:
//   - filterFilenameStart: the function filters files whose names start with
//     the specified prefix.
//   - filterFilenameEnd: the function filters files whose names end with
//     the specified suffix.
//   - filterSubdir: the function limits the search to files within
//     the specified subdirectory.
//
// TODO: https://github.com/artefactual/archivematica/blob/95a1daba07a1037dccaf628428fb3b39b795b75e/src/MCPServer/lib/server/packages.py#L649-L700
func (p *Package) Files(filterFilenameStart, filterFilenameEnd, filterSubdir string) iter.Seq2[replacementMapping, error] {
	filesReturnedAlready := map[string]struct{}{}
	return func(yield func(replacementMapping, error) bool) {
		if false {
			yield(map[string]replacement{}, nil)
		}
		err := filepath.WalkDir(p.Path(), func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return err
			}
			fname := d.Name()
			if filterFilenameStart != "" && !strings.HasPrefix(fname, filterFilenameStart) {
				return nil
			}
			if filterFilenameStart != "" && !strings.HasPrefix(fname, filterFilenameStart) {
				return nil
			}
			if _, ok := filesReturnedAlready[path]; !ok {
				yield(map[string]replacement{
					"%relativeLocation": replacement(path),
					"%fileUUID%":        replacement(""),
					"%fileGrpUse%":      replacement(""),
				}, nil)
			}
			return nil
		})
		if err != nil {
			yield(nil, err)
		}
	}
}

func (p *Package) replacements() replacementMapping {
	return map[string]replacement{
		"%tmpDirectory%":        replacement(joinPath(p.sharedDir, "tmp", "")),
		"%processingDirectory%": replacement(joinPath(p.sharedDir, "currentlyProcessing", "")),
		"%watchDirectoryPath%":  replacement(joinPath(p.sharedDir, "watchedDirectories", "")),
		"%rejectedDirectory%":   replacement(joinPath(p.sharedDir, "rejected", "")),
	}
}

// saveValue persists "value" as a package variable.
func (p *Package) saveValue(ctx context.Context, name, value string) error {
	if err := p.store.CreateUnitVar(ctx, p.id, p.watchedAt.UnitType, name, value, uuid.Nil, true); err != nil {
		return fmt.Errorf("save value: %v", err)
	}
	return nil
}

// saveLinkID persist "linkID" as a package variable.
func (p *Package) saveLinkID(ctx context.Context, name string, linkID uuid.UUID) error {
	if err := p.store.CreateUnitVar(ctx, p.id, p.watchedAt.UnitType, name, "", linkID, true); err != nil {
		return fmt.Errorf("save linkID: %v", err)
	}
	return nil
}

type replacement string

// escape special characters like slashes, quotes, and backticks.
func (r replacement) escape() string {
	v := string(r)

	// Escape backslashes first
	v = strings.ReplaceAll(v, "\\", "\\\\")

	var escaped string
	for _, char := range v {
		switch char {
		case '\\':
			escaped += "\\\\"
		case '"', '`':
			escaped += "\\" + string(char)
		default:
			escaped += string(char)
		}
	}

	return escaped
}

type replacementMapping map[string]replacement

func (rm replacementMapping) withContext(pCtx *packageContext) {
	for el := pCtx.Front(); el != nil; el = el.Next() {
		rm[el.Key] = rm[el.Value]
	}
}

type unit interface {
	hydrate(ctx context.Context, path, watchedDir string) error
	reload(ctx context.Context) error
	markProcessing(ctx context.Context) error
	markDone(ctx context.Context) error
	replacements(filterSubdirPath string) replacementMapping
	replacementPath() string
	unitVariableType() string
	jobUnitType() string
}

type Transfer struct {
	pkg                     *Package
	processingConfiguration string
}

var _ unit = (*Transfer)(nil)

func (u *Transfer) hydrate(ctx context.Context, path, watchedDir string) error {
	path = strings.Replace(path, "%sharedPath%", u.pkg.sharedDir, 1)
	id := uuidFromPath(path)
	created := false

	// Ensure that a Transfer is either created or updated. The strategy differs
	// depending on whether we know both its identifier and location, or only
	// the latter.
	if id != uuid.Nil {
		var opErr error
		created, opErr = u.pkg.store.UpsertTransfer(ctx, id, path)
		if opErr != nil {
			return opErr
		}
	} else {
		var opErr error
		id, created, opErr = u.pkg.store.EnsureTransfer(ctx, path)
		if opErr != nil {
			return opErr
		}
	}

	u.pkg.id = id
	u.pkg.path = path
	u.pkg.logger.V(1).Info("Transfer hydrated.", "created", created, "id", id)

	return nil
}

func (u *Transfer) reload(ctx context.Context) error {
	path, err := u.pkg.store.ReadTransferLocation(ctx, u.pkg.id)
	if err != nil {
		return err
	}
	u.pkg.UpdatePath(path)

	name, err := u.pkg.store.ReadUnitVar(ctx, u.pkg.id, u.unitVariableType(), "processingConfiguration")
	if errors.Is(err, store.ErrNotFound) {
		u.processingConfiguration = "default"
	} else if err != nil {
		return err
	} else {
		u.processingConfiguration = name
	}

	return nil
}

func (u *Transfer) markProcessing(ctx context.Context) error {
	// def queryset(self): return models.Transfer.objects.filter(pk=self.uuid)
	return nil
}

func (u *Transfer) markDone(ctx context.Context) error {
	// def queryset(self): return models.Transfer.objects.filter(pk=self.uuid)
	return nil
}

func (u *Transfer) replacements(filterSubdirPath string) replacementMapping {
	mapping := u.pkg.replacements()
	maps.Copy(mapping, baseReplacements(u.pkg))
	maps.Copy(mapping, map[string]replacement{
		u.replacementPath():        replacement(u.pkg.Path()),
		"%unitType%":               replacement(u.unitVariableType()),
		"%processingConfiguration": replacement(u.processingConfiguration),
	})

	return mapping
}

func (u *Transfer) replacementPath() string {
	return "%transferDirectory%"
}

func (u *Transfer) unitVariableType() string {
	return "Transfer"
}

func (u *Transfer) jobUnitType() string {
	return "unitTransfer"
}

type SIP struct {
	pkg         *Package
	aipFilename string
	sipType     string
}

var _ unit = (*SIP)(nil)

func (u *SIP) hydrate(ctx context.Context, path, watchedDir string) error {
	return nil
}

func (u *SIP) reload(ctx context.Context) error {
	// sip = models.SIP.objects.get(uuid=self.uuid)
	// self.current_path = sip.currentpath
	// self.aip_filename = sip.aip_filename or ""
	// self.sip_type = sip.sip_type
	return nil
}

func (u *SIP) markProcessing(ctx context.Context) error {
	// def queryset(self): return models.SIP.objects.filter(pk=self.uuid)
	return nil
}

func (u *SIP) markDone(ctx context.Context) error {
	// def queryset(self): return models.SIP.objects.filter(pk=self.uuid)
	return nil
}

func (u *SIP) replacements(filterSubdirPath string) replacementMapping {
	mapping := u.pkg.replacements()
	maps.Copy(mapping, baseReplacements(u.pkg))
	maps.Copy(mapping, map[string]replacement{
		"%unitType%":   replacement(u.unitVariableType()),
		"%AIPFilename": replacement(u.aipFilename),
		"%SIPType%":    replacement(u.sipType),
	})
	return mapping
}

func (u *SIP) replacementPath() string {
	return "%SIPDirectory%"
}

func (u *SIP) unitVariableType() string {
	return "SIP"
}

func (u *SIP) jobUnitType() string {
	return "unitSIP"
}

type DIP struct {
	pkg *Package
}

var _ unit = (*DIP)(nil)

func (u *DIP) hydrate(ctx context.Context, path, watchedDir string) error {
	return nil
}

func (u *DIP) reload(ctx context.Context) error {
	return nil // No-op.
}

func (u *DIP) markProcessing(ctx context.Context) error {
	// def queryset(self): return models.SIP.objects.filter(pk=self.uuid)
	return nil
}

func (u *DIP) markDone(ctx context.Context) error {
	// def queryset(self): return models.SIP.objects.filter(pk=self.uuid)
	return nil
}

func (u *DIP) replacements(filterSubdirPath string) replacementMapping {
	mapping := u.pkg.replacements()
	maps.Copy(mapping, baseReplacements(u.pkg))
	maps.Copy(mapping, map[string]replacement{
		"%unitType%": replacement(u.unitVariableType()),
	})
	if filterSubdirPath != "" {
		mapping["%relativeLocation%"] = replacement(
			strings.Replace(filterSubdirPath, "%sharedPath%", u.pkg.sharedDir, 1),
		)
	}

	return mapping
}

func (u *DIP) replacementPath() string {
	return "%SIPDirectory%"
}

func (u *DIP) unitVariableType() string {
	return "DIP"
}

func (u *DIP) jobUnitType() string {
	return "unitDIP"
}

type decision struct {
	opts     []option
	recv     chan option
	unsolved atomic.Bool
	sync.Mutex
}

func (pd *decision) build(opts ...option) {
	pd.Lock()
	pd.opts = opts
	pd.recv = make(chan option) // is this ok?
	pd.Unlock()

	pd.unsolved.Store(true)
}

func (pd *decision) resolve(opt option) error {
	if !pd.unsolved.Load() {
		return errors.New("decision is not pending resolution")
	}

	select {
	case pd.recv <- opt:
		pd.unsolved.Store(false)
	default:
		return errors.New("resolve can't proceed because nobody is listening")
	}

	return nil
}

func (pd *decision) decision() []option {
	if !pd.unsolved.Load() {
		return nil
	}

	var opts []option
	if pd.unsolved.Load() {
		pd.Lock()
		opts = make([]option, len(pd.opts))
		copy(opts, pd.opts)
		pd.Unlock()
	}

	return opts
}

// option is a single selectable decision choice.
//
// In most cases, an option is the UUID of a workflow item, but there is one
// exception: "Store DIP location", containing a location path.
type option string

func (do option) uuid() uuid.UUID {
	id, err := uuid.Parse(string(do))
	if err != nil {
		return uuid.Nil
	}
	return id
}

func dirBasename(path string) string {
	abs, _ := filepath.Abs(path)
	return filepath.Base(abs)
}

// Replacements needed by all unit types.
func baseReplacements(p *Package) replacementMapping {
	path := p.Path()
	return map[string]replacement{
		"%SIPUUID%":              replacement(p.id.String()),
		"%SIPName%":              replacement(p.Name()),
		"%SIPLogsDirectory%":     replacement(joinPath(path, "logs", "")),
		"%SIPObjectsDirectory%":  replacement(joinPath(path, "objects", "")),
		"%SIPDirectory%":         replacement(path),
		"%SIPDirectoryBasename%": replacement(dirBasename(path)),
		"%relativeLocation%":     replacement(p.PathForDB()),
	}
}

// packageContext tracks choices made previously while processing.
type packageContext struct {
	// We're using an ordered map to mimic PackageContext's use of OrderedDict.
	// It may not be necessary after all.
	*orderedmap.OrderedMap[string, string]
}

func loadContext(ctx context.Context, p *Package) (*packageContext, error) {
	pCtx := &packageContext{
		orderedmap.NewOrderedMap[string, string](),
	}

	// TODO: we shouldn't need one UnitVariable per chain, with all the same values.
	vars, err := p.store.ReadUnitVars(ctx, p.id, p.unitVariableType(), "replacementDict")
	if err != nil {
		return nil, err
	}
	for _, item := range vars {
		if item.Value == nil {
			continue
		}
		m, err := python.EvalMap(*item.Value)
		if err != nil {
			p.logger.Error(err, "Failed to eval unit variable value %q.", *item.Value)
			continue
		}
		for k, v := range m {
			pCtx.Set(k, v)
		}
	}

	kvs := []any{"len", pCtx.Len()}
	for el := pCtx.Front(); el != nil; el = el.Next() {
		kvs = append(kvs, fmt.Sprintf("var:%s", el.Key), el.Value)
	}
	p.logger.V(2).Info("Package context loaded from the database.", kvs...)

	return pCtx, nil
}

func (ctx *packageContext) copy() *orderedmap.OrderedMap[string, string] {
	return ctx.Copy()
}
