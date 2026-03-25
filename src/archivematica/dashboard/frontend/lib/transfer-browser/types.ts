export interface TransferFormData {
  name: string
  type:
    | 'standard'
    | 'zipfile'
    | 'unzipped bag'
    | 'zipped bag'
    | 'dspace'
    | 'disk image'
    | 'dataverse'
  accession: string
  accessSystemId: string
  processingConfig: string
  autoApprove: boolean
}

export interface ProcessingConfig {
  pk: string
  name: string
}

export interface TransferComponent {
  id: string
  path: string
  location: string
  uuid?: string
}

export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
  children_fetched?: boolean
  loading?: boolean
  size?: number
  modified?: string
  display_string?: string
}
