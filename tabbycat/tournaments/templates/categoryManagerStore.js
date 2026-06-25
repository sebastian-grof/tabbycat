import { defineStore } from 'pinia'

// New folders are given decreasing negative ids until they are saved and the
// server hands back their real primary keys.
let tempIdCounter = -1

function bySeq (a, b) {
  if (a.seq !== b.seq) {
    return a.seq - b.seq
  }
  return (a.name || '').localeCompare(b.name || '')
}

export const useCategoryManagerStore = defineStore('categoryManager', {
  state: () => ({
    folders: {}, // keyed by id (negative ids are unsaved)
    tournaments: {}, // keyed by id
    expanded: {}, // folderId -> bool (UI only, default expanded)
    query: '', // live search/filter text (UI only)
    dirty: false,
    saving: false,
    snapshot: null, // JSON string of the last-saved state, used by discard()
  }),
  getters: {
    childFolders: (state) => (parentId) => Object.values(state.folders)
      .filter((folder) => folder.parentId === parentId).sort(bySeq),
    folderTournaments: (state) => (categoryId) => Object.values(state.tournaments)
      .filter((tournament) => tournament.categoryId === categoryId).sort(bySeq),
    isExpanded: (state) => (id) => state.expanded[id] !== false,
    descendantIds: (state) => (id) => {
      const result = []
      const walk = (parentId) => {
        Object.values(state.folders).forEach((folder) => {
          if (folder.parentId === parentId) {
            result.push(folder.id)
            walk(folder.id)
          }
        })
      }
      walk(id)
      return result
    },
    folderCount: (state) => Object.keys(state.folders).length,
    uncategorisedCount: (state) => Object.values(state.tournaments)
      .filter((tournament) => tournament.categoryId === null).length,

    // ---- search / filtering ----
    normalisedQuery: (state) => state.query.trim().toLowerCase(),
    matchesText () {
      return (text) => {
        const q = this.normalisedQuery
        if (!q) return true
        return (text || '').toLowerCase().includes(q)
      }
    },
    // A tournament is visible if there is no query or its name matches.
    tournamentVisible () {
      return (tournament) => !this.normalisedQuery || this.matchesText(tournament.name)
    },
    // A folder is visible if it matches, or any descendant folder/tournament matches.
    folderVisible () {
      const visible = (folder) => {
        if (!this.normalisedQuery) return true
        if (this.matchesText(folder.name)) return true
        if (this.folderTournaments(folder.id).some((t) => this.matchesText(t.name))) return true
        return this.childFolders(folder.id).some((child) => visible(child))
      }
      return visible
    },
  },
  actions: {
    init ({ categories, tournaments }) {
      const folders = {}
      categories.forEach((category) => { folders[category.id] = { ...category } })
      const tours = {}
      tournaments.forEach((tournament) => { tours[tournament.id] = { ...tournament } })
      this.folders = folders
      this.tournaments = tours
      this.dirty = false
      this.snapshot = JSON.stringify({ folders, tournaments: tours })
    },
    markDirty () {
      this.dirty = true
    },
    setQuery (value) {
      this.query = value
    },
    toggleExpanded (id) {
      this.expanded[id] = !this.isExpanded(id)
    },
    expandAll () {
      Object.keys(this.folders).forEach((id) => { this.expanded[id] = true })
    },
    collapseAll () {
      Object.keys(this.folders).forEach((id) => { this.expanded[id] = false })
    },
    nextFolderSeq (parentId) {
      return this.childFolders(parentId).reduce((max, folder) => Math.max(max, folder.seq), -1) + 1
    },
    nextTournamentSeq (categoryId) {
      return this.folderTournaments(categoryId).reduce((max, t) => Math.max(max, t.seq), -1) + 1
    },
    createFolder (parentId, defaultName) {
      const id = tempIdCounter--
      this.folders[id] = {
        id,
        name: defaultName,
        slug: '',
        description: '',
        active: true,
        public: true,
        parentId: parentId,
        seq: this.nextFolderSeq(parentId),
      }
      if (parentId !== null) {
        this.expanded[parentId] = true
      }
      this.markDirty()
      return id
    },
    renameFolder (id, name) {
      this.folders[id].name = name
      this.markDirty()
    },
    updateFolderField (id, field, value) {
      this.folders[id][field] = value
      this.markDirty()
    },
    deleteFolder (id) {
      const parentId = this.folders[id].parentId
      // Don't lose anything: child folders and tournaments bubble up a level.
      this.childFolders(id).forEach((child) => { child.parentId = parentId })
      this.folderTournaments(id).forEach((tournament) => { tournament.categoryId = parentId })
      delete this.folders[id]
      delete this.expanded[id]
      this.markDirty()
    },
    moveFolderInto (id, parentId) {
      if (id === parentId) {
        return false
      }
      if (parentId !== null && this.descendantIds(id).includes(parentId)) {
        return false // would create a cycle
      }
      const folder = this.folders[id]
      if (folder.parentId === parentId) {
        return false
      }
      folder.parentId = parentId
      folder.seq = this.childFolders(parentId).filter((f) => f.id !== id).length
      if (parentId !== null) {
        this.expanded[parentId] = true
      }
      this.markDirty()
      return true
    },
    moveTournamentInto (id, categoryId) {
      const tournament = this.tournaments[id]
      if (tournament.categoryId === categoryId) {
        return false
      }
      tournament.categoryId = categoryId
      tournament.seq = this.folderTournaments(categoryId).filter((t) => t.id !== id).length
      if (categoryId !== null) {
        this.expanded[categoryId] = true
      }
      this.markDirty()
      return true
    },
    handleDrop (payload, targetParentId) {
      if (!payload || typeof payload.id === 'undefined') {
        return false
      }
      if (payload.type === 'folder') {
        return this.moveFolderInto(payload.id, targetParentId)
      }
      if (payload.type === 'tournament') {
        return this.moveTournamentInto(payload.id, targetParentId)
      }
      return false
    },
    reorderFolder (id, direction) {
      const folder = this.folders[id]
      const ordered = this.childFolders(folder.parentId).map((f) => f.id)
      const index = ordered.indexOf(id)
      const swap = direction === 'up' ? index - 1 : index + 1
      if (swap < 0 || swap >= ordered.length) {
        return
      }
      ;[ordered[index], ordered[swap]] = [ordered[swap], ordered[index]]
      ordered.forEach((fid, i) => { this.folders[fid].seq = i })
      this.markDirty()
    },
    reorderTournament (id, direction) {
      const tournament = this.tournaments[id]
      const ordered = this.folderTournaments(tournament.categoryId).map((t) => t.id)
      const index = ordered.indexOf(id)
      const swap = direction === 'up' ? index - 1 : index + 1
      if (swap < 0 || swap >= ordered.length) {
        return
      }
      ;[ordered[index], ordered[swap]] = [ordered[swap], ordered[index]]
      ordered.forEach((tid, i) => { this.tournaments[tid].seq = i })
      this.markDirty()
    },
    buildPayload () {
      return {
        folders: Object.values(this.folders).map((folder) => ({
          id: folder.id,
          name: folder.name,
          slug: folder.slug || '',
          description: folder.description || '',
          active: !!folder.active,
          public: !!folder.public,
          parentId: folder.parentId === undefined ? null : folder.parentId,
          seq: folder.seq || 0,
        })),
        tournaments: Object.values(this.tournaments).map((tournament) => ({
          id: tournament.id,
          categoryId: tournament.categoryId === undefined ? null : tournament.categoryId,
          seq: tournament.seq || 0,
        })),
      }
    },
    applyResult ({ idMap, categories, tournaments }) {
      // Re-key the UI's expand state from temporary ids to the saved ids, then
      // adopt the server's authoritative tree.
      const map = {}
      Object.keys(idMap || {}).forEach((key) => { map[Number(key)] = idMap[key] })
      const newExpanded = {}
      Object.keys(this.expanded).forEach((key) => {
        const realId = map[Number(key)] || Number(key)
        newExpanded[realId] = this.expanded[key]
      })
      this.init({ categories, tournaments })
      this.expanded = newExpanded
    },
    discard () {
      const { folders, tournaments } = JSON.parse(this.snapshot)
      this.folders = folders
      this.tournaments = tournaments
      this.dirty = false
    },
  },
})
