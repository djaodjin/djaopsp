// Copyright (c) 2022, DjaoDjin inc.
// see LICENSE.

Vue.component('scorecard', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        return {
            url: this.$urls.survey_api_sample_answers,
            rfxCoreAvailable: false,
            metricsAvailable: false,
            targetsAvailable: false,
            activitySpecificAvailable: false
        }
    },
    mounted: function(){
        this.get();
    }
});
