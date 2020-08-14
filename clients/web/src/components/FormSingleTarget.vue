<template>
  <fragment>
    <v-checkbox class="mt-0" v-model="isEnabled" hide-details>
      <template v-slot:label>
        <b>{{ targetConfig.text }}</b>
      </template>
    </v-checkbox>

    <v-expand-transition>
      <div class="pl-8 py-1" v-show="isEnabled">
        <v-textarea
          class="mt-4"
          :label="$t('targets.tab1.form.textarea-target')"
          v-model="target.text"
          hide-details="auto"
          auto-grow
          outlined
          rows="4"
          row-height="16"
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
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { VALID_ASSESSMENT_TARGETS } from '@/config/app'

export default {
  name: 'FormSingleTarget',

  props: ['target'],

  data() {
    return {
      isEnabled: true,
      areExamplesVisible: false,
      targetConfig: VALID_ASSESSMENT_TARGETS.find(
        (config) => config.value === this.target.key
      ),
    }
  },

  components: {
    Fragment,
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
