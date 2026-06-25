<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useAjax } from '../../templates/composables/useAjax.js'
import { useDjangoI18n } from '../../templates/composables/useDjangoI18n.js'
import { useCategoryManagerStore } from './categoryManagerStore.js'
import CategoryFolder from './CategoryFolder.vue'
import CategoryTournament from './CategoryTournament.vue'

const props = defineProps({
  initialData: { type: Object, required: true },
  saveUrl: { type: String, required: true },
})

const store = useCategoryManagerStore()
const { gettext } = useDjangoI18n()
const { ajaxSave } = useAjax()

store.init(props.initialData)

const rootFolders = computed(() => store.childFolders(null).filter((f) => store.folderVisible(f)))
const rootTournaments = computed(() => store.folderTournaments(null).filter((t) => store.tournamentVisible(t)))

const hasQuery = computed(() => store.normalisedQuery.length > 0)
const noResults = computed(() => hasQuery.value && rootFolders.value.length === 0 && rootTournaments.value.length === 0)

const newTopFolder = () => {
  store.createFolder(null, gettext('New folder'))
}

const onRootDrop = (event) => {
  let payload
  try {
    payload = JSON.parse(event.dataTransfer.getData('text'))
  } catch (error) {
    return
  }
  store.handleDrop(payload, null)
}

const save = () => {
  if (!store.dirty || store.saving) {
    return
  }
  store.saving = true
  ajaxSave(
    props.saveUrl,
    store.buildPayload(),
    'category layout',
    (response) => {
      store.applyResult(response)
      store.saving = false
    },
    () => {
      store.saving = false
    },
    null,
    true,
  )
}

const discard = () => {
  if (!store.dirty || store.saving) {
    return
  }
  if (window.confirm(gettext('Discard all unsaved changes?'))) {
    store.discard()
  }
}

const beforeUnloadHandler = (event) => {
  if (store.dirty) {
    event.preventDefault()
    event.returnValue = ''
  }
}

onMounted(() => window.addEventListener('beforeunload', beforeUnloadHandler))
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnloadHandler))
</script>

