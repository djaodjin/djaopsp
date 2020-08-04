<template>
  <fragment>
    <practice-section-header
      :small="true"
      :section="practice.question.section.name"
      :subcategory="practice.question.subcategory.name"
    />
    <p class="mb-2 description">{{ practice.question.text }}</p>
    <div class="mb-2 d-sm-inline-block">
      <v-subheader class="pl-0 pr-2 d-inline">
        {{ valueCategory.text }}
      </v-subheader>
      <practice-value-chip
        class="mr-6"
        dark
        :value="practice[valueCategory.value]"
      />
    </div>
    <div class="mb-2 d-sm-inline-block">
      <v-subheader class="pl-0 pr-2 d-inline">Implementation Rate</v-subheader>
      <implementation-value-chip :value="practice.implementationRate" />
    </div>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import PracticeSectionHeader from '@/components/PracticeSectionHeader'
import PracticeValueChip from '@/components/PracticeValueChip'
import ImplementationValueChip from '@/components/ImplementationValueChip'

export default {
  name: 'PracticeOverview',

  props: ['practice', 'valueCategory'],

  components: {
    Fragment,
    ImplementationValueChip,
    PracticeSectionHeader,
    PracticeValueChip,
  },
}
</script>
