import test from 'node:test'
import assert from 'node:assert/strict'

import {
  DEFAULT_PROJECT_KEY,
  buildDashboardUrl,
  hasPersistedProjectChoice,
  pageKeyFromUrl,
  projectKeyFromUrlOrStorage,
} from '../src/projectContext.js'

test('project URL takes precedence over local storage', () => {
  const location = { search: '?project=standard+product' }
  const storage = { getItem: () => 'west-kowloon' }
  assert.equal(projectKeyFromUrlOrStorage(location, storage), 'standard product')
})

test('project context falls back safely when storage is unavailable', () => {
  const location = { search: '' }
  const storage = { getItem: () => { throw new Error('disabled') } }
  assert.equal(projectKeyFromUrlOrStorage(location, storage), DEFAULT_PROJECT_KEY)
  assert.equal(hasPersistedProjectChoice(location, storage), false)
})

test('page selection and URL building preserve the global project context', () => {
  const pages = { dashboard: true, performance: true }
  assert.equal(pageKeyFromUrl(pages, { search: '?page=performance' }), 'performance')
  assert.equal(pageKeyFromUrl(pages, { search: '?page=missing' }), 'dashboard')
  assert.equal(
    buildDashboardUrl('http://127.0.0.1:5174/?page=performance', 'dashboard', 'jockey club'),
    '/?project=jockey+club',
  )
})
