package servercmd

import (
	"errors"
	"os"
	"path/filepath"
)

var sharedDirs = []string{
	"arrange",
	"completed",
	"completed/transfers",
	"currentlyProcessing",
	"DIPbackups",
	"failed",
	"rejected",
	"sharedMicroServiceTasksConfigs",
	"sharedMicroServiceTasksConfigs/createXmlEventsAssist",
	"sharedMicroServiceTasksConfigs/generateAIP",
	"sharedMicroServiceTasksConfigs/generateAIP/bagit",
	"sharedMicroServiceTasksConfigs/processingMCPConfigs",
	"sharedMicroServiceTasksConfigs/transcoder",
	"sharedMicroServiceTasksConfigs/transcoder/defaultIcons",
	"SIPbackups",
	"tmp",
	"watchedDirectories",
	"watchedDirectories/activeTransfers",
	"watchedDirectories/activeTransfers/baggitDirectory",
	"watchedDirectories/activeTransfers/baggitZippedDirectory",
	"watchedDirectories/activeTransfers/dataverseTransfer",
	"watchedDirectories/activeTransfers/Dspace",
	"watchedDirectories/activeTransfers/maildir",
	"watchedDirectories/activeTransfers/standardTransfer",
	"watchedDirectories/activeTransfers/TRIM",
	"watchedDirectories/activeTransfers/zippedDirectory",
	"watchedDirectories/approveNormalization",
	"watchedDirectories/SIPCreation",
	"watchedDirectories/SIPCreation/completedTransfers",
	"watchedDirectories/SIPCreation/SIPsUnderConstruction",
	"watchedDirectories/storeAIP",
	"watchedDirectories/system",
	"watchedDirectories/system/autoProcessSIP",
	"watchedDirectories/system/autoRestructureForCompliance",
	"watchedDirectories/system/createAIC",
	"watchedDirectories/system/reingestAIP",
	"watchedDirectories/uploadDIP",
	"watchedDirectories/uploadedDIPs",
	"watchedDirectories/workFlowDecisions",
	"watchedDirectories/workFlowDecisions/compressionAIPDecisions",
	"watchedDirectories/workFlowDecisions/createTree",
	"watchedDirectories/workFlowDecisions/examineContentsChoice",
	"watchedDirectories/workFlowDecisions/extractPackagesChoice",
	"watchedDirectories/workFlowDecisions/metadataReminder",
	"watchedDirectories/workFlowDecisions/selectFormatIDToolIngest",
	"watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer",
	"www",
	"www/AIPsStore",
	"www/AIPsStore/transferBacklog",
	"www/AIPsStore/transferBacklog/arrange",
	"www/AIPsStore/transferBacklog/originals",
	"www/DIPsStore",
}

func createSharedDirs(path string) error {
	var errs error

	for _, item := range sharedDirs {
		err := os.MkdirAll(filepath.Join(path, item), os.FileMode(0o770))
		if err != nil {
			return errors.Join(errs, err)
		}
	}

	return errs
}
