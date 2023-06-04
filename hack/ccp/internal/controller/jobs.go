// Types of jobs:
//   - Decision jobs:
//     outputDecisionJob, nextChainDecisionJob, updateContextDecisionJob.
//   - Client jobs:
//     directoryClientScriptJob, filesClientScriptJob, outputClientScriptJob
//   - Local jobs:
//     setUnitVarLinkJob, getUnitVarLinkJob
package controller

import (
	"context"
	"errors"

	"github.com/artefactual/archivematica/hack/ccp/internal/workflow"
	"github.com/go-logr/logr"
	"github.com/google/uuid"
)

// job is an executable unit that wraps a workflow chain link.
type job interface {
	exec(context.Context) (uuid.UUID, error)
}

// Job.
//
// Manager: linkTaskManagerGetUserChoiceFromMicroserviceGeneratedList.
// Class: OutputDecisionJob(DecisionJob).
type outputDecisionJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkStandardTaskConfig
}

func newOutputDecisionJob(logger logr.Logger, p *Package, wl *workflow.Link) (*outputDecisionJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &outputDecisionJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *outputDecisionJob) exec(ctx context.Context) (uuid.UUID, error) {
	return uuid.Nil, nil
}

// Job.
//
// 1. Reload *Package (pull state from db into memory since it can be changed by client scripts).
// 2. Persist job in database: https://github.com/artefactual/archivematica/blob/fbda1a91d6dff086e7124fa1d7a3c7953d8755bb/src/MCPServer/lib/server/jobs/base.py#L76.
// 3. Load preconfigured choices, and resolve the job if the decision is preconfigured.
// 4. Otherwise, mark as awaiting decision, put on hold. Decision must be made by the user via the API.
// 5. ...
//
// Manager: linkTaskManagerChoice.
// Class: NextChainDecisionJob(DecisionJob).
type nextChainDecisionJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkMicroServiceChainChoice
}

func newNextChainDecisionJob(logger logr.Logger, p *Package, wl *workflow.Link) (*nextChainDecisionJob, error) {
	config, ok := wl.Config.(workflow.LinkMicroServiceChainChoice)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &nextChainDecisionJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *nextChainDecisionJob) exec(ctx context.Context) (uuid.UUID, error) {
	choice, err := l.p.PreconfiguredChoice(l.wl.ID)
	if err != nil {
		return uuid.UUID{}, err
	}

	// When we have a preconfigured choice.
	if choice != nil {
		ret, err := uuid.Parse(choice.GoToChain)
		if err != nil {
			return uuid.UUID{}, err
		}
		return ret, nil
	}

	// Await until choice is made.
	if decision, err := l.p.AwaitDecision(ctx); err != nil {
		return uuid.UUID{}, err
	} else {
		return decision, nil
	}
}

// Job.
//
// Manager: linkTaskManagerReplacementDicFromChoice.
// Class: UpdateContextDecisionJob(DecisionJob) (decisions.py).
type updateContextDecisionJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkMicroServiceChoiceReplacementDic
}

func newUpdateContextDecisionJob(logger logr.Logger, p *Package, wl *workflow.Link) (*updateContextDecisionJob, error) {
	config, ok := wl.Config.(workflow.LinkMicroServiceChoiceReplacementDic)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &updateContextDecisionJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *updateContextDecisionJob) exec(ctx context.Context) (uuid.UUID, error) {
	return l.wl.ExitCodes[0].LinkID, nil
}

// Job.
//
// Manager: linkTaskManagerDirectories.
// Class: DirectoryClientScriptJob(DecisionJob).
type directoryClientScriptJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkStandardTaskConfig
}

func newDirectoryClientScriptJob(logger logr.Logger, p *Package, wl *workflow.Link) (*directoryClientScriptJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &directoryClientScriptJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *directoryClientScriptJob) exec(ctx context.Context) (uuid.UUID, error) {
	return uuid.Nil, nil
}

// Job.
//
// Manager: linkTaskManagerFiles.
// Class: FilesClientScriptJob(DecisionJob).
type filesClientScriptJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkStandardTaskConfig
}

func newFilesClientScriptJob(logger logr.Logger, p *Package, wl *workflow.Link) (*filesClientScriptJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &filesClientScriptJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *filesClientScriptJob) exec(ctx context.Context) (uuid.UUID, error) {
	return uuid.Nil, nil
}

// Job.
//
// Manager: linkTaskManagerGetMicroserviceGeneratedListInStdOut.
// Class: OutputClientScriptJob(DecisionJob).
type outputClientScriptJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkStandardTaskConfig
}

func newOutputClientScriptJob(logger logr.Logger, p *Package, wl *workflow.Link) (*outputClientScriptJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &outputClientScriptJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *outputClientScriptJob) exec(ctx context.Context) (uuid.UUID, error) {
	return uuid.Nil, nil
}

// setUnitVarLinkJob is a local job that sets the unit variable configured in the workflow.
//
// Manager: linkTaskManagerSetUnitVariable.
// Class: SetUnitVarLinkJob(DecisionJob) (decisions.py).
type setUnitVarLinkJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkTaskConfigSetUnitVariable
}

func newSetUnitVarLinkJob(logger logr.Logger, p *Package, wl *workflow.Link) (*setUnitVarLinkJob, error) {
	config, ok := wl.Config.(workflow.LinkTaskConfigSetUnitVariable)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &setUnitVarLinkJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *setUnitVarLinkJob) exec(ctx context.Context) (uuid.UUID, error) {
	return l.config.ChainID, nil
}

// getUnitVarLinkJob is a local job that gets the next link in the chain from a UnitVariable.
//
// Manager: linkTaskManagerUnitVariableLinkPull.
// Class: GetUnitVarLinkJob(DecisionJob) (decisions.py).
type getUnitVarLinkJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkTaskConfigUnitVariableLinkPull
}

func newGetUnitVarLinkJob(logger logr.Logger, p *Package, wl *workflow.Link) (*getUnitVarLinkJob, error) {
	config, ok := wl.Config.(workflow.LinkTaskConfigUnitVariableLinkPull)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &getUnitVarLinkJob{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *getUnitVarLinkJob) exec(ctx context.Context) (uuid.UUID, error) {
	return l.config.ChainID, nil
}
