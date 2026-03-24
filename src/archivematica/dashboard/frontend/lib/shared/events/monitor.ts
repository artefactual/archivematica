export const TRANSFER_STARTED_EVENT = 'archivematica:transfer-started'

export const dispatchTransferStartedEvent = (): void => {
  document.dispatchEvent(new CustomEvent(TRANSFER_STARTED_EVENT))
}
