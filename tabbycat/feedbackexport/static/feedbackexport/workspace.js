/* Durable exports: the browser observes jobs; it never drives their delivery. */
(() => {
  'use strict'
  const start = document.getElementById('export-start')
  const requestJSON = async (url, options = {}) => {
    const response = await fetch(url, { credentials: 'same-origin', ...options })
    let data
    try { data = await response.json() } catch (_) { throw new Error(`HTTP ${response.status}`) }
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`)
    return data
  }
  if (start) {
    const rows = [...start.querySelectorAll('[data-tournament-row]')]
    const search = document.getElementById('tournament-search')
    const filter = document.getElementById('tournament-filter')
    const button = document.getElementById('start-export')
    let submitting = false
    const update = () => {
      let matching = 0
      let selected = 0
      let feedback = 0
      const kind = start.querySelector('[name=kind]:checked').value
      rows.forEach(row => {
        const visible = row.dataset.search.includes(search.value.trim().toLowerCase()) &&
          (filter.value === 'all' || filter.value === row.dataset.active)
        row.hidden = !visible
        if (visible) matching++
        const checkbox = row.querySelector('[name=tournaments]')
        if (checkbox.checked) { selected++; feedback += Number(checkbox.dataset.feedbackCount) }
      })
      document.getElementById('selected-count').textContent = selected
      document.getElementById('selected-feedback').textContent = kind === 'activity' ? '0' : feedback
      document.getElementById('selected-activity').textContent = kind === 'feedback' ? '0' : selected
      document.getElementById('matching-count').textContent = `${matching} / ${rows.length}`
      document.getElementById('no-matches').hidden = matching !== 0
      if (button) button.disabled = submitting || selected === 0
    }
    start.addEventListener('change', update)
    search.addEventListener('input', update)
    document.getElementById('select-matching').addEventListener('click', () => {
      rows.filter(row => !row.hidden).forEach(row => {
        const checkbox = row.querySelector('[name=tournaments]')
        if (!checkbox.disabled) checkbox.checked = true
      })
      update()
    })
    document.getElementById('clear-selection').addEventListener('click', () => {
      rows.forEach(row => { row.querySelector('[name=tournaments]').checked = false })
      update()
    })
    start.addEventListener('submit', async event => {
      event.preventDefault()
      if (submitting) return
      submitting = true
      update()
      const error = document.getElementById('start-error')
      error.hidden = true
      try {
        const data = await requestJSON(start.action, { method: 'POST', body: new FormData(start), headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        window.location.assign(data.url)
      } catch (reason) {
        error.textContent = reason.message
        error.hidden = false
        submitting = false
        update()
      }
    })
    update()
  }

  const job = document.getElementById('export-job')
  if (!job) return
  let terminal = ['completed', 'completed_errors'].includes(job.dataset.status)
  let delay = 2000
  let timer
  let fetching = false
  let failedPoll = false
  const error = document.getElementById('job-error')
  const statusOptions = [...document.getElementById('item-status').options]
  const statusLabels = Object.fromEntries(statusOptions.map(option => [option.value, option.textContent]))
  const date = value => value ? new Date(value).toLocaleString() : '—'
  const updateSummary = data => {
    terminal = data.terminal
    const statusLabel = document.getElementById('job-status')
    if (statusLabel.textContent !== data.status_label) statusLabel.textContent = data.status_label
    document.getElementById('job-progress').value = data.percent
    document.getElementById('preparation-note').hidden = data.preparation_done
    job.querySelectorAll('[data-count]').forEach(element => {
      element.textContent = element.dataset.count === 'total' ? data.total : (data.counts[element.dataset.count] || 0)
    })
    document.getElementById('last-progress').textContent = date(data.last_progress_at)
    document.getElementById('next-retry').textContent = date(data.next_attempt_at)
    const blocked = document.getElementById('blocked-reasons')
    blocked.replaceChildren()
    Object.entries(data.blocked_types).forEach(([kind, reason]) => {
      const line = document.createElement('p')
      line.className = 'exports-notice'
      line.textContent = `${document.getElementById('job-items').dataset[kind]}: ${reason}`
      blocked.append(line)
    })
    job.querySelectorAll('[data-control]').forEach(form => {
      form.hidden = form.dataset.control === 'pause' ? terminal || data.status === 'paused'
        : form.dataset.control === 'resume' ? !['paused', 'blocked'].includes(data.status)
          : data.status !== 'completed_errors'
    })
    if (data.health) {
      document.getElementById('worker-health').classList.toggle('is-ready', data.health.worker_online)
      document.getElementById('worker-label').textContent = data.health.worker_online ? job.dataset.onlineLabel : job.dataset.offlineLabel
      document.getElementById('worker-warning').hidden = data.health.worker_online
    }
  }
  const updateItems = data => {
    const body = document.getElementById('job-items')
    // Do not replace a keyboard user's focused control during a poll.
    if (body.contains(document.activeElement)) return
    // Keep an expanded diagnostic readable while polling other progress.
    const expanded = new Set([...body.querySelectorAll('details[open]')].map(detail => detail.dataset.item))
    body.replaceChildren()
    data.items.forEach(item => {
      const row = document.createElement('tr')
      const cells = Array.from({ length: 5 }, () => document.createElement('td'))
      cells[0].textContent = item.label || `#${item.source_id}`
      cells[1].textContent = body.dataset[item.kind]
      const badge = document.createElement('span')
      badge.className = 'exports-badge'
      badge.dataset.state = item.status
      badge.textContent = statusLabels[item.status] || item.status
      cells[2].append(badge)
      cells[3].textContent = item.attempts
      if (item.last_error || Object.keys(item.receipt).length) {
        const details = document.createElement('details')
        details.dataset.item = String(item.id)
        details.open = expanded.has(String(item.id))
        const summary = document.createElement('summary')
        summary.textContent = body.dataset.details + (item.http_status ? ` · HTTP ${item.http_status}` : '')
        const message = document.createElement('p')
        message.textContent = item.last_error
        details.append(summary, message)
        Object.entries(item.receipt).forEach(([key, value]) => {
          const line = document.createElement('div')
          line.textContent = `${key}: ${value}`
          details.append(line)
        })
        cells[4].append(details)
      } else cells[4].textContent = '—'
      row.append(...cells)
      body.append(row)
    })
    if (!data.items.length) {
      const row = document.createElement('tr')
      const cell = document.createElement('td')
      cell.colSpan = 5
      cell.className = 'exports-empty'
      cell.textContent = body.dataset.empty
      row.append(cell)
      body.append(row)
    }
    document.getElementById('items-page').textContent = `${data.page} / ${data.pages}`
    for (const [direction, number] of [['previous', data.page - 1], ['next', data.page + 1]]) {
      const link = document.getElementById(`items-${direction}`)
      link.hidden = number < 1 || number > data.pages
      const query = new URLSearchParams(window.location.search)
      query.set('page', number)
      link.href = `?${query}`
    }
  }
  const schedule = () => {
    clearTimeout(timer)
    if ((!terminal || failedPoll) && !document.hidden) timer = setTimeout(poll, delay)
  }
  const poll = async () => {
    if (fetching || document.hidden) return
    fetching = true
    try {
      const [summary, items] = await Promise.all([
        requestJSON(job.dataset.statusUrl),
        requestJSON(job.dataset.itemsUrl + window.location.search)
      ])
      updateSummary(summary)
      updateItems(items)
      error.hidden = true
      failedPoll = false
      delay = ['paused', 'blocked'].includes(summary.status) ? 10000 : 2000
    } catch (_) {
      failedPoll = true
      error.textContent = job.dataset.reconnecting
      error.hidden = false
      delay = Math.min(delay * 2, 30000)
    } finally { fetching = false; schedule() }
  }
  job.querySelectorAll('[data-control]').forEach(form => {
    form.addEventListener('submit', async event => {
      event.preventDefault()
      const button = form.querySelector('button')
      button.disabled = true
      try {
        const data = await requestJSON(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        updateSummary(data)
        error.hidden = true
        delay = 2000
        await poll()
      } catch (reason) { error.textContent = reason.message; error.hidden = false }
      finally { button.disabled = false }
    })
  })
  document.addEventListener('visibilitychange', () => {
    clearTimeout(timer)
    if (!document.hidden) poll()
  })
  poll()
})()
