package controller

import (
	"context"
	"errors"
	"fmt"
	"io/fs"
	"maps"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"

	"github.com/go-logr/logr"
	"github.com/google/uuid"
	"iter"

	"github.com/artefactual/archivematica/hack/ccp/internal/store"
	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
)

// A Package can be a Transfer, a SIP, or a DIP.
type Package struct {
	logger    logr.Logger
	store     store.Store
	id        uuid.UUID
	path      string
	base      string
	name      string
	isDir     bool
	sharedDir string
	watchedAt *workflow.WatchedDirectory
	decision  decision
	unit
}

func NewPackage(ctx context.Context, logger logr.Logger, store store.Store, path, sharedDir string, wd *workflow.WatchedDirectory) (*Package, error) {
	fi, err := os.Stat(path)
	if err != nil {
		return nil, fmt.Errorf("stat: %v", err)
	}

	base, name := filepath.Split(path)

	p := &Package{
		logger:    logger,
		store:     store,
		path:      path,
		base:      base,
		name:      name,
		isDir:     fi.IsDir(),
		sharedDir: sharedDir,
		watchedAt: wd,
	}

	switch {
	case wd.UnitType == "Transfer":
		p.unit = &Transfer{p: p}
	case wd.UnitType == "SIP" && p.isDir:
		p.unit = &SIP{p: p}
	case wd.UnitType == "DIP" && p.isDir:
		p.unit = &DIP{p: p}
	default:
		return nil, fmt.Errorf("unexpected type given for file %q (dir: %t)", path, p.isDir)
	}

	if err := p.hydrate(ctx, path, wd.Path); err != nil {
		return nil, fmt.Errorf("hydrate: %v", err)
	}

	return p, nil
}

func (p *Package) String() string {
	return p.name
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
		err := filepath.WalkDir(p.base, func(path string, d fs.DirEntry, err error) error {
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
		"%tmpDirectory%":        replacement(filepath.Join(p.sharedDir, "tmp")),
		"%processingDirectory%": replacement(filepath.Join(p.sharedDir, "currentlyProcessing")),
		"%watchDirectoryPath%":  replacement(filepath.Join(p.sharedDir, "watchedDirectories")),
		"%rejectedDirectory%":   replacement(filepath.Join(p.sharedDir, "rejected")),
	}
}

type replacement string

// escape special characters like slashes, quotes, and backticks.
func (r replacement) escape() string {
	v := string(r)
	v = strings.ReplaceAll(v, "\\", "\\\\")
	v = strings.ReplaceAll(v, "\"", "\\\"")
	v = strings.ReplaceAll(v, "`", "\\`")
	return v
}

type replacementMapping map[string]replacement

func (rm replacementMapping) withContext(ctx jobContext) {
	maps.Copy(ctx.replacements, rm)
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
	p                       *Package
	currentPath             string
	processingConfiguration string
}

var _ unit = (*Transfer)(nil)

func (u *Transfer) hydrate(ctx context.Context, path, watchedDir string) error {
	path = strings.Replace(path, "%sharedPath%", u.p.sharedDir, 1)

	id, err := uuidFromPath(path)
	if err != nil {
		return fmt.Errorf("read UUID from path: %v", err)
	}

	created := true

	// Ensure that a Transfer is either created or updated. The strategy differs
	// depending on whether we know both its identifier and location, or only
	// the latter.
	if id != uuid.Nil {
		var opErr error
		created, opErr = u.p.store.UpsertTransfer(ctx, id, path)
		if opErr != nil {
			return opErr
		}
	} else {
		var opErr error
		id, created, opErr = u.p.store.EnsureTransfer(ctx, path)
		if opErr != nil {
			return opErr
		}
	}

	u.p.logger.V(1).Info("Transfer hydrated.", "created", created, "id", id, "path", path)

	return nil
}

func (u *Transfer) reload(ctx context.Context) error {
	// transfer = models.Transfer.objects.get(uuid=self.uuid)
	// self.current_path = transfer.currentlocation
	// self.processing_configuration = transfer.processing_configuration
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
	mapping := u.p.replacements()
	maps.Copy(mapping, baseReplacements(u.p, u.currentPath))
	maps.Copy(mapping, map[string]replacement{
		u.replacementPath():        replacement(u.currentPath),
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
	p           *Package
	currentPath string
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
	mapping := u.p.replacements()
	maps.Copy(mapping, baseReplacements(u.p, u.currentPath))
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
	p           *Package
	currentPath string
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
	mapping := u.p.replacements()
	maps.Copy(mapping, baseReplacements(u.p, u.currentPath))
	maps.Copy(mapping, map[string]replacement{
		"%unitType%": replacement(u.unitVariableType()),
	})
	if filterSubdirPath != "" {
		mapping["%relativeLocation%"] = replacement(
			strings.Replace(filterSubdirPath, "%sharedPath%", u.p.sharedDir, 1),
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
func baseReplacements(p *Package, currentPath string) replacementMapping {
	return map[string]replacement{
		"%SIPUUID%":              replacement(p.id.String()),
		"%SIPName%":              replacement(p.name),
		"%SIPLogsDirectory%":     replacement(filepath.Join(currentPath, "logs") + string(filepath.Separator)),
		"%SIPObjectsDirectory%":  replacement(filepath.Join(currentPath, "objects") + string(filepath.Separator)),
		"%SIPDirectory%":         replacement(currentPath),
		"%SIPDirectoryBasename%": replacement(dirBasename(currentPath)),
		"%relativeLocation%":     replacement(strings.Replace(currentPath, "%sharedPath%", p.sharedDir, 1)),
	}
}

func uuidFromPath(path string) (uuid.UUID, error) {
	path = strings.TrimRight(path, "/")
	if len(path) < 36 {
		return uuid.Nil, fmt.Errorf("path is too short")
	}
	id, err := uuid.Parse(path[len(path)-36:])
	if err != nil {
		return uuid.Nil, err
	}
	return id, nil
}
