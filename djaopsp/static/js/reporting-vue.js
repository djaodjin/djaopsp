// reporting components

Vue.component('reporting-organizations', {
    mixins: [
        itemListMixin
    ],
    data: function(){
        var data = {
            url: this.$urls.api_suppliers,
            item: {
                email: "",
                full_name: "",
                type: "organization",
                printable_name: "",
                created_at: null
            },
            message: "",
            start_at: null,
            accountExtra: {
                supply_chain: false,
                reminder: false
            },
            getCompleteCb: 'populateSummaryChart',
        }
        if( this.$dateRange ) {
            if( this.$dateRange.start_at ) {
                data.start_at = moment(
                    this.$dateRange.start_at).format("YYYY-MM-DD");
            }
        }
        if( this.$accountExtra ) {
            data.accountExtra = this.$accountExtra;
        }
        return data;
    },
    methods: {
        getScoreDisplay: function(score) {
            return (score !== null) ? score.toString() + "%" : "";
        },
        shortDate: function(at_time) {
            return moment(at_time).format("MMM D, YYYY");
        },

        populateSummaryChart: function() {
            var vm = this;
            // populate the completion summary chart
            var summary = $("#completion-summary-chart .chart");
            summary.empty();
            summary.append("<svg></svg>");
            summaryChart("#completion-summary-chart .chart svg",
                vm.items.summary);
        },
        addAccount: function(dataset, newAccount) {
            var vm = this;
            if( newAccount ) {
                if( newAccount.hasOwnProperty('slug') && newAccount.slug ) {
                    vm.item.slug = newAccount.slug;
                }
                if( newAccount.hasOwnProperty('email') && newAccount.email ) {
                    vm.item.email = newAccount.email;
                }
                if( newAccount.hasOwnProperty('full_name')
                    && newAccount.full_name ) {
                    vm.item.full_name = newAccount.full_name;
                }
                if( newAccount.hasOwnProperty('created_at')
                    && newAccount.created_at ) {
                    vm.item.created_at = newAccount.created_at;
                }
            }
            $("#invite-reporting-entity").modal("show");
        },
        requestAssessment: function() {
            var vm = this;
            vm.$refs.account.reset();
            vm.reqPost(vm.$urls.api_accessibles, {organization: vm.item},
            function success(resp) {
                vm.get();
            },
            function fail(resp) {
                if( resp.status === 404 ) {
                    vm.reqPost(vm.$urls.api_accessibles + "?force=1", {
                        organization: vm.item,
                        message: $('[name="message"]').val()},
                    function success(resp) {
                        vm.get();
                    },
                    function error(resp) {
                        showErrorMessages(resp);
                    });
                } else {
                    showErrorMessages(resp);
                }
            });
            return false;
        },
        remove: function ($event, idx) {
            var vm = this;
            var removeUrl = vm.$urls.api_accessibles + vm.items.results[idx].slug + '/';
            vm.reqDelete(removeUrl,
            function success(resp) {
                // XXX need to consider multiple segments
                vm.items.results.splice(idx, 1);
            });
        },
        savePreferences: function() {
            var vm = this;
            var updated = true;
            vm.accountExtra['o'] = vm.params.o;
            vm.accountExtra['ot'] = vm.params.ot;
            if( vm.start_at ) {
                vm.accountExtra['start_at'] = vm.start_at;
                updated = true;
            } else {
                delete vm.accountExtra.start_at;
            }
            vm.reqPatch(vm.$urls.api_organization_profile, {
                extra: JSON.stringify(vm.accountExtra)},
            function(resp) {
                if( updated ) vm.filterList();
                showMessages(['Preferences saved.'], 'info');
            });
        },
    },
    mounted: function(){
        this.get();
    }
});


Vue.component('activity-summary', {
    data: function() {
        return this.getInitData();
    },
    methods: {
        getInitData: function(){
            var data = {
                params: {
                    ends_at: null
                }
            };
            if( this.$dateRange.ends_at ) {
                // uiv-date-picker will expect ends_at as a String
                // but DATE_FORMAT will literally cut the hour part,
                // regardless of timezone. We don't want an empty list
                // as a result.
                // If we use moment `endOfDay` we get 23:59:59 so we
                // add a full day instead.
                data.params['ends_at'] = moment(
                    this.$dateRange.ends_at).add(1,'days').format('YYYY-MM-DD');
            }
            return data;
        }
    }
});


