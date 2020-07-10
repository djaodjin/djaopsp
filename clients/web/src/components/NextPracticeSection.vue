<template>
  <v-card outlined class="py-3 px-4">
    <practice-section-header
      :section="section.content.name"
      :subcategory="subcategory.content.name"
    />
    <div class="mt-2 text-right">
      <button-primary
        color="secondary"
        display="inline"
        :to="{
          path: `${$route.path}${$route.hash}`,
          query: {
            section: section.id,
            subcategory: subcategory.id,
          },
        }"
      >
        <span>View Next Section</span>
        <v-icon class="ml-2" small color="white">mdi-arrow-right</v-icon>
      </button-primary>
    </div>
  </v-card>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

export default {
  name: 'NextPracticeSection',

  props: ['section', 'subcategory'],

  components: {
    ButtonPrimary,
    PracticeSectionHeader,
  },
}
</script>
