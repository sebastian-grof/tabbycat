<script setup>
import { computed, nextTick, ref } from 'vue'
import { useDraggable } from '../../templates/composables/useDraggable.js'
import { useDjangoI18n } from '../../templates/composables/useDjangoI18n.js'
import { useCategoryManagerStore } from './categoryManagerStore.js'
import CategoryTournament from './CategoryTournament.vue'

const props = defineProps({
  folder: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})

const store = useCategoryManagerStore()
const { gettext } = useDjangoI18n()

const { dragStart, dragEnd, drag } = useDraggable({
  locked: false,
  dragPayload: { type: 'folder', id: props.folder.id },
})

const editingName = ref(false)
const settingsOpen = ref(false)
const nameInput = ref(null)

const childFolders = computed(() => store.childFolders(props.folder.id).filter((f) => store.folderVisible(f)))
const childTournaments = computed(() => store.folderTournaments(props.folder.id).filter((t) => store.tournamentVisible(t)))
const totalFolders = computed(() => store.childFolders(props.folder.id).length)
const totalTournaments = computed(() => store.folderTournaments(props.folder.id).length)
const hasChildren = computed(() => totalFolders.value > 0 || totalTournaments.value > 0)
const hasVisibleChildren = computed(() => childFolders.value.length > 0 || childTournaments.value.length > 0)
const searching = computed(() => store.normalisedQuery.length > 0)
const expanded = computed(() => (searching.value ? true : store.isExpanded(props.folder.id)))

const countLabel = computed(() => {
  const f = totalFolders.value
  const t = totalTournaments.value
  const folderWord = f === 1 ? gettext('folder') : gettext('folders')
  const tournamentWord = t === 1 ? gettext('tournament') : gettext('tournaments')
  return `${f} ${folderWord} · ${t} ${tournamentWord}`
})

// Drop target state
const dragCounter = ref(0)
const aboutToDrop = ref(false)

const onDragEnter = () => {
  dragCounter.value += 1
  aboutToDrop.value = true
}
const onDragLeave = () => {
  dragCounter.value -= 1
  if (dragCounter.value === 0) {
    aboutToDrop.value = false
  }
}
const onDrop = (event) => {
  dragCounter.value = 0
  aboutToDrop.value = false
  let payload
  try {
    payload = JSON.parse(event.dataTransfer.getData('text'))
  } catch (error) {
    return
  }
  store.handleDrop(payload, props.folder.id)
}

const startRename = async () => {
  editingName.value = true
  await nextTick()
  if (nameInput.value) {
    nameInput.value.focus()
    nameInput.value.select()
  }
}

const addSubfolder = () => {
  store.createFolder(props.folder.id, gettext('New folder'))
}

const removeFolder = () => {
  const message = hasChildren.value
    ? gettext('Delete this folder? Its contents will move up to the level above.')
    : gettext('Delete this folder?')
  if (window.confirm(message)) {
    store.deleteFolder(props.folder.id)
  }
}
</script>

