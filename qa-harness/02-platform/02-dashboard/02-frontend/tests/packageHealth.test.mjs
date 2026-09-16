import test from 'node:test'
import assert from 'node:assert/strict'

import { annotateRequirementChanges } from '../src/utils/packageHealth.js'

function pkg(id, date, module = '08-discount', subproject = '02-website') {
  return {
    id,
    project: 'west-kowloon',
    subproject,
    module,
    date_slug: date,
  }
}

test('marks every later package for the same module as a requirement change', () => {
  const result = annotateRequirementChanges([
    pkg('change-2', '2026-07-14'),
    pkg('baseline', '2026-06-25'),
    pkg('change-1', '2026-07-07'),
  ])

  const byId = Object.fromEntries(result.map(item => [item.id, item]))
  assert.equal(byId.baseline.is_requirement_change, false)
  assert.equal(byId['change-1'].is_requirement_change, true)
  assert.equal(byId['change-1'].requirement_change_number, 1)
  assert.equal(byId['change-2'].requirement_change_number, 2)
  assert.equal(byId['change-2'].requirement_baseline_date, '2026-06-25')
})

test('does not combine matching module names from different subprojects', () => {
  const result = annotateRequirementChanges([
    pkg('website', '2026-06-25', '08-discount', '02-website'),
    pkg('box-office', '2026-07-07', '08-discount', '01-box-office'),
  ])

  assert.deepEqual(result.map(item => item.is_requirement_change), [false, false])
})

test('leaves a module with only one package as an initial package', () => {
  const [result] = annotateRequirementChanges([
    pkg('only-package', '2026-07-13', '10-SSO'),
  ])

  assert.equal(result.is_requirement_change, false)
  assert.equal(result.requirement_baseline_date, null)
})
