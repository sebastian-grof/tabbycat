<script setup>
import { useDraggable } from '../../templates/composables/useDraggable.js'
import { useDjangoI18n } from '../../templates/composables/useDjangoI18n.js'
import { useCategoryManagerStore } from './categoryManagerStore.js'

const props = defineProps({
  tournament: { type: Object, required: true },
})

const store = useCategoryManagerStore()
const { gettext } = useDjangoI18n()
const { dragStart, dragEnd, drag } = useDraggable({
  locked: false,
  dragPayload: { type: 'tournament', id: props.tournament.id },
})
</script>

<template>
  <div
    class="cm-row cm-tournament"
    draggable="true"
    @drag="drag"
    @dragstart="dragStart"
    @dragend="dragEnd"
  >
    <span class="cm-grip" :title="gettext('Drag to move')">
      <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><circle cx="9" cy="6" r="1.5" /><circle cx="9" cy="12" r="1.5" /><circle cx="9" cy="18" r="1.5" /><circle cx="15" cy="6" r="1.5" /><circle cx="15" cy="12" r="1.5" /><circle cx="15" cy="18" r="1.5" /></svg>
    </span>
    <span class="cm-fileicon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
    </span>
    <span class="cm-name text-truncate">{{ tournament.name }}</span>
    <span v-if="!tournament.active" class="cm-tag">{{ gettext('inactive') }}</span>
    <span class="cm-spacer"></span>
    <span class="cm-actions">
      <button type="button" class="cm-iconbtn" :title="gettext('Move up')" @click="store.reorderTournament(tournament.id, 'up')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5" /><polyline points="5 12 12 5 19 12" /></svg>
      </button>
      <button type="button" class="cm-iconbtn" :title="gettext('Move down')" @click="store.reorderTournament(tournament.id, 'down')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><polyline points="19 12 12 19 5 12" /></svg>
      </button>
    </span>
  </div>
</template>

<style scoped>
.cm-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 8px;
  border-radius: 9px;
  font-size: 14px;
  cursor: grab;
  transition: background .12s;
}
.cm-row:hover { background: #f7f5fb; }

.cm-grip { display: inline-flex; color: #cdd1d8; cursor: grab; flex: 0 0 16px; }
.cm-grip svg { width: 16px; height: 16px; }
.cm-fileicon { display: inline-flex; color: #aab0b8; flex: 0 0 auto; }
.cm-fileicon svg { width: 17px; height: 17px; }

.cm-name { font-weight: 500; color: #41464d; min-width: 0; }
.cm-tag {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: #9aa0a8;
  background: #eef0f2;
  padding: 2px 7px;
  border-radius: 5px;
}
.cm-spacer { flex: 1 1 auto; }

.cm-actions { display: flex; align-items: center; gap: 2px; opacity: 0; transition: opacity .12s; }
.cm-row:hover .cm-actions,
.cm-row:focus-within .cm-actions { opacity: 1; }
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
</style>