Vue.component('reporting-practices', {
    mixins: [
        itemListMixin
    ],
    data: function(){
        return {
            url: this.$urls.api_reporting_practices,
        }
    },
    methods: {
    },
    mounted: function(){
        this.get()
    }
});


/** Reporting completion rate
 */
Vue.component('reporting-completion-rate', {
    mixins: [
        itemMixin
    ],
    props: [
        'ends_at'
    ],
    data: function(){
        return {
            url: this.$urls.api_reporting_completion_rate,
            getCb: 'chart'
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            var labels = [];
            var datasets = [];
            var colors = [UTILITY_COLOR, UTILITY_COLOR_LAST, EUISSCA_COLOR];
            for( var idx = 0; idx < resp.table.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.table[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        var label = moment(
                            resp.table[idx].values[valIdx][0]).format(
                                'YYYY-MM-DD');
                        labels.push(label);
                    }
                    data.push(resp.table[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.table[idx].key,
                    backgroundColor: colors[idx],
                    borderColor: colors[idx],
                    data: data
                });
            }
            if( vm.completionRate ) {
                vm.completionRate.destroy();
            }
            vm.completionRate = new Chart(
                document.getElementById('completionRate'),
                {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {}
                }
            );
        },
        get: function(){
            var vm = this;
            if(!vm.url) return;
            var url = vm.url;
            if( vm.ends_at ) {
                url += '?ends_at=' + vm.ends_at
            }
            var cb = vm[vm.getCb];
            if( !cb ) {
                cb = function(res){
                    vm.item = res
                    vm.itemLoaded = true;
                }
            }
            vm.reqGet(url, cb);
        },
    },
    mounted: function(){
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
    watch: {
        ends_at: function(newVal, oldVal) {
            this.debouncedGet();
        }
    },
});


/** Reporting planned improvements and targets
 */
Vue.component('reporting-goals', {
    mixins: [
        itemMixin
    ],
    props: [
        'ends_at'
    ],
    data: function(){
        return {
            url: this.$urls.api_reporting_goals,
            getCb: 'chart'
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            var labels = [];
            var datasets = [];
            var colors = [UTILITY_COLOR, EUISSCA_COLOR];
            for( var idx = 0; idx < resp.table.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.table[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.table[idx].values[valIdx][0]);
                    }
                    data.push(resp.table[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.table[idx].key,
                    backgroundColor: colors[idx],
                    borderColor: colors[idx],
                    data: data
                });
            }
            if( vm.goals ) {
                vm.goals.destroy();
            }
            vm.goals = new Chart(
                document.getElementById('goals'),
                {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: false,
                                text: 'Planned improvements & targets'
                            }
                        }
                    },
                }
            );
        },
        get: function(){
            var vm = this;
            if(!vm.url) return;
            var url = vm.url;
            if( vm.ends_at ) {
                url += '?ends_at=' + vm.ends_at
            }
            var cb = vm[vm.getCb];
            if( !cb ) {
                cb = function(res){
                    vm.item = res
                    vm.itemLoaded = true;
                }
            }
            vm.reqGet(url, cb);
        },
    },
    mounted: function(){
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
    watch: {
        ends_at: function(newVal, oldVal) {
            this.debouncedGet();
        }
    },
});


/** Reporting assessments completed by segments
 */
Vue.component('reporting-by-segments', {
    mixins: [
        itemMixin
    ],
    props: [
        'ends_at'
    ],
    data: function(){
        return {
            url: this.$urls.api_reporting_by_segments,
            getCb: 'chart'
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            var labels = [];
            var datasets = [];
            var colors = [UTILITY_COLOR, EUISSCA_COLOR];
            for( var idx = 0; idx < resp.table.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.table[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.table[idx].values[valIdx][0]);
                    }
                    data.push(resp.table[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.table[idx].key,
                    backgroundColor: colors[idx],
                    borderColor: colors[idx],
                    data: data
                });
            }
            if( vm.bySegements ) {
                vm.bySegements.destroy();
            }
            vm.bySegements = new Chart(
                document.getElementById('bySegements'),
                {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        indexAxis: 'y',
                        // Elements options apply to all of the options unless
                        // overridden in a dataset In this case, we are setting
                        // the border of each horizontal bar to be 2px wide.
                        elements: {
                            bar: {
                                borderWidth: 2,
                            }
                        },
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right',
                            },
                            title: {
                                display: false,
                                text: 'By Segments'
                            }
                        }
                    },
                }
            );
        },
        get: function(){
            var vm = this;
            if(!vm.url) return;
            var url = vm.url;
            if( vm.ends_at ) {
                url += '?ends_at=' + vm.ends_at
            }
            var cb = vm[vm.getCb];
            if( !cb ) {
                cb = function(res){
                    vm.item = res
                    vm.itemLoaded = true;
                }
            }
            vm.reqGet(url, cb);
        },
    },
    mounted: function(){
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
    watch: {
        ends_at: function(newVal, oldVal) {
            this.debouncedGet();
        }
    },
});


