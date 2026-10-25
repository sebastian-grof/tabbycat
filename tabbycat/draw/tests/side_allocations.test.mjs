import assert from 'node:assert/strict'
import { Buffer } from 'node:buffer'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { URL } from 'node:url'

// Load the browser ES module without changing the project's CommonJS config.
const source = await readFile(new URL('../templates/side_allocations.js', import.meta.url), 'utf8')
const { normalizeTeamName, createTeamComparator, saveSidePreallocation } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`)
const team = (id, shortName, rank = null, bracketOrder = null, longName = shortName) => ({ id, shortName, longName, rank, bracketOrder })
const sortedIds = (teams, mode, reverse = false) => [...teams].sort(createTeamComparator(mode, reverse, 'en')).map(team => team.id)

test('search normalizes case and combining accents and supports a single character', () => {
  assert.equal(normalizeTeamName('ŽILINA'), 'zilina')
  assert.equal(normalizeTeamName('Z\u030cilina'), 'zilina')
  assert.ok(normalizeTeamName('Univerzita Žilina').includes(normalizeTeamName('ž')))
})

test('alphabetical ordering is natural and resolves duplicate names by full name then ID', () => {
  const teams = [team(4, 'Team 10'), team(3, 'team 2', null, null, 'Zulu'), team(2, 'Team 2', null, null, 'Alpha'), team(1, 'Team 2', null, null, 'Alpha')]
  assert.deepEqual(sortedIds(teams, 'alphabetical'), [1, 2, 3, 4])
  assert.deepEqual(sortedIds(teams, 'alphabetical', true), [4, 3, 2, 1])
})

test('bracket standings keep tied ranks alphabetical and unranked teams last in both directions', () => {
  const teams = [team(4, 'Unranked'), team(3, 'Zulu', 2, 1), team(2, 'Alpha', 2, 1), team(1, 'Winner', 1, 0)]
  assert.deepEqual(sortedIds(teams, 'bracket'), [1, 2, 3, 4])
  assert.deepEqual(sortedIds(teams, 'bracket', true), [2, 3, 1, 4])
})

test('bracket reversal keeps tournament standings order inside each bracket', () => {
  const teams = [team(4, 'Zulu', 3, 1), team(2, 'Zulu', 1, 0), team(3, 'Alpha', 4, 1), team(1, 'Alpha', 2, 0)]
  assert.deepEqual(sortedIds(teams, 'bracket'), [2, 1, 4, 3])
  assert.deepEqual(sortedIds(teams, 'bracket', true), [4, 3, 2, 1])
})

test('matrix saves preserve zero and clear values and send CSRF credentials', async () => {
  for (const side of [0, 1, null]) {
    let request
    const fetcher = async (url, options) => {
      request = { url, ...options }
      return { ok: true, json: async () => ({ status: 'true', summary: { assigned: 1 } }) }
    }
    const result = await saveSidePreallocation('/sides/update/', 'csrf-test', { team_id: 2, round_id: 3, side }, fetcher)
    assert.equal(JSON.parse(request.body).side, side)
    assert.equal(request.headers['X-CSRFToken'], 'csrf-test')
    assert.equal(request.credentials, 'same-origin')
    assert.equal(result.summary.assigned, 1)
  }
})

test('matrix saves surface server rejections and network failures', async () => {
  await assert.rejects(saveSidePreallocation('/sides/update/', 'csrf', {}, async () => ({
    ok: false, json: async () => ({ status: 'false', message: 'Draw already generated' }),
  })), /Draw already generated/)
  await assert.rejects(saveSidePreallocation('/sides/update/', 'csrf', {}, async () => {
    throw new Error('offline')
  }), /offline/)
})
