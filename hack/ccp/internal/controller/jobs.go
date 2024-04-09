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
	"github.com/sevein/gearmin"
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
	// When we have a preconfigured choice.
	choice, err := l.p.PreconfiguredChoice(l.wl.ID)
	if err != nil {
		return uuid.Nil, err
	}
	if choice != nil {
		if ret, err := uuid.Parse(choice.GoToChain); err != nil {
			l.logger.Info("Preconfigured choice is not a valid UUID.", "choice", choice.GoToChain, "err", err)
		} else {
			return ret, nil
		}
	}

	// Build decision options.
	opts := make([]option, len(l.config.Choices))
	for i, item := range l.config.Choices {
		opts[i] = option(item.String())
	}

	// Wait for decision resolution.
	if decision, err := l.p.AwaitDecision(ctx, opts); err != nil {
		return uuid.Nil, err
	} else {
		return decision.uuid(), nil
	}
}

// updateContextDecisionJob is a job that updates the chain context based on a user choice.
//
// Manager: linkTaskManagerReplacementDicFromChoice (14 matches).
// Class: UpdateContextDecisionJob(DecisionJob) (decisions.py).
type updateContextDecisionJob struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkMicroServiceChoiceReplacementDic
}

// nolint: unused
var updateContextDecisionJobChoiceMapping = map[string]string{
	// Decision point "Assign UUIDs to directories?".
	"8882bad4-561c-4126-89c9-f7f0c083d5d7": "bd899573-694e-4d33-8c9b-df0af802437d",
	"e10a31c3-56df-4986-af7e-2794ddfe8686": "bd899573-694e-4d33-8c9b-df0af802437d",
	"d6f6f5db-4cc2-4652-9283-9ec6a6d181e5": "bd899573-694e-4d33-8c9b-df0af802437d",
	"1563f22f-f5f7-4dfe-a926-6ab50d408832": "bd899573-694e-4d33-8c9b-df0af802437d",
	// Decision "Yes" (for "Assign UUIDs to directories?").
	"7e4cf404-e62d-4dc2-8d81-6141e390f66f": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
	"2732a043-b197-4cbc-81ab-4e2bee9b74d3": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
	"aa793efa-1b62-498c-8f92-cab187a99a2a": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
	"efd98ddb-80a6-4206-80bf-81bf00f84416": "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
	// Decision "No" (for "Assign UUIDs to directories?").
	"0053c670-3e61-4a3e-a188-3a2dd1eda426": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
	"8e93e523-86bb-47e1-a03a-4b33e13f8c5e": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
	"6dfbeff8-c6b1-435b-833a-ed764229d413": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
	"dc0ee6b6-ed5f-42a3-bc8f-c9c7ead03ed1": "891f60d0-1ba8-48d3-b39e-dd0934635d29",
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
	id := l.wl.ExitCodes[0].LinkID
	if id == nil || *id == uuid.Nil {
		return uuid.Nil, errors.New("ops")
	}
	return *id, nil
}

// Job.
//
// Manager: linkTaskManagerDirectories.
// Class: DirectoryClientScriptJob(DecisionJob).
type directoryClientScriptJob struct {
	logger  logr.Logger
	gearman *gearmin.Server
	p       *Package
	wl      *workflow.Link
	config  *workflow.LinkStandardTaskConfig
}

func newDirectoryClientScriptJob(logger logr.Logger, gearman *gearmin.Server, p *Package, wl *workflow.Link) (*directoryClientScriptJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &directoryClientScriptJob{
		logger:  logger,
		gearman: gearman,
		p:       p,
		wl:      wl,
		config:  &config,
	}, nil
}

func (l *directoryClientScriptJob) exec(ctx context.Context) (uuid.UUID, error) {
	data, err := submitJob(ctx, l.gearman, l.config.Execute, []byte("todo-args"))
	if err != nil {
		return uuid.Nil, err
	}

	l.logger.V(1).Info("data", data)

	return uuid.Nil, nil
}

// Job.
//
// Manager: linkTaskManagerFiles.
// Class: FilesClientScriptJob(DecisionJob).
type filesClientScriptJob struct {
	logger  logr.Logger
	gearman *gearmin.Server
	p       *Package
	wl      *workflow.Link
	config  *workflow.LinkStandardTaskConfig
}

func newFilesClientScriptJob(logger logr.Logger, gearman *gearmin.Server, p *Package, wl *workflow.Link) (*filesClientScriptJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &filesClientScriptJob{
		logger:  logger,
		gearman: gearman,
		p:       p,
		wl:      wl,
		config:  &config,
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
	logger  logr.Logger
	gearman *gearmin.Server
	p       *Package
	wl      *workflow.Link
	config  *workflow.LinkStandardTaskConfig
}

func newOutputClientScriptJob(logger logr.Logger, gearman *gearmin.Server, p *Package, wl *workflow.Link) (*outputClientScriptJob, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &outputClientScriptJob{
		logger:  logger,
		gearman: gearman,
		p:       p,
		wl:      wl,
		config:  &config,
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

func submitJob(ctx context.Context, gearman *gearmin.Server, funcName string, data []byte) ([]byte, error) {
	var (
		ret  []byte
		err  error
		done = make(chan struct{})
	)

	gearman.Submit(
		&gearmin.JobRequest{
			FuncName:   funcName,
			Data:       data,
			Background: false,
			Callback: func(update gearmin.JobUpdate) {
				switch update.Type {
				case gearmin.JobUpdateTypeComplete:
					ret = update.Data
					done <- struct{}{}
				case gearmin.JobUpdateTypeException:
					ret = update.Data
					err = errors.New("failed")
					done <- struct{}{}
				case gearmin.JobUpdateTypeFail:
					err = errors.New("failed")
					done <- struct{}{}
				}
			},
		},
	)

	select {
	case <-done:
		return ret, err
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}
