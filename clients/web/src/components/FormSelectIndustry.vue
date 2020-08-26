<template>
  <v-sheet
    class="px-6 pt-6 pb-3"
    :elevation="STANDALONE ? 3 : 0"
    :outlined="!Boolean(STANDALONE)"
  >
    <form data-cy="industry-form" @submit.prevent="submitIndustry">
      <label data-cy="industry-label" for="industry" class="d-block mb-3">
        Please choose the industry that best applies to your organization:
      </label>
      <v-select
        id="industry"
        hide-details
        label="Industry segment"
        class="mb-6"
        :items="industries"
      >
        <template v-slot:item="{ item, on, attrs }">
          <v-list-item-content v-bind="attrs" v-on="on">
            <v-list-item-title
              :class="[item.isChild ? 'child' : 'single']"
              v-text="item.text"
              @click="selectIndustry(item)"
            ></v-list-item-title>
          </v-list-item-content>
        </template>
      </v-select>
      <div v-show="industry" class="text-right">
        <button-primary type="submit" display="inline">Next</button-primary>
      </div>
      <div class="text-right mt-8 mb-4">
        <span>Don't know what to select?</span>
        <a data-cy="examples" class="ml-2" href="/docs/faq/#general-4"
          >See examples.</a
        >
      </div>
    </form>
  </v-sheet>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'FormSelectIndustry',

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.industries = await this.$context.getIndustries()
    },
    selectIndustry(item) {
      this.industry = {
        title: item.text,
        path: item.value,
      }
    },
    submitIndustry() {
      this.$emit('industry:set', this.industry)
    },
  },

  data() {
    return {
      industries: [],
      industry: null,
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  components: {
    ButtonPrimary,
  },
}
</script>

<style lang="scss" scoped>
.v-list-item__title.child {
  margin-left: 16px;
}
</style>
