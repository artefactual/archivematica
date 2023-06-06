package processing

import (
	"encoding/xml"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

var builtinConfigs = map[string]ProcessingConfig{
	"default":   defaultConfig,
	"automated": automatedConfig,
}

func InstallBuiltinConfigs(path string) error {
	var errs error
	for name, config := range builtinConfigs {
		path := filepath.Join(path, fmt.Sprintf("%sProcessingMCP.xml", name))
		blob, err := xml.MarshalIndent(config, "", "  ")
		if err != nil {
			errs = errors.Join(errs, fmt.Errorf("cannot encode %s: %v", path, err))
			continue
		}
		err = os.WriteFile(path, blob, os.FileMode(0o660))
		if err != nil {
			errs = errors.Join(errs, fmt.Errorf("cannot write %s: %v", path, err))
			continue
		}
	}
	return errs
}

var defaultConfig = ProcessingConfig{
	Choices: Choices{
		Choices: []Choice{
			{
				Comment:   "Select compression level",
				AppliesTo: "01c651cb-c174-4ba4-b985-1d87a44d6754",
				GoToChain: "414da421-b83f-4648-895f-a34840e3c3f5",
			},
			{
				Comment:   "Perform file format identification (Submission documentation & metadata)",
				AppliesTo: "087d27be-c719-47d8-9bbb-9a7d8b609c44",
				GoToChain: "4dec164b-79b0-4459-8505-8095af9655b5",
			},
			{
				Comment:   "Bind PIDs",
				AppliesTo: "a2ba5278-459a-4638-92d9-38eb1588717d",
				GoToChain: "44a7c397-8187-4fd2-b8f7-c61737c4df49",
			},
			{
				Comment:   "Generate transfer structure report",
				AppliesTo: "56eebd45-5600-4768-a8c2-ec0114555a3d",
				GoToChain: "df54fec1-dae1-4ea6-8d17-a839ee7ac4a7",
			},
			{
				Comment:   "Perform policy checks on originals",
				AppliesTo: "70fc7040-d4fb-4d19-a0e6-792387ca1006",
				GoToChain: "3e891cc4-39d2-4989-a001-5107a009a223",
			},
			{
				Comment:   "Generate thumbnails",
				AppliesTo: "498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
				GoToChain: "c318b224-b718-4535-a911-494b1af6ff26",
			},
			{
				Comment:   "Select compression algorithm",
				AppliesTo: "01d64f58-8295-4b7b-9cab-8f1b153a504f",
				GoToChain: "9475447c-9889-430c-9477-6287a9574c5b",
			},
			{
				Comment:   "Perform policy checks on access derivatives",
				AppliesTo: "8ce07e94-6130-4987-96f0-2399ad45c5c2",
				GoToChain: "76befd52-14c3-44f9-838f-15a4e01624b0",
			},
			{
				Comment:   "Perform file format identification (Ingest)",
				AppliesTo: "7a024896-c4f7-4808-a240-44c87c762bc5",
				GoToChain: "3c1faec7-7e1e-4cdd-b3bd-e2f05f4baa9b",
			},
			{
				Comment:   "Perform policy checks on preservation derivatives",
				AppliesTo: "153c5f41-3cfb-47ba-9150-2dd44ebc27df",
				GoToChain: "b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546",
			},
			{
				Comment:   "Assign UUIDs to directories",
				AppliesTo: "bd899573-694e-4d33-8c9b-df0af802437d",
				GoToChain: "891f60d0-1ba8-48d3-b39e-dd0934635d29",
			},
			{
				Comment:   "Document empty directories",
				AppliesTo: "d0dfa5fc-e3c2-4638-9eda-f96eea1070e0",
				GoToChain: "65273f18-5b4e-4944-af4f-09be175a88e8",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "856d2d65-cd25-49fa-8da9-cabb78292894",
				GoToChain: "6e431096-c403-4cbf-a59a-a26e86be54a8",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "1dad74a2-95df-4825-bbba-dca8b91d2371",
				GoToChain: "1ac7d792-b63f-46e0-9945-d48d9e5c02c9",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "7e81f94e-6441-4430-a12d-76df09181b66",
				GoToChain: "97be337c-ff27-4869-bf63-ef1abc9df15d",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "390d6507-5029-4dae-bcd4-ce7178c9b560",
				GoToChain: "34944d4f-762e-4262-8c79-b9fd48521ca0",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
				GoToChain: "3e8c0c39-3f30-4c9b-a449-85eef1b2a458",
			},
		},
	},
}

var automatedConfig = ProcessingConfig{
	Choices: Choices{
		Choices: []Choice{
			{
				Comment:   "Store DIP",
				AppliesTo: "5e58066d-e113-4383-b20b-f301ed4d751c",
				GoToChain: "8d29eb3d-a8a8-4347-806e-3d8227ed44a1",
			},
			{
				Comment:   "Select compression level",
				AppliesTo: "01c651cb-c174-4ba4-b985-1d87a44d6754",
				GoToChain: "414da421-b83f-4648-895f-a34840e3c3f5",
			},
			{
				Comment:   "Examine contents",
				AppliesTo: "accea2bf-ba74-4a3a-bb97-614775c74459",
				GoToChain: "e0a39199-c62a-4a2f-98de-e9d1116460a8",
			},
			{
				Comment:   "Perform file format identification (Submission documentation & metadata)",
				AppliesTo: "087d27be-c719-47d8-9bbb-9a7d8b609c44",
				GoToChain: "4dec164b-79b0-4459-8505-8095af9655b5",
			},
			{
				Comment:   `Normalize (match 1 for "Normalize for preservation")`,
				AppliesTo: "cb8e5706-e73f-472f-ad9b-d1236af8095f",
				GoToChain: "612e3609-ce9a-4df6-a9a3-63d634d2d934",
			},
			{
				Comment:   `Normalize (match 2 for "Normalize for preservation")`,
				AppliesTo: "7509e7dc-1e1b-4dce-8d21-e130515fce73",
				GoToChain: "612e3609-ce9a-4df6-a9a3-63d634d2d934",
			},
			{
				Comment:   "Bind PIDs",
				AppliesTo: "a2ba5278-459a-4638-92d9-38eb1588717d",
				GoToChain: "44a7c397-8187-4fd2-b8f7-c61737c4df49",
			},
			{
				Comment:   "Create SIP(s)",
				AppliesTo: "bb194013-597c-4e4a-8493-b36d190f8717",
				GoToChain: "61cfa825-120e-4b17-83e6-51a42b67d969",
			},
			{
				Comment:   "Delete packages after extraction",
				AppliesTo: "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
				GoToChain: "85b1e45d-8f98-4cae-8336-72f40e12cbef",
			},
			{
				Comment:   "Transcribe files (OCR)",
				AppliesTo: "82ee9ad2-2c74-4c7c-853e-e4eaf68fc8b6",
				GoToChain: "0a24787c-00e3-4710-b324-90e792bfb484",
			},
			{
				Comment:   "Perform file format identification (Transfer)",
				AppliesTo: "f09847c2-ee51-429a-9478-a860477f6b8d",
				GoToChain: "d97297c7-2b49-4cfe-8c9f-0613d63ed763",
			},
			{
				Comment:   "Store DIP location",
				AppliesTo: "cd844b6e-ab3c-4bc6-b34f-7103f88715de",
				GoToChain: "/api/v2/location/default/DS/",
			},
			{
				Comment:   "Generate transfer structure report",
				AppliesTo: "56eebd45-5600-4768-a8c2-ec0114555a3d",
				GoToChain: "e9eaef1e-c2e0-4e3b-b942-bfb537162795",
			},
			{
				Comment:   "Perform policy checks on originals",
				AppliesTo: "70fc7040-d4fb-4d19-a0e6-792387ca1006",
				GoToChain: "3e891cc4-39d2-4989-a001-5107a009a223",
			},
			{
				Comment:   "Reminder: add metadata if desired",
				AppliesTo: "eeb23509-57e2-4529-8857-9d62525db048",
				GoToChain: "5727faac-88af-40e8-8c10-268644b0142d",
			},
			{
				Comment:   "Generate thumbnails",
				AppliesTo: "498f7a6d-1b8c-431a-aa5d-83f14f3c5e65",
				GoToChain: "972fce6c-52c8-4c00-99b9-d6814e377974",
			},
			{
				Comment:   "Select compression algorithm",
				AppliesTo: "01d64f58-8295-4b7b-9cab-8f1b153a504f",
				GoToChain: "9475447c-9889-430c-9477-6287a9574c5b",
			},
			{
				Comment:   "Store AIP",
				AppliesTo: "2d32235c-02d4-4686-88a6-96f4d6c7b1c3",
				GoToChain: "9efab23c-31dc-4cbd-a39d-bb1665460cbe",
			},
			{
				Comment:   "Perform policy checks on access derivatives",
				AppliesTo: "8ce07e94-6130-4987-96f0-2399ad45c5c2",
				GoToChain: "76befd52-14c3-44f9-838f-15a4e01624b0",
			},
			{
				Comment:   "Perform file format identification (Ingest)",
				AppliesTo: "7a024896-c4f7-4808-a240-44c87c762bc5",
				GoToChain: "5b3c8268-5b33-4b70-b1aa-0e4540fe03d1",
			},
			{
				Comment:   "Perform policy checks on preservation derivatives",
				AppliesTo: "153c5f41-3cfb-47ba-9150-2dd44ebc27df",
				GoToChain: "b7ce05f0-9d94-4b3e-86cc-d4b2c6dba546",
			},
			{
				Comment:   "Assign UUIDs to directories",
				AppliesTo: "bd899573-694e-4d33-8c9b-df0af802437d",
				GoToChain: "2dc3f487-e4b0-4e07-a4b3-6216ed24ca14",
			},
			{
				Comment:   "Store AIP location",
				AppliesTo: "b320ce81-9982-408a-9502-097d0daa48fa",
				GoToChain: "/api/v2/location/default/AS/",
			},
			{
				Comment:   "Document empty directories",
				AppliesTo: "d0dfa5fc-e3c2-4638-9eda-f96eea1070e0",
				GoToChain: "65273f18-5b4e-4944-af4f-09be175a88e8",
			},
			{
				Comment:   "Extract packages",
				AppliesTo: "dec97e3c-5598-4b99-b26e-f87a435a6b7f",
				GoToChain: "01d80b27-4ad1-4bd1-8f8d-f819f18bf685",
			},
			{
				Comment:   "Approve normalization",
				AppliesTo: "de909a42-c5b5-46e1-9985-c031b50e9d30",
				GoToChain: "1e0df175-d56d-450d-8bee-7df1dc7ae815",
			},
			{
				Comment:   "Upload DIP",
				AppliesTo: "92879a29-45bf-4f0b-ac43-e64474f0f2f9",
				GoToChain: "6eb8ebe7-fab3-4e4c-b9d7-14de17625baa",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "856d2d65-cd25-49fa-8da9-cabb78292894",
				GoToChain: "6e431096-c403-4cbf-a59a-a26e86be54a8",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "1dad74a2-95df-4825-bbba-dca8b91d2371",
				GoToChain: "1ac7d792-b63f-46e0-9945-d48d9e5c02c9",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "7e81f94e-6441-4430-a12d-76df09181b66",
				GoToChain: "97be337c-ff27-4869-bf63-ef1abc9df15d",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "390d6507-5029-4dae-bcd4-ce7178c9b560",
				GoToChain: "34944d4f-762e-4262-8c79-b9fd48521ca0",
			},
			{
				Comment:   "Virus scanning: Yes",
				AppliesTo: "97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
				GoToChain: "3e8c0c39-3f30-4c9b-a449-85eef1b2a458",
			},
		},
	},
}
