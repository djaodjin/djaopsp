<template>
  <fragment>
    <section-title :title="$t('targets.title')" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>
        <div class="pa-4">
          <p>{{ $t('targets.tab1.intro') }}</p>
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-management.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-construction.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-eng-and-design.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-office-grounds.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-procurement.png"
          />
        </div>
      </template>
      <template v-slot:tab2>
        <div class="pa-4">
          <p>{{ $t('targets.tab2.intro') }}</p>
          <form-environmental-targets />
        </div>
      </template>
    </tab-container>
    <dialog-confirm
      :isOpen="showDialogPreviousTargets"
      title="Previous Targets"
      actionText="Ok, thanks"
      @confirm="closeAndSaveAsViewed"
    >
      <p>
        Your organization has submitted environmental targets in the past for
        the industry segment selected.
      </p>
      <p>
        Please edit or re-submit the targets from the most recent assessment.
      </p>
    </dialog-confirm>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import DialogConfirm from '@/components/DialogConfirm'
import FormEnvironmentalTargets from '@/components/FormEnvironmentalTargets'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

const DIALOG_PREVIOUS_TARGETS = 'previousTargets'

export default {
  name: 'AssessmentEnvironmentalTargets',

  created() {
    this.viewDialog(DIALOG_PREVIOUS_TARGETS)
  },

  methods: {
    closeAndSaveAsViewed() {
      this.showDialogPreviousTargets = false
      window.localStorage.setItem(DIALOG_PREVIOUS_TARGETS, 'viewed')
    },

    async viewDialog(dialogName) {
      const wasViewed = window.localStorage.getItem(dialogName)
      if (!wasViewed) {
        // TODO: Send request to check if previous targets have been submitted
        const previousTargetsSubmitted = true
        if (previousTargetsSubmitted) {
          this.showDialogPreviousTargets = true
        }
      }
    },
  },

  data() {
    return {
      showDialogPreviousTargets: false,
      tabs: [
        { text: this.$t('targets.tab1.title'), href: 'tab-1' },
        { text: this.$t('targets.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    DialogConfirm,
    FormEnvironmentalTargets,
    Fragment,
    SectionTitle,
    TabContainer,
  },
}
</script>
