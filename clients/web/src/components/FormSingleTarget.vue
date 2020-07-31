<template>
  <fragment>
    <v-checkbox class="mt-2" v-model="target.include" hide-details>
      <template v-slot:label>
        <b>{{ label }}</b>
      </template>
    </v-checkbox>

    <v-expand-transition>
      <div class="pl-8 py-1" v-show="target.include">
        <div class="date-picker">
          <v-menu
            :close-on-content-click="false"
            v-model="menuBy"
            transition="scale-transition"
            offset-y
            max-width="290"
          >
            <template v-slot:activator="{ on, attrs }">
              <v-text-field
                v-bind="attrs"
                v-on="on"
                hide-details="auto"
                v-model="target.dateBy"
                label="By"
                append-icon="mdi-calendar"
                readonly
              ></v-text-field>
            </template>
            <v-date-picker
              v-model="target.dateBy"
              :min="new Date().toISOString()"
              @input="menuBy = false"
            ></v-date-picker>
          </v-menu>
        </div>

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

        <div class="date-picker">
          <v-menu
            :close-on-content-click="false"
            v-model="menuBaseline"
            transition="scale-transition"
            offset-y
            max-width="290"
          >
            <template v-slot:activator="{ on, attrs }">
              <v-text-field
                v-bind="attrs"
                v-on="on"
                hide-details="auto"
                v-model="target.dateBaseline"
                label="Baseline"
                append-icon="mdi-calendar"
                readonly
              ></v-text-field>
            </template>
            <v-date-picker
              v-model="target.dateBaseline"
              :max="new Date().toISOString()"
              @input="menuBaseline = false"
            ></v-date-picker>
          </v-menu>
        </div>

        <v-textarea
          class="mt-4"
          :label="$t('targets.tab1.form.textarea-comments')"
          v-model="target.comments"
          hide-details="auto"
          auto-grow
          outlined
          rows="4"
          row-height="16"
        ></v-textarea>
      </div>
    </v-expand-transition>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'

export default {
  name: 'FormSingleTarget',

  props: ['label', 'target'],

  data() {
    return {
      menuBy: false,
      menuBaseline: false,
    }
  },

  components: {
    Fragment,
  },
}
</script>

<style lang="scss" scoped>
.date-picker {
  max-width: 290px;
}
</style>