<template>
  <div
    class="cm-folder"
    :class="{ 'cm-drop-active': aboutToDrop }"
    @dragover.prevent
    @drop.prevent.stop="onDrop"
    @dragenter.stop="onDragEnter"
    @dragleave.stop="onDragLeave"
  >
    <div
      class="cm-row cm-folder-row"
      draggable="true"
      @drag="drag"
      @dragstart="dragStart"
      @dragend="dragEnd"
    >
      <button
        type="button"
        class="cm-chevron"
        :class="{ 'cm-hidden': !hasChildren }"
        :title="expanded ? gettext('Collapse') : gettext('Expand')"
        @click="store.toggleExpanded(folder.id)"
      >
        <svg v-if="expanded && hasChildren" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
      </button>

      <span class="cm-ficon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>
      </span>

      <span
        v-if="!editingName"
        class="cm-name"
        :title="gettext('Double-click to rename')"
        @dblclick="startRename"
      >{{ folder.name }}</span>
      <input
        v-else
        ref="nameInput"
        class="cm-input cm-name-input"
        :value="folder.name"
        @input="store.renameFolder(folder.id, $event.target.value)"
        @keyup.enter="editingName = false"
        @blur="editingName = false"
      >

      <span
        class="cm-pill"
        :class="folder.public ? 'cm-pill-public' : 'cm-pill-private'"
        role="button"
        :title="gettext('Click to toggle visibility')"
        @click="store.updateFolderField(folder.id, 'public', !folder.public)"
      ><span class="cm-dot"></span>{{ folder.public ? gettext('Public') : gettext('Private') }}</span>
      <span
        class="cm-pill"
        :class="folder.active ? 'cm-pill-active' : 'cm-pill-hidden'"
        role="button"
        :title="gettext('Click to toggle whether this folder is shown')"
        @click="store.updateFolderField(folder.id, 'active', !folder.active)"
      ><span class="cm-dot"></span>{{ folder.active ? gettext('Active') : gettext('Hidden') }}</span>

      <span class="cm-count">{{ countLabel }}</span>

      <span class="cm-spacer"></span>

      <span class="cm-actions">
        <button type="button" class="cm-iconbtn" :title="gettext('Move up')" @click="store.reorderFolder(folder.id, 'up')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" /></svg>
        </button>
        <button type="button" class="cm-iconbtn" :title="gettext('Move down')" @click="store.reorderFolder(folder.id, 'down')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" /></svg>
        </button>
        <button type="button" class="cm-iconbtn" :title="gettext('New subfolder')" @click="addSubfolder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /><line x1="12" y1="11" x2="12" y2="17" /><line x1="9" y1="14" x2="15" y2="14" /></svg>
        </button>
        <button type="button" class="cm-iconbtn" :title="gettext('Rename')" @click="startRename">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
        </button>
        <button type="button" class="cm-iconbtn" :class="{ 'cm-on': settingsOpen }" :title="gettext('Settings')" @click="settingsOpen = !settingsOpen">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" /><line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" /><line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" /><line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" /></svg>
        </button>
        <button type="button" class="cm-iconbtn cm-danger" :title="gettext('Delete')" @click="removeFolder">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
        </button>
      </span>
    </div>

    <div v-if="settingsOpen" class="cm-settings">
      <div class="cm-field cm-field-slug">
        <label>{{ gettext('Slug (public URL)') }}</label>
        <input class="cm-input" :value="folder.slug" :placeholder="gettext('Auto-generated on save')"
               @input="store.updateFolderField(folder.id, 'slug', $event.target.value)">
      </div>
      <div class="cm-field cm-field-desc">
        <label>{{ gettext('Description') }}</label>
        <input class="cm-input" :value="folder.description"
               @input="store.updateFolderField(folder.id, 'description', $event.target.value)">
      </div>
    </div>

    <div v-if="expanded" class="cm-children">
      <CategoryFolder v-for="child in childFolders" :key="'f' + child.id" :folder="child" :depth="depth + 1" />
      <CategoryTournament v-for="tournament in childTournaments" :key="'t' + tournament.id" :tournament="tournament" />
      <p v-if="!hasVisibleChildren && !searching" class="cm-empty">
        {{ gettext('Empty — drag folders or tournaments here.') }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.cm-folder { border-radius: 9px; }
.cm-folder.cm-drop-active > .cm-folder-row {
  background: rgba(102, 61, 160, .11);
  box-shadow: inset 0 0 0 2px #663da0;
}

.cm-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 8px;
  border-radius: 9px;
  font-size: 14px;
}
.cm-folder-row { cursor: grab; transition: background .12s; }
.cm-folder-row:hover { background: #f7f5fb; }

.cm-chevron {
  flex: 0 0 22px;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #9aa0a8;
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
}
.cm-chevron svg { width: 14px; height: 14px; }
.cm-chevron:hover { background: #ece8f5; color: #663da0; }
.cm-chevron.cm-hidden { visibility: hidden; }

.cm-ficon { display: inline-flex; color: #663da0; flex: 0 0 auto; }
.cm-ficon svg { width: 18px; height: 18px; }

.cm-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 260px;
  color: #272c36;
}
.cm-input { font: inherit; padding: 4px 9px; border: 1px solid #d7d3e2; border-radius: 7px; }
.cm-input:focus { outline: none; border-color: #663da0; box-shadow: 0 0 0 3px rgba(102, 61, 160, .18); }
.cm-name-input { max-width: 260px; font-weight: 600; }

.cm-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  cursor: pointer;
  border: 1px solid transparent;
  white-space: nowrap;
  user-select: none;
  transition: box-shadow .12s;
}
.cm-pill:hover { box-shadow: 0 0 0 3px rgba(20, 20, 40, .05); }
.cm-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex: 0 0 6px; }
.cm-pill-public { background: #e6f2f6; color: #1488a1; }
.cm-pill-private { background: #fceadd; color: #cc6a20; }
.cm-pill-active { background: #e1f5ed; color: #069270; }
.cm-pill-hidden { background: #eceef1; color: #828a93; }

.cm-count { font-size: 12px; color: #a2a8b0; white-space: nowrap; }
.cm-spacer { flex: 1 1 auto; }

.cm-actions { display: flex; align-items: center; gap: 2px; opacity: 0; transition: opacity .12s; }
.cm-folder-row:hover .cm-actions,
.cm-folder-row:focus-within .cm-actions { opacity: 1; }
.cm-iconbtn {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #8b929a;
  border-radius: 7px;
  cursor: pointer;
  padding: 0;
}
.cm-iconbtn svg { width: 15px; height: 15px; }
.cm-iconbtn:hover { background: #ece8f5; color: #663da0; }
.cm-iconbtn.cm-on { background: #ece8f5; color: #663da0; }
.cm-iconbtn.cm-danger:hover { background: #fbe7ee; color: #d1185e; }

.cm-settings {
  display: flex;
  gap: 14px;
  padding: 12px 14px;
  margin: 2px 0 6px 30px;
  background: #faf9fc;
  border: 1px solid #efedf4;
  border-radius: 10px;
}
.cm-field { display: flex; flex-direction: column; gap: 5px; }
.cm-field-slug { flex: 0 0 40%; }
.cm-field-desc { flex: 1 1 auto; }
.cm-field label { font-size: 11px; font-weight: 600; color: #7a818a; }
.cm-field .cm-input { width: 100%; max-width: none; }

/* Nesting + tree guide line */
.cm-children { padding-left: 11px; margin-left: 19px; border-left: 1.5px solid #e9e7ef; }
.cm-empty { font-style: italic; color: #aab0b8; font-size: 13px; padding: 4px 8px; margin: 0; }
</style>
