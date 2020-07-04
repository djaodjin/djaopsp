<template>
  <v-fade-transition mode="out-in">
    <div :key="subcategory.id" class="section-subcategory">
      <practice-section-header
        :category="section.content.name"
        :title="subcategory.content.name"
      />
      <table class="mt-4 mx-n4">
        <thead>
          <tr>
            <th class="pl-4">Questions</th>
            <th class="pr-3">Answers</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="question in subcategory.questions" :key="question.id">
            <practice-section-subcategory-row
              :section="section"
              :subcategory="subcategory"
              :question="question"
              :answers="answers"
            />
          </tr>
        </tbody>
      </table>
    </div>
  </v-fade-transition>
</template>

<script>
import PracticeSectionHeader from '@/components/PracticeSectionHeader'
import PracticeSectionSubcategoryRow from './PracticeSectionSubcategoryRow'

export default {
  name: 'PracticeSectionSubcategory',

  props: ['section', 'subcategory', 'answers'],

  components: {
    PracticeSectionHeader,
    PracticeSectionSubcategoryRow,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.section-subcategory {
  & ::v-deep table {
    border-collapse: collapse;

    th {
      &:first-child {
        text-align: left;
        width: 72%;
      }
      &:last-child {
        width: 28%;
      }
    }
    tr:nth-child(even) {
      background-color: $background-row-alternate;
    }
  }
}
</style>
