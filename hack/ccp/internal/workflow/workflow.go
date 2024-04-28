package workflow

import (
	"embed"
	"encoding/json"
	"fmt"
	"os"

	"github.com/google/uuid"
	"github.com/tailscale/hujson"
)

//go:embed assets/*
var assets embed.FS

func Default() (*Document, error) {
	const name = "assets/workflow.json"
	return LoadEmbedded(name)
}

func LoadEmbedded(name string) (*Document, error) {
	blob, err := assets.ReadFile(name)
	if err != nil {
		return nil, err
	}

	doc, err := LoadFromJSON(blob)
	if err != nil {
		return nil, err
	}

	return doc, nil
}

func LoadFromFile(path string) (*Document, error) {
	blob, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	doc, err := LoadFromJSON(blob)
	if err != nil {
		return nil, err
	}

	return doc, nil
}

func LoadFromJSON(blob []byte) (*Document, error) {
	blob, err := hujson.Standardize(blob)
	if err != nil {
		return nil, err
	}

	var d Document
	if err := json.Unmarshal(blob, &d); err != nil {
		return nil, fmt.Errorf("error decoding workflow: %v", err)
	}

	return &d, nil
}

type I18nField map[string]string

func (f I18nField) String() string {
	s, ok := f["en"]
	if ok {
		return s
	}
	return ""
}

type WatchedDirectory struct {
	ChainID  uuid.UUID `json:"chain_id"`
	OnlyDirs bool      `json:"only_dirs"`
	Path     string    `json:"path"`
	UnitType string    `json:"unit_type"`
}

type Chain struct {
	ID          uuid.UUID `json:"-"`
	Description I18nField `json:"description"`
	LinkID      uuid.UUID `json:"link_id"`
	Start       bool      `json:"start"`
}

type Link struct {
	ID                uuid.UUID            `json:"-"`
	Manager           string               `json:"-"`
	Config            interface{}          `json:"config"`
	Description       I18nField            `json:"description"`
	ExitCodes         map[int]LinkExitCode `json:"exit_codes"`
	FallbackJobStatus string               `json:"fallback_job_status"`
	FallbackLinkID    uuid.UUID            `json:"fallback_link_id"`
	Group             I18nField            `json:"group"`
	End               bool                 `json:"end"`
}

type linkProxy Link

func (l *Link) UnmarshalJSON(b []byte) error {
	// First pass to retrieve model attribute.
	configModel := struct {
		Config struct {
			Manager string `json:"@manager"`
			Model   string `json:"@model"`
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

	l.Manager = configModel.Config.Manager

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
		config := LinkTaskConfigSetUnitVariable{}
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
	JobStatus string     `json:"job_status"`
	LinkID    *uuid.UUID `json:"link_id"`
}

type Document struct {
	Chains             map[uuid.UUID]*Chain `json:"chains"`
	Links              map[uuid.UUID]*Link  `json:"links"`
	WatchedDirectories []*WatchedDirectory  `json:"watched_directories"`
}

type documentProxy Document

func (d *Document) UnmarshalJSON(b []byte) error {
	dp := documentProxy{}
	if err := json.Unmarshal(b, &dp); err != nil {
		return err
	}
	*d = Document(dp)

	for id, v := range d.Chains {
		v.ID = id
	}

	for id, v := range d.Links {
		v.ID = id
	}

	return nil
}

type LinkMicroServiceChainChoice struct {
	Model   string      `json:"@model"`
	Manager string      `json:"@manager"`
	Choices []uuid.UUID `json:"chain_choices"`
}

type ConfigReplacement struct {
	ID          string            `json:"id"`
	Description I18nField         `json:"description"`
	Items       map[string]string `json:"items"`
}

type LinkMicroServiceChoiceReplacementDic struct {
	Model        string              `json:"@model"`
	Manager      string              `json:"@manager"`
	Replacements []ConfigReplacement `json:"replacements"`
}

type LinkStandardTaskConfig struct {
	Model         string `json:"@model"`
	Manager       string `json:"@manager"`
	Arguments     string `json:"arguments"`
	Execute       string `json:"execute"`
	FilterFileEnd string `json:"filter_file_end,omitempty"`
	FilterSubdir  string `json:"filter_subdir,omitempty"`
	StderrFile    string `json:"stderr_file,omitempty"`
	StdoutFile    string `json:"stdout_file,omitempty"`
}

type LinkTaskConfigSetUnitVariable struct {
	Model         string    `json:"@model"`
	Manager       string    `json:"@manager"`
	Variable      string    `json:"variable"`
	VariableValue string    `json:"variable_value"`
	LinkID        uuid.UUID `json:"chain_id"`
}

type LinkTaskConfigUnitVariableLinkPull struct {
	Model         string    `json:"@model"`
	Manager       string    `json:"@manager"`
	Variable      string    `json:"variable"`
	VariableValue string    `json:"variable_value"`
	LinkID        uuid.UUID `json:"chain_id"`
}
