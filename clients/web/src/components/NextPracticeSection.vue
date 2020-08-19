<template>
  <footer class="mt-md-8 mt-xl-0">
    <a
      class="reference my-6 my-md-0 ml-md-4 mx-xl-0 mb-xl-6"
      href="/docs/faq/#best-practices-1"
      >How were best practices for each industry segment identified or
      selected?</a
    >
    <v-card outlined class="py-3 px-4 mx-md-4 pa-md-4 mx-xl-0">
      <practice-section-header
        class="text-right"
        :section="section.content.name"
        :subcategory="subcategory.content.name"
      />
      <div class="mt-4 text-right">
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
  </footer>
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

<style lang="scss" scoped>
footer {
  .reference {
    display: block;
    font-size: 0.85rem;
    width: 70%;
  }

  @media #{map-get($display-breakpoints, 'md-and-up')} {
    display: flex;
    justify-content: space-between;

    .reference {
      width: 30%;
      font-size: 0.9rem;
      line-height: 1.6;
      align-self: flex-start;
    }

    ::v-deep .v-card {
      width: 55%;
    }
  }

  @media #{map-get($display-breakpoints, 'lg-and-up')} {
    ::v-deep .v-card {
      width: 45%;
    }
  }

  @media #{map-get($display-breakpoints, 'xl-only')} {
    display: block;

    .reference {
      width: 100%;
    }

    ::v-deep .v-card {
      width: 100%;
    }
  }
}
</style>
