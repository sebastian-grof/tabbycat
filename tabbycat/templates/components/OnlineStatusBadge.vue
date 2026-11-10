<script setup>
import { useDjangoI18n } from '../composables/useDjangoI18n.js'

defineProps({ online: { type: Boolean, default: false } })
const { gettext } = useDjangoI18n()
</script>

<template>
  <span
    v-if="online"
    class="badge online-status"
    :title="gettext('Participating remotely')"
    :aria-label="gettext('Online adjudicator: participating remotely')"
  >{{ gettext('Online') }}</span>
</template>