<template>
  <div class="cm-manager">
    <!-- Toolbar -->
    <div class="cm-toolbar">
      <button type="button" class="cm-btn cm-btn-outline" @click="newTopFolder">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
        {{ gettext('New folder') }}
      </button>
      <button type="button" class="cm-btn cm-btn-primary" :disabled="!store.dirty || store.saving" @click="save">
        <template v-if="store.saving">
          <svg class="cm-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.2-8.5" /></svg>
          {{ gettext('Saving…') }}
        </template>
        <template v-else>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" /><polyline points="17 21 17 13 7 13 7 21" /><polyline points="7 3 7 8 15 8" /></svg>
          {{ gettext('Save layout') }}
        </template>
      </button>
      <button type="button" class="cm-btn cm-btn-ghost" :disabled="!store.dirty || store.saving" @click="discard">
        {{ gettext('Discard changes') }}
      </button>
      <span v-if="store.dirty" class="cm-dirty">
        <span class="cm-dot"></span> {{ gettext('Unsaved changes') }}
      </span>

      <div class="cm-tool-right">
        <div class="cm-search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          <input type="text" :placeholder="gettext('Search folders & tournaments')"
                 :value="store.query" @input="store.setQuery($event.target.value)">
          <button v-if="hasQuery" type="button" class="cm-clear" :title="gettext('Clear')" @click="store.setQuery('')">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>
        <button type="button" class="cm-iconbtn-lg" :title="gettext('Expand all')" @click="store.expandAll()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="7 13 12 18 17 13" /><polyline points="7 6 12 11 17 6" /></svg>
        </button>
        <button type="button" class="cm-iconbtn-lg" :title="gettext('Collapse all')" @click="store.collapseAll()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="17 11 12 6 7 11" /><polyline points="17 18 12 13 7 18" /></svg>
        </button>
      </div>
    </div>

    <!-- Tree -->
    <div class="cm-tree card">
      <div class="cm-section-label">{{ gettext('Uncategorised tournaments') }}</div>
      <p class="cm-help">
        {{ gettext('Tournaments here appear directly on the homepage. Drop one onto a folder to file it away.') }}
      </p>
      <div class="cm-droproot" @dragover.prevent @drop.prevent="onRootDrop">
        <CategoryTournament v-for="tournament in rootTournaments" :key="'t' + tournament.id" :tournament="tournament" />
        <p v-if="store.folderTournaments(null).length === 0 && !hasQuery" class="cm-empty cm-empty-pad">
          {{ gettext('Every tournament is filed into a folder.') }}
        </p>
      </div>

      <div class="cm-divider"></div>

      <div class="cm-section-label">{{ gettext('Folders') }}</div>
      <div class="cm-droproot" @dragover.prevent @drop.prevent="onRootDrop">
        <CategoryFolder v-for="folder in rootFolders" :key="'f' + folder.id" :folder="folder" :depth="0" />
        <p v-if="store.childFolders(null).length === 0 && !hasQuery" class="cm-empty cm-empty-pad">
          {{ gettext('No folders yet. Click “New folder” to create one.') }}
        </p>
      </div>

      <div v-if="noResults" class="cm-noresults">
        {{ gettext('No folders or tournaments match your search.') }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.cm-manager {
  --cm-accent: #663da0;
}

/* Toolbar */
.cm-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.cm-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 15px;
  border-radius: 9px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: filter .12s, background .12s;
}
.cm-btn svg { width: 16px; height: 16px; }
.cm-btn-primary { background: var(--cm-accent); color: #fff; }
.cm-btn-primary:hover { filter: brightness(1.07); }
.cm-btn-outline { background: #fff; border-color: #dcd5ea; color: var(--cm-accent); }
.cm-btn-outline:hover { background: #f4f0fb; }
.cm-btn-ghost { background: transparent; color: #6b7178; }
.cm-btn-ghost:hover { background: #eef0f2; }
.cm-btn:disabled { opacity: .42; cursor: default; filter: none; }
.cm-dirty {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  color: #cf6a1e;
  font-weight: 600;
}
.cm-dirty .cm-dot { width: 8px; height: 8px; border-radius: 50%; background: #fd681d; }

.cm-tool-right { margin-left: auto; display: flex; align-items: center; gap: 8px; }
.cm-search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e2def0;
  border-radius: 9px;
  padding: 8px 11px;
  min-width: 230px;
  transition: box-shadow .12s, border-color .12s;
}
.cm-search:focus-within { border-color: var(--cm-accent); box-shadow: 0 0 0 3px rgba(102, 61, 160, .15); }
.cm-search input { border: none; outline: none; font: inherit; font-size: 13.5px; background: transparent; flex: 1 1 auto; width: 100%; }
.cm-search > svg { color: #9aa0a8; flex: 0 0 16px; width: 16px; height: 16px; }
.cm-clear { border: none; background: transparent; color: #b3b8bf; cursor: pointer; display: inline-flex; padding: 2px; border-radius: 5px; }
.cm-clear:hover { color: #6b7178; background: #f0f0f3; }
.cm-iconbtn-lg {
  width: 38px;
  height: 38px;
  border: 1px solid #e2def0;
  background: #fff;
  border-radius: 9px;
  color: #6b7178;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.cm-iconbtn-lg svg { width: 18px; height: 18px; }
.cm-iconbtn-lg:hover { background: #f4f0fb; color: var(--cm-accent); border-color: #dcd5ea; }

/* Spinner */
.cm-spin { animation: cm-spin .7s linear infinite; }
@keyframes cm-spin { to { transform: rotate(360deg); } }

/* Tree */
.cm-tree { padding: 8px 10px 14px; min-height: 8rem; }
.cm-section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .07em;
  text-transform: uppercase;
  color: #9aa0a8;
  padding: 10px 10px 6px;
}
.cm-help { margin: 0 0 6px; padding: 0 10px; color: #9aa0a8; font-size: 13px; }
.cm-divider { height: 1px; background: #eeecf2; margin: 12px 6px; }
.cm-droproot { border-radius: 10px; }
.cm-empty { font-style: italic; color: #aab0b8; font-size: 13px; }
.cm-empty-pad { padding: 6px 10px; }
.cm-noresults { text-align: center; color: #9aa0a8; padding: 28px 12px; font-size: 14px; }
</style>
