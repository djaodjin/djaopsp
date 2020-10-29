<template>
  <fragment>
    <intro-section
      :orgName="organization.name"
      :industryName="assessment.industryName"
      title="Environmental Targets"
    >
      <div>
        <p>
          Define environmental targets for your organization and communicate its
          commitment to <b>adopt sustainable business practices</b>.
        </p>
        <p>
          Let environmental targets <b>guide and support your business</b> after
          benchmarking your performance data against other organizations in the
          industry.
        </p>
        <button-primary
          data-cy="btn-continue"
          class="mt-8"
          :to="
            $routeMap.get('assessmentTargets').getPath({
              org,
              slug: assessment.slug,
              industryPath: assessment.industryPath,
            })
          "
          >Continue</button-primary
        >
        <div class="text-center">
          <v-btn
            text
            class="mx-n4 mx-sm-0 mt-6"
            color="secondary"
            :to="
              $routeMap.get('assessmentHome').getPath({
                org: organizationId,
                slug: assessment.slug,
                industryPath: assessment.industryPath,
              })
            "
          >
            Continue without targets
          </v-btn>
        </div>
      </div>
    </intro-section>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'

export default {
  name: 'IntroEnvironmentalTargets',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization, assessment] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.org, this.id),
      ])
      this.organization = organization
      this.assessment = assessment
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
    }
  },

  components: {
    Fragment,
    ButtonPrimary,
    IntroSection,
  },
}
</script>
