// Presentation only: rows and their enabled form controls always stay in the form.
export const normalizeTeamName = value => String(value).normalize('NFD').replace(/\p{M}/gu, '').toLocaleLowerCase()

export function createTeamComparator (mode, reverse, locale) {
  const collator = new Intl.Collator(locale, { numeric: true, sensitivity: 'base' })
  const alphabetical = (a, b) => collator.compare(a.shortName, b.shortName) || collator.compare(a.longName, b.longName) || a.id - b.id
  const direction = reverse ? -1 : 1
  return (a, b) => {
    if (mode === 'alphabetical') return direction * alphabetical(a, b)
    const key = 'bracketOrder'
    // Unranked teams stay last in either direction.
    if (a[key] === null && b[key] !== null) return 1
    if (b[key] === null && a[key] !== null) return -1
    const groupOrder = direction * ((a[key] ?? 0) - (b[key] ?? 0))
    // Only reverse the bracket order; keep the strongest teams first within it.
    return groupOrder || (a.rank ?? Infinity) - (b.rank ?? Infinity) || alphabetical(a, b)
  }
}

export function initSideAllocationNavigation (root, navigation) {
  const search = root.querySelector('#side-team-search')
  const sort = root.querySelector('#side-team-sort')
  const reverseButton = root.querySelector('[data-reverse-sort]')
  const directionLabel = root.querySelector('[data-sort-direction]')
  const gettext = window.gettext || (text => text)
  const interpolate = (text, values) => text.replace(/%\((\w+)\)s/g, (_, key) => values[key])
  const metadata = new Map(navigation.teams.map(team => [String(team.id), {
    ...team,
    searchNames: [normalizeTeamName(team.shortName), normalizeTeamName(team.longName)],
  }]))
  const tables = [...root.querySelectorAll('[data-team-table]')].map(body => ({
    body,
    rows: [...body.querySelectorAll('[data-team-id]')],
    empty: body.querySelector('[data-filter-empty]'),
    count: root.querySelector(`[data-team-count="${body.dataset.teamTable}"]`),
  }))
  let reverse = false

  const update = () => {
    const query = normalizeTeamName(search.value.trim())
    const mode = navigation.available ? sort.value : 'alphabetical'
    const comparator = createTeamComparator(mode, reverse, document.documentElement.lang || undefined)
    const labels = {
      alphabetical: reverse ? gettext('Z–A') : gettext('A–Z'),
      bracket: reverse ? gettext('Lowest bracket first') : gettext('Highest bracket first'),
    }
    directionLabel.textContent = labels[mode]
    reverseButton.setAttribute('aria-pressed', String(reverse))
    root.querySelectorAll('[data-filter-save-note]').forEach(note => { note.hidden = !query })

    tables.forEach(({ body, rows, empty, count }) => {
      body.querySelectorAll('[data-bracket-heading]').forEach(heading => heading.remove())
      rows.sort((a, b) => comparator(metadata.get(a.dataset.teamId), metadata.get(b.dataset.teamId)))
      let matching = 0
      let lastBracket
      rows.forEach(row => {
        const team = metadata.get(row.dataset.teamId)
        const visible = !query || team.searchNames.some(name => name.includes(query))
        row.hidden = !visible
        if (visible) {
          matching += 1
          if (mode === 'bracket' && team.bracketOrder !== lastBracket) {
            const heading = document.createElement('tr')
            heading.dataset.bracketHeading = ''
            const cell = document.createElement('th')
            cell.colSpan = row.cells.length
            cell.textContent = team.bracketLabel || gettext('Unranked')
            heading.appendChild(cell)
            body.appendChild(heading)
            lastBracket = team.bracketOrder
          }
        }
        const rank = row.querySelector('[data-team-rank]')
        if (rank) {
          rank.hidden = mode !== 'bracket' || team.rank === null
          rank.textContent = team.rank === null ? '' : interpolate(gettext('Rank %(rank)s'), { rank: team.rank })
        }
        body.appendChild(row)
      })
      empty.hidden = rows.length === 0 || matching !== 0
      body.appendChild(empty)
      count.textContent = interpolate(count.dataset.countLabel, { matching: matching, total: rows.length })
    })
  }

  search.addEventListener('input', update)
  sort.addEventListener('change', () => {
    reverse = false
    update()
  })
  root.querySelector('[data-apply-sort]').addEventListener('click', update)
  reverseButton.addEventListener('click', () => {
    reverse = !reverse
    update()
  })
  root.querySelectorAll('[data-clear-search]').forEach(button => button.addEventListener('click', () => {
    search.value = ''
    update()
    search.focus()
  }))
  update()
  root.querySelector('[data-team-toolbar]').hidden = false
}
