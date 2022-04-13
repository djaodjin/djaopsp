// Copyright (c) 2022, DjaoDjin inc.
// see LICENSE.

Vue.component('scorecard', {
    mixins: [
        itemListMixin,
        practicesListMixin
    ],
    data: function() {
        return {
            url: this.$urls.survey_api_sample_answers,
            params: {o: ""},
            account_benchmark_url: this.$urls.api_account_benchmark,
            chartsLoaded: false,
            chartsAPIResp: null,
            charts: {},
            activeTile: null
        }
    },
    methods: {
        buildChart: function(data) {
            var vm = this;
            var labels = data.distribution.x;
            var datasets = [];
            var colors = [
                '#f0ad4e', '#f0ad4e',
                '#f0ad4e', '#f0ad4e'];
            datasets.push({
                label: "peers",
                backgroundColor: '#f0ad4e',
                borderColor: '#f0ad4e',
                data: data.distribution.y
            });
            var chartKey = data.slug;
            var chart = vm.charts[chartKey];
            if( chart ) {
                chart.destroy();
            }
            var element = document.getElementById(chartKey);
            if( element ) {
                vm.charts[chartKey] = new Chart(
                    element,
                    {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: datasets
                        },
                        options: {
                            responsive: false,
                            plugins: {
                                legend: {
                                    display: false,
                                    // position: 'top',
                                },
                                title: {
                                    display: false
                                }
                            }
                        },
                    }
                );
                if( data.nb_respondents ) {
                    vm.charts[chartKey].nb_respondents = data.nb_respondents;
                }
            }
        },
        buildCharts: function(resp) {
            var vm = this;
            for( var idx = 0; idx < resp.length; ++idx ) {
                if( resp[idx].normalized_score ) {
                    for( var jdx = 0; jdx < vm.items.results.length; ++jdx ) {
                        if( vm.items.results[jdx].slug === resp[idx].slug ) {
                            vm.items.results[jdx].normalized_score =
                                resp[idx].normalized_score;
                            break;
                        }
                    }
                    vm.buildChart(resp[idx]);
                }
            }
            vm.$forceUpdate();
        },
        buildSummaryChart: function() {
            // Creates the top level summary polar chart
            var vm = this;
            var chartKey = 'summary-chart';
            var chart = vm.charts[chartKey];
            if( chart ) {
                chart.destroy();
            }
            var element = document.getElementById(chartKey);
            if( element ) {
                vm.charts[chartKey] = new Chart(
                    element,
                    {
                        type: 'polarArea',
                        data: {
                            labels: [
                                'energy', 'ghg-emissions', 'waste', 'water'],
                            datasets: [{
                                label: "score",
                                data: [11, 16, 7, 3]
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    display: false,
                                    // position: 'top',
                                },
                                title: {
                                    display: false
                                }
                            }
                        },
                    }
                );
            }
        },
        getColHeaders: function(practice) {
            var vm = this;
            var headers = [];
            var answer = vm.getPrimaryAnswer(practice);  // XXX more than one
            var period = new Date(answer.created_at).getYear();
            if( !isNaN(period) ) {
                headers.push(period);
            }
            return headers;
        },
        getColValue: function(practice, colHeader) {
            var vm = this;
            var vals = [];
            var answer = vm.getPrimaryAnswer(practice);  // XXX more than one
            var period = new Date(answer.created_at).getYear();
            if( !isNaN(period) ) {
                headers.push(answer.measured);
            }
            return headers;
        },
        getNbRespondents: function(practice) {
            var vm = this;
            return vm.charts &&
                vm.charts[practice.slug] &&
                vm.charts[practice.slug].nb_respondents ?
                vm.charts[practice.slug].nb_respondents : "?";
        },
        indentHeader: function(practice) {
            var vm = this;
            if( vm.isPractice(practice) ) {
                return "bestpractice";
            }
            if( practice.indent <= 0 ) {
                return "heading-tile";
            }
            var indentSpace = practice.indent - 1;
            return "heading-" + indentSpace;
        },
        resetAssessment: function($event, prefix) {
            var vm = this;
            var form = $($event.target);
            var modalDialog = form.parents('.modal');
            modalDialog.modal('hide');
            var path = vm.activeTile.path;
            vm.reqPost(vm.$urls.api_assessment_sample + '/reset' + path,
            function success(resp) {
                console.log("XXX removed section");
                vm.items = {results: [], count: 0};
                vm.itemsLoaded = false;
                vm.get();
            });
        },
        setActiveElement: function(practice) {
            this.activeTile = practice;
        },
    },
    computed: {
    },
    watch: {
        itemsLoaded: function (val) {
            var vm = this;
            if( vm.chartsLoaded ) {
                setTimeout(function() {
                    vm.buildCharts(vm.chartsAPIResp);
                }, 5000);
            }
        },
        chartsLoaded: function (val) {
            var vm = this;
            if( vm.itemsLoaded ) {
                setTimeout(function() {
                    vm.buildCharts(vm.chartsAPIResp);
                }, 5000);
            }
        },
    },
    mounted: function(){
        var vm = this;
        vm.get();
        vm.reqGet(vm.account_benchmark_url,
        function(resp) {
            vm.chartsAPIResp = resp;
            vm.chartsLoaded = true;
        });
        vm.buildSummaryChart();
    }
});


Vue.component('scorecard-history', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_historical_scores,
        }
    },
    mounted: function(){
        this.get();
    }
});
