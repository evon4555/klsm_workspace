export const DEFAULT_PROJECT_KEY = 'west-kowloon'
export const PROJECT_STORAGE_KEY = 'qa-dashboard.activeProject'
export const DEFAULT_PAGE_KEY = 'dashboard'

export const OFFLINE_PROJECTS = [
  {
    key: DEFAULT_PROJECT_KEY,
    name: 'West Kowloon (offline project catalog)',
    kind: 'project',
    workspace: 'west-kowloon',
    zentaoProductId: null,
    zentaoExecutionId: null,
  },
]

export function pageKeyFromUrl(pageMap, location = globalThis.window?.location) {
  if (!location) return DEFAULT_PAGE_KEY
  const page = new URLSearchParams(location.search).get('page')
  return pageMap[page] ? page : DEFAULT_PAGE_KEY
}

export function projectKeyFromUrlOrStorage(
  location = globalThis.window?.location,
  storage = globalThis.window?.localStorage,
) {
  if (!location) return DEFAULT_PROJECT_KEY
  const urlProject = new URLSearchParams(location.search).get('project')
  if (urlProject) return urlProject
  try {
    return storage?.getItem(PROJECT_STORAGE_KEY) || DEFAULT_PROJECT_KEY
  } catch {
    return DEFAULT_PROJECT_KEY
  }
}

export function hasPersistedProjectChoice(
  location = globalThis.window?.location,
  storage = globalThis.window?.localStorage,
) {
  if (!location) return false
  if (new URLSearchParams(location.search).get('project')) return true
  try {
    return Boolean(storage?.getItem(PROJECT_STORAGE_KEY))
  } catch {
    return false
  }
}

export function buildDashboardUrl(currentHref, nextPageKey, nextProjectKey) {
  const url = new URL(currentHref)
  if (nextPageKey === DEFAULT_PAGE_KEY) {
    url.searchParams.delete('page')
  } else {
    url.searchParams.set('page', nextPageKey)
  }
  url.searchParams.set('project', nextProjectKey)
  return `${url.pathname}${url.search}${url.hash}`
}
