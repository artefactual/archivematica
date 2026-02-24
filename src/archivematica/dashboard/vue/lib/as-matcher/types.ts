export type MatcherObjectPath = Readonly<{
  uuid: string
  path: string
}>

export type MatcherResourceNode = Readonly<{
  id: string | number
  title?: string | null
  identifier?: string | null
  dates?: string | null
  levelOfDescription?: string | null
  children?: MatcherResourceNode[] | null | false
}>

export type MatcherInitialMatch = Readonly<{
  resource_id: string | number
  file_uuid: string
  resource: MatcherResourceNode
}>

export type MatcherLabels = Readonly<{
  filterObjects: string
  filterResources: string
  pair: string
  pairSelectedObjects: string
  restartMatching: string
  reviewMatches: string
  objects: string
  resources: string
  pairs: string
  selectAll: string
  file: string
  level: string
  title: string
  identifier: string
  dates: string
  selectedResource: string
  targetResource: string
  noneSelected: string
  selectedObjects: string
  deleteMatch: string
  noResourceSelected: string
  noObjectsSelected: string
  duplicateMatch: string
  pairRequestFailed: string
  deleteRequestFailed: string
  noPairsYet: string
}>

export type MatcherUrls = Readonly<{
  match: string
  review: string
  reset: string | null
}>

export type MatcherBootstrapData = Readonly<{
  dipUuid: string
  objectPaths: MatcherObjectPath[]
  resourceData: MatcherResourceNode
  initialMatches: MatcherInitialMatch[]
  urls: MatcherUrls
  labels: MatcherLabels
}>

export type ResourceSortKey = 'sortPosition' | 'title' | 'identifier' | 'dates'

export type ResourceRow = {
  id: string
  resourceId: string
  depth: number
  sortPosition: number
  levelOfDescription: string
  title: string
  identifier: string
  dates: string
}

export type MatchRow = {
  localId: number
  createdOrder: number
  objectUuid: string
  objectPath: string
  resourceId: string
  resourceSortPosition: number | null
  levelOfDescription: string
  title: string
  identifier: string
  dates: string
}

export type AlertType = 'warning' | 'danger' | 'info'

export type AlertMessage = {
  id: number
  type: AlertType
  message: string
}

export type ObjectSelectionRow = {
  uuid: string
  path: string
  isPaired: boolean
  isChecked: boolean
}
