<template>
  <v-fade-transition mode="out-in">
    <div :key="subcategory.id" class="section-subcategory">
      <practice-section-header
        class="ml-md-4"
        :section="section.content.name"
        :subcategory="subcategory.content.name"
      />
      <table class="mt-4 mx-n4 mt-md-8 mx-xl-0 mb-xl-4">
        <thead>
          <tr>
            <th class="pl-4 pl-md-8">Questions</th>
            <th class="pr-3 pr-md-8">Answers</th>
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

    @media #{map-get($display-breakpoints, 'sm-and-up')} {
      width: calc(100% + 32px); // make up for the negative margins
    }

    th {
      &:first-child {
        text-align: left;
        width: 72%;

        @media #{map-get($display-breakpoints, 'md-and-up')} {
          width: 65%;
        }
      }
      &:last-child {
        width: 28%;

        @media #{map-get($display-breakpoints, 'md-and-up')} {
          width: 35%;
        }
      }
    }
    tr:nth-child(even) {
      background-color: $background-row-alternate;
    }
  }

  @media #{map-get($display-breakpoints, 'xl-only')} {
    width: 70%;

    & ::v-deep table {
      width: 100%;
    }
  }
}
</style>