/** Reporting GHG emissions (%)
 */
Vue.component('reporting-ghg-emissions-rate', {
    mixins: [
        itemMixin
    ],
    props: [
        'ends_at'
    ],
    data: function(){
        return {
            url: this.$urls.api_reporting_ghg_emissions_rate,
            getCb: 'chart'
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            var labels = [];
            var datasets = [];
            var colors = [
                [UTILITY_COLOR, UTILITY_COLOR_LAST],
                [EUISSCA_COLOR, EUISSCA_COLOR_LAST]];
            for( var idx = 0; idx < resp.table.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.table[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.table[idx].values[valIdx][0]);
                    }
                    data.push(resp.table[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.table[idx].key,
                    backgroundColor: colors[idx],
                    data: data
                });
            }
            if( vm.GHGEmissionsRate ) {
                vm.GHGEmissionsRate.destroy();
            }
            vm.GHGEmissionsRate = new Chart(
                document.getElementById('GHGEmissionsRate'),
                {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {}
                }
            );
        },
        get: function(){
            var vm = this;
            if(!vm.url) return;
            var url = vm.url;
            if( vm.ends_at ) {
                url += '?ends_at=' + vm.ends_at
            }
            var cb = vm[vm.getCb];
            if( !cb ) {
                cb = function(res){
                    vm.item = res
                    vm.itemLoaded = true;
                }
            }
            vm.reqGet(url, cb);
        },
    },
    mounted: function(){
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
    watch: {
        ends_at: function(newVal, oldVal) {
            this.debouncedGet();
        }
    },
});


/** Reporting GHG emissions (amount)
 */
Vue.component('reporting-ghg-emissions-amount', {
    mixins: [
        itemMixin
    ],
    props: [
        'ends_at'
    ],
    data: function(){
        return {
            url: this.$urls.api_reporting_ghg_emissions_amount,
            getCb: 'chart'
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            var labels = [];
            var datasets = [];
            var colors = [UTILITY_COLOR, EUISSCA_COLOR];
            for( var idx = 0; idx < resp.table.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.table[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        var label = moment(
                            resp.table[idx].values[valIdx][0]).format(
                                'YYYY-MM-DD');
                        labels.push(label);
                    }
                    data.push(resp.table[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.table[idx].key,
                    backgroundColor: colors[idx],
                    borderColor: colors[idx],
                    data: data
                });
            }
            if( vm.GHGEmissionsAmount ) {
                vm.GHGEmissionsAmount.destroy();
            }
            vm.GHGEmissionsAmount = new Chart(
                document.getElementById('GHGEmissionsAmount'),
                {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {}
                }
            );
        },
        get: function(){
            var vm = this;
            if(!vm.url) return;
            var url = vm.url;
            if( vm.ends_at ) {
                url += '?ends_at=' + vm.ends_at
            }
            var cb = vm[vm.getCb];
            if( !cb ) {
                cb = function(res){
                    vm.item = res
                    vm.itemLoaded = true;
                }
            }
            vm.reqGet(url, cb);
        },
    },
    mounted: function(){
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
    watch: {
        ends_at: function(newVal, oldVal) {
            this.debouncedGet();
        }
    },
});


Vue.component('active-reporting-entities', {
    mixins: [
        itemListMixin
    ],
    data: function(){
        return {
            url: this.$urls.api_active_reporting_entities,
        }
    },
    methods: {
    },
    mounted: function(){
        this.params.ends_at = null;
        this.get();
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
});


Vue.component('inactive-reporting-entities', {
    mixins: [
        itemListMixin
    ],
    data: function(){
        return {
            url: this.$urls.api_inactive_reporting_entities,
        }
    },
    methods: {
        showHideRoles: function(entry) {
            var vm = this;
            if( !entry.roles ) {
                vm.reqGet(vm._safeUrl(vm.$urls.api_organizations, entry.slug)
                    + '/roles',
                function success(resp) {
                    // Vue.set(entry, 'roles', [{printable_name: "Alice"}]);
                    Vue.set(entry, 'roles', resp.results);
                });
            }
        }
    },
    mounted: function(){
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    },
});
