<template>
  <!-- TODO: Refactor into target components -->
  <form @submit.prevent="processForm">
    <v-checkbox v-model="withEnergyReduction" hide-details>
      <template v-slot:label>
        <b>{{ $t('targets.tab2.form.cbx-energy') }}</b>
      </template>
    </v-checkbox>
    <v-expand-transition>
      <v-container class="pl-8 py-1" v-show="withEnergyReduction">
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuByEnergy"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateByEnergy"
                  label="By"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateByEnergy"
                @input="menuByEnergy = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              :label="$t('targets.tab2.form.textarea-label')"
              hide-details="auto"
              auto-grow
              outlined
              rows="3"
              row-height="16"
            ></v-textarea>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuBaselineEnergy"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateBaselineEnergy"
                  label="Baseline"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateBaselineEnergy"
                @input="menuBaselineEnergy = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
      </v-container>
    </v-expand-transition>

    <v-checkbox v-model="withGhgEmissions" hide-details>
      <template v-slot:label>
        <b>{{ $t('targets.tab2.form.cbx-emissions') }}</b>
      </template>
    </v-checkbox>
    <v-expand-transition>
      <v-container class="pl-8 py-1" v-show="withGhgEmissions">
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuByEmissions"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateByEmissions"
                  label="By"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateByEmissions"
                @input="menuByEmissions = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              :label="$t('targets.tab2.form.textarea-label')"
              hide-details="auto"
              auto-grow
              outlined
              rows="3"
              row-height="16"
            ></v-textarea>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuBaselineEmissions"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateBaselineEmissions"
                  label="Baseline"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateBaselineEmissions"
                @input="menuBaselineEmissions = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
      </v-container>
    </v-expand-transition>

    <v-checkbox v-model="withWaterUse" hide-details>
      <template v-slot:label>
        <b>{{ $t('targets.tab2.form.cbx-water') }}</b>
      </template>
    </v-checkbox>
    <v-expand-transition>
      <v-container class="pl-8 py-1" v-show="withWaterUse">
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuByWater"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateByWater"
                  label="By"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateByWater"
                @input="menuByWater = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              :label="$t('targets.tab2.form.textarea-label')"
              hide-details="auto"
              auto-grow
              outlined
              rows="3"
              row-height="16"
            ></v-textarea>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuBaselineWater"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateBaselineWater"
                  label="Baseline"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateBaselineWater"
                @input="menuBaselineWater = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
      </v-container>
    </v-expand-transition>

    <v-checkbox v-model="withWaste" hide-details>
      <template v-slot:label>
        <b>{{ $t('targets.tab2.form.cbx-waste') }}</b>
      </template>
    </v-checkbox>
    <v-expand-transition>
      <v-container class="pl-8 py-1" v-show="withWaste">
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuByWaste"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateByWaste"
                  label="By"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateByWaste"
                @input="menuByWaste = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              :label="$t('targets.tab2.form.textarea-label')"
              hide-details="auto"
              auto-grow
              outlined
              rows="3"
              row-height="16"
            ></v-textarea>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-menu
              :close-on-content-click="false"
              v-model="menuBaselineWaste"
              transition="scale-transition"
              offset-y
            >
              <template v-slot:activator="{ on, attrs }">
                <v-text-field
                  hide-details="auto"
                  v-model="dateBaselineWaste"
                  label="Baseline"
                  append-icon="mdi-calendar"
                  readonly
                  v-bind="attrs"
                  v-on="on"
                ></v-text-field>
              </template>
              <v-date-picker
                v-model="dateBaselineWaste"
                @input="menuBaselineWaste = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>
      </v-container>
    </v-expand-transition>

    <button-primary class="my-5" type="submit">{{
      $t('targets.tab2.btn-submit')
    }}</button-primary>
  </form>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'AssessmentEnvironmentalTargets',

  props: ['assessmentId'],

  data() {
    return {
      dateByEnergy: new Date().toISOString().substr(0, 10),
      dateBaselineEnergy: new Date().toISOString().substr(0, 10),
      menuByEnergy: false,
      menuBaselineEnergy: false,
      dateByEmissions: new Date().toISOString().substr(0, 10),
      dateBaselineEmissions: new Date().toISOString().substr(0, 10),
      menuByEmissions: false,
      menuBaselineEmissions: false,
      dateByWater: new Date().toISOString().substr(0, 10),
      dateBaselineWater: new Date().toISOString().substr(0, 10),
      menuByWater: false,
      menuBaselineWater: false,
      dateByWaste: new Date().toISOString().substr(0, 10),
      dateBaselineWaste: new Date().toISOString().substr(0, 10),
      menuByWaste: false,
      menuBaselineWaste: false,
      withEnergyReduction: true,
      withGhgEmissions: true,
      withWaterUse: true,
      withWaste: true,
    }
  },

  methods: {
    processForm: function () {
      console.log('form submitted: ', this.form)
      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.assessmentId },
      })
    },
  },

  components: {
    ButtonPrimary,
  },
}
</script>
