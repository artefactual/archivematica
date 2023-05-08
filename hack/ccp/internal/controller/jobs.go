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

// DecisionJob:
// 1. Reload *Package (pull state from db into memory since it can be changed by client scripts).
// 2. Persist job in database: https://github.com/artefactual/archivematica/blob/fbda1a91d6dff086e7124fa1d7a3c7953d8755bb/src/MCPServer/lib/server/jobs/base.py#L76.
// 3. Load preconfigured choices, and resolve the job if the decision is preconfigured.
// 4. Otherwise, mark as awaiting decision, put on hold. Decision must be made by the user via the API.
// 5. ...
//
// Manager: linkTaskManagerChoice.
// Class: NextChainDecisionJob(DecisionJob) (decisions.py).
type chainChoice struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkMicroServiceChainChoice
}

func newChainChoice(logger logr.Logger, p *Package, wl *workflow.Link) (*chainChoice, error) {
	config, ok := wl.Config.(workflow.LinkMicroServiceChainChoice)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &chainChoice{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *chainChoice) exec(ctx context.Context) (uuid.UUID, error) {
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
	if decision, err := l.p.Await(ctx); err != nil {
		return uuid.UUID{}, err
	} else {
		return decision, nil
	}
}

type choiceReplacementDict struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkMicroServiceChoiceReplacementDic
}

func newChoiceReplacementDict(logger logr.Logger, p *Package, wl *workflow.Link) (*choiceReplacementDict, error) {
	config, ok := wl.Config.(workflow.LinkMicroServiceChoiceReplacementDic)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &choiceReplacementDict{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *choiceReplacementDict) exec(ctx context.Context) (uuid.UUID, error) {
	return l.wl.ExitCodes[0].LinkID, nil
}

type standardTask struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkStandardTaskConfig
}

func newStandardTask(logger logr.Logger, p *Package, wl *workflow.Link) (*standardTask, error) {
	config, ok := wl.Config.(workflow.LinkStandardTaskConfig)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &standardTask{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *standardTask) exec(ctx context.Context) (uuid.UUID, error) {
	if len(l.wl.ExitCodes) > 0 {
		if l.wl.ExitCodes[0].LinkID != uuid.Nil {
			return l.wl.ExitCodes[0].LinkID, nil
		}
	}
	return uuid.Nil, nil
}

type setUnitVariable struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkTaskConfigSetUnitVariable
}

func newSetUnitVariable(logger logr.Logger, p *Package, wl *workflow.Link) (*setUnitVariable, error) {
	config, ok := wl.Config.(workflow.LinkTaskConfigSetUnitVariable)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &setUnitVariable{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *setUnitVariable) exec(ctx context.Context) (uuid.UUID, error) {
	return l.config.ChainID, nil
}

type getUnitVariable struct {
	logger logr.Logger
	p      *Package
	wl     *workflow.Link
	config *workflow.LinkTaskConfigUnitVariableLinkPull
}

func newGetUnitVariable(logger logr.Logger, p *Package, wl *workflow.Link) (*getUnitVariable, error) {
	config, ok := wl.Config.(workflow.LinkTaskConfigUnitVariableLinkPull)
	if !ok {
		return nil, errors.New("invalid config")
	}

	return &getUnitVariable{
		logger: logger,
		p:      p,
		wl:     wl,
		config: &config,
	}, nil
}

func (l *getUnitVariable) exec(ctx context.Context) (uuid.UUID, error) {
	return l.config.ChainID, nil
}
