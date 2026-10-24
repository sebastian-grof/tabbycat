<script setup>
import { computed, ref } from 'vue'
import { useAjax } from '../composables/useAjax.js'

const props = defineProps({
  cellData: Object,
})

const emit = defineEmits(['saved'])

const { ajaxSave } = useAjax(time => emit('saved', time))

const displayValue = computed(() => props.cellData.value ?? '')
const saving = ref(false)

const selectUpdate = (newValue) => {
  const cd = props.cellData
  const previousValue = cd.value
  const selectedOption = cd.options.find(option => String(option.value) === newValue)
  const selectedValue = newValue === '' ? null : (selectedOption?.value ?? newValue)
  cd.value = selectedValue

  if (props.cellData.noSave) {
    return
  }

  const payload = { ...cd.payload, [cd.payloadKey]: selectedValue }
  saving.value = true
  ajaxSave(cd.saveURL, payload, cd.saveMessage, () => {
    // Keep an existing batch-edit form in sync with successful inline edits.
    const batchField = cd.syncFieldId && document.getElementById(cd.syncFieldId)
    if (batchField) batchField.value = selectedValue ?? ''
    saving.value = false
  }, () => {
    cd.value = previousValue
    saving.value = false
  }, null)
}
</script>

<template>
  <td :class="cellData.class ? cellData.class : null">
    <select
      :value="displayValue"
      class="form-control"
      :name="cellData.name"
      :disabled="saving"
      @change="selectUpdate($event.target.value)"
    >
      <option
        v-if="cellData.blankLabel !== undefined"
        value=""
      >
        {{ cellData.blankLabel }}
      </option>
      <option
        v-for="option in cellData.options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>
  </td>
</template>
