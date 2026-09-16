function packageGroupKey(pkg) {
  return [pkg.project || '', pkg.subproject || '', pkg.module || ''].join('\u0000')
}

function comparePackageTime(left, right) {
  const dateOrder = String(left.date_slug || '').localeCompare(String(right.date_slug || ''))
  if (dateOrder !== 0) return dateOrder
  return String(left.id || '').localeCompare(String(right.id || ''))
}

/**
 * Mark later date packages for the same project/subproject/module as
 * requirement changes. The earliest package stays the unlabelled baseline.
 */
export function annotateRequirementChanges(packages = []) {
  const groups = new Map()

  for (const pkg of packages) {
    const key = packageGroupKey(pkg)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(pkg)
  }

  const changeInfoById = new Map()
  for (const group of groups.values()) {
    if (group.length < 2) continue
    const ordered = [...group].sort(comparePackageTime)
    const baselineDate = ordered[0].date_slug
    ordered.slice(1).forEach((pkg, index) => {
      changeInfoById.set(pkg.id, {
        is_requirement_change: true,
        requirement_change_number: index + 1,
        requirement_baseline_date: baselineDate,
      })
    })
  }

  return packages.map(pkg => ({
    ...pkg,
    is_requirement_change: false,
    requirement_change_number: null,
    requirement_baseline_date: null,
    ...(changeInfoById.get(pkg.id) || {}),
  }))
}
