package processing

import (
	"encoding/xml"
	"fmt"
	"io"
	"strings"
)

type Choice struct {
	XMLName   xml.Name `xml:"preconfiguredChoice"`
	Comment   string   `xml:"-"`
	AppliesTo string   `xml:"appliesTo"`
	GoToChain string   `xml:"goToChain"`
}

type Choices struct {
	XMLName xml.Name `xml:"preconfiguredChoices"`
	Choices []Choice `xml:"preconfiguredChoice"`
}

func (c *Choices) UnmarshalXML(d *xml.Decoder, start xml.StartElement) error {
	var comment string
	for {
		t, err := d.Token()
		if err != nil {
			if err == io.EOF {
				break
			}
			return err
		}
		switch se := t.(type) {
		case xml.Comment:
			comment = string(se)
		case xml.StartElement:
			if se.Name.Local == "preconfiguredChoice" {
				var p Choice
				err := d.DecodeElement(&p, &se)
				if err != nil {
					return err
				}
				p.Comment = strings.TrimSpace(comment)
				c.Choices = append(c.Choices, p)
			}
		}
	}
	return nil
}

func (pc Choices) MarshalXML(e *xml.Encoder, start xml.StartElement) error {
	for _, p := range pc.Choices {
		if err := e.EncodeToken(xml.CharData("\n  ")); err != nil {
			return err
		}
		if err := e.EncodeToken(xml.Comment(fmt.Sprintf(" %s ", p.Comment))); err != nil {
			return err
		}
		if err := e.Encode(p); err != nil {
			return err
		}
	}
	return e.Flush()
}

type ProcessingConfig struct {
	XMLName xml.Name `xml:"processingMCP"`
	Choices Choices  `xml:"preconfiguredChoices"`
}

func ParseConfig(reader io.Reader) ([]Choice, error) {
	bytes, err := io.ReadAll(reader)
	if err != nil {
		return nil, err
	}

	var config ProcessingConfig
	err = xml.Unmarshal(bytes, &config)
	if err != nil {
		return nil, err
	}

	return config.Choices.Choices, nil
}
