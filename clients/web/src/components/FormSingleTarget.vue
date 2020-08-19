<template>
  <div v-bind="$attrs">
    <v-checkbox
      class="mt-0"
      hide-details
      v-model="target.enabled"
      @click="validate"
    >
      <template v-slot:label>
        <b>{{ targetConfig.text }}</b>
      </template>
    </v-checkbox>

    <v-expand-transition>
      <div class="pl-8 py-1" v-show="target.enabled">
        <v-textarea
          class="mt-4"
          :label="$t('targets.tab1.form.textarea-target')"
          v-model="target.text"
          hide-details="auto"
          auto-grow
          outlined
          rows="5"
          row-height="16"
          :rules="[
            (v) =>
              !!v ||
              !target.enabled ||
              'Please supply a target description or uncheck the target',
          ]"
        ></v-textarea>
        <div class="mt-3 examples">
          <span>
            Need help writing your target?
            <button type="button" @click="areExamplesVisible = true">
              View some examples.
            </button>
          </span>
          <v-expand-transition>
            <ul class="ml-4" v-show="areExamplesVisible">
              <li
                class="mt-2"
                v-for="(example, index) in targetConfig.examples"
                :key="index"
              >
                {{ example }}
              </li>
            </ul>
          </v-expand-transition>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import { VALID_ASSESSMENT_TARGETS } from '@/config/app'

export default {
  name: 'FormSingleTarget',

  props: ['target'],

  data() {
    return {
      areExamplesVisible: false,
      targetConfig: VALID_ASSESSMENT_TARGETS.find(
        (config) => config.value === this.target.key
      ),
    }
  },

  methods: {
    validate() {
      this.$emit('form:validate')
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.examples {
  font-size: 0.9rem;

  button {
    color: $primary-color;

    &:active,
    &:focus {
      outline: 0 none;
    }
  }

  ul {
    list-style: disc;
  }
}
</style>
