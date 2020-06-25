<template>
  <div class="section-subcategory">
    <practice-section-header
      :category="section.category"
      :title="subcategory.title"
    />
    <table class="mt-4 mx-n4">
      <thead>
        <tr>
          <th class="pl-4">Questions</th>
          <th>Answers</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="question in subcategory.questions" :key="question.id">
          <td class="py-2 px-4">{{ question.text }}</td>
          <td class="py-2 text-center">
            <router-link
              :to="{
                path: `${$route.path}${$route.hash}`,
                query: {
                  section: section.id,
                  subcategory: subcategory.id,
                  question: question.id,
                },
              }"
              >TBD</router-link
            >
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

export default {
  name: 'PracticeSectionSubcategory',

  props: ['section', 'subcategory'],

  components: {
    PracticeSectionHeader,
  },
}
</script>

<style lang="scss" scoped>
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
      background-color: #f1f1f1;
    }
  }
}
</style>
