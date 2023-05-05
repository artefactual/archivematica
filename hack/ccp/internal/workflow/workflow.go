package workflow

import (
	"embed"
	"encoding/json"
	"fmt"
)

//go:embed assets/*
var assets embed.FS

func LoadEmbedded(name string) (*Document, error) {
	data, err := assets.ReadFile(name)
	if err != nil {
		return nil, err
	}

	var doc Document
	err = json.Unmarshal(data, &doc)
	if err != nil {
		return nil, err
	}

	return &doc, nil
}

func Default() (*Document, error) {
	const name = "assets/workflow.json"
	return LoadEmbedded(name)
}

func LoadFromJSON(blob []byte) (*Document, error) {
	var d Document
	if err := json.Unmarshal(blob, &d); err != nil {
		return nil, fmt.Errorf("error decoding workflow: %v", err)
	}

	return &d, nil
}

type I18nField map[string]string

type WatchedDirectory struct {
	ChainID  string `json:"chain_id"`
	OnlyDirs bool   `json:"only_dirs"`
	Path     string `json:"path"`
	UnitType string `json:"unit_type"`
}

type Chain struct {
	ID          string    `json:"-"`
	Description I18nField `json:"description"`
	LinkID      string    `json:"link_id"`
	Start       bool      `json:"start"`
}

type Link struct {
	ID                string                `json:"-"`
	Config            interface{}           `json:"config"`
	Description       I18nField             `json:"description"`
	ExitCodes         map[int]*LinkExitCode `json:"exit_codes"`
	FallbackJobStatus string                `json:"fallback_job_status"`
	FallbackLinkID    string                `json:"fallback_link_id"`
	Group             I18nField             `json:"group"`
	End               bool                  `json:"end"`
}

type linkProxy Link

func (l *Link) UnmarshalJSON(b []byte) error {
	// First pass to retrieve model attribute.
	configModel := struct {
		Config struct {
			Model string `json:"@model"`
		} `json:"config"`
	}{}
	if err := json.Unmarshal(b, &configModel); err != nil {
		return err
	}

	// Second pass to retrieve raw config.
	rawConfig := struct {
		Config json.RawMessage `json:"config"`
	}{}
	if err := json.Unmarshal(b, &rawConfig); err != nil {
		return err
	}

	link := linkProxy{}
	if err := json.Unmarshal(b, &link); err != nil {
		return err
	}
	*l = Link(link)

	switch configModel.Config.Model {
	case "MicroServiceChainChoice":
		config := LinkMicroServiceChainChoice{}
		if err := json.Unmarshal(rawConfig.Config, &config); err != nil {
			return err
		}
		l.Config = config
	case "MicroServiceChoiceReplacementDic":
		config := LinkMicroServiceChoiceReplacementDic{}
		if err := json.Unmarshal(rawConfig.Config, &config); err != nil {
			return err
		}
		l.Config = config
	case "StandardTaskConfig":
		config := LinkStandardTaskConfig{}
		if err := json.Unmarshal(rawConfig.Config, &config); err != nil {
			return err
		}
		l.Config = config
	case "TaskConfigSetUnitVariable":
		config := LinkTaskConfigUnitVariableLinkPull{}
		if err := json.Unmarshal(rawConfig.Config, &config); err != nil {
			return err
		}
		l.Config = config
	case "TaskConfigUnitVariableLinkPull":
		config := LinkTaskConfigUnitVariableLinkPull{}
		if err := json.Unmarshal(rawConfig.Config, &config); err != nil {
			return err
		}
		l.Config = config
	default:
		return fmt.Errorf("unknown link model: %s", configModel.Config.Model)
	}

	return nil
}

type LinkExitCode struct {
	JobStatus string `json:"job_status"`
	LinkID    string `json:"link_id"`
}

type Document struct {
	WatchedDirectories []*WatchedDirectory `json:"watched_directories"`
	Chains             map[string]*Chain   `json:"chains"`
	Links              map[string]*Link    `json:"links"`
}

type sharedLink struct {
	Model   string `json:"@model"`
	Manager string `json:"@manager"`
}

type LinkMicroServiceChainChoice struct {
	sharedLink
	Choices []string `json:"chain_choices"`
}

type ConfigReplacement struct {
	ID          string            `json:"id"`
	Description I18nField         `json:"description"`
	Items       map[string]string `json:"items"`
}

type LinkMicroServiceChoiceReplacementDic struct {
	sharedLink
	Replacements []ConfigReplacement `json:"replacements"`
}

type LinkStandardTaskConfig struct {
	sharedLink
	Arguments          string `json:"arguments"`
	Execute            string `json:"execute"`
	FilterFileEnd      string `json:"filter_file_end"`
	FilterSubdir       string `json:"filter_subdir"`
	RequiresOutputLock bool   `json:"requires_output_lock"`
	StderrFile         string `json:"stderr_file"`
	StdoutFile         string `json:"stdout_file"`
}

type LinkTaskConfigSetUnitVariable struct {
	sharedLink
	Variable      string `json:"variable"`
	VariableValue string `json:"variable_value"`
	ChainID       string `json:"chain_id"`
}

type LinkTaskConfigUnitVariableLinkPull struct {
	sharedLink
	Variable      string `json:"variable"`
	VariableValue string `json:"variable_value"`
	ChainID       string `json:"chain_id"`
}
