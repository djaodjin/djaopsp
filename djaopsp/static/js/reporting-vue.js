// reporting components

var percentToggleMixin = {
    data: function() {
        var data = {
            percentToggle: 0,
            params: {
                unit: 'percentage'
            },
        }
        return data;
    },
    watch: {
        percentToggle: function(newVal, oldVal) {
            var vm = this;
            if( parseInt(newVal) > 0 ) {
                vm.params.unit = null;
            } else {
                vm.params.unit = 'percentage';
            }
        }
    }
};


/** Component to list, add and remove profiles that are currently invited
    to a campaign.
 */
Vue.component('engage-profiles', {
    mixins: [
        itemListMixin,
        percentToggleMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_portfolios_requests,
            api_profiles_base_url: this.$urls.api_organizations,
            typeaheadUrl: this.$urls.api_account_candidates,
            params: {
                o: 'full_name'
            },
            newItem: {
                email: "",
                full_name: "",
                type: "organization",
                printable_name: "",
                created_at: null
            },
            showContacts: -1,
            showRespondents: -1,
            showRecipients: -1,
            showEditTags: -1,
            message: this.$defaultRequestInitiatedMessage,
            getCb: 'loadComplete'
        }
    },
    methods: {
        hasNoReportingStatus: function(item) {
            return (typeof item.reporting_status === 'undefined') ||
                item.reporting_status === null;
        },
        reload: function() {
            var vm = this;
            vm.lastGetParams = vm.getParams();
            var typeaheadQueryString =
                '?o=full_name&q_f=full_name&q_f=email&q=' +
                vm.lastGetParams['q'];
            vm.reqMultiple([{
                method: 'GET', url: vm.url + vm.getQueryString(),
            },{
                method: 'GET', url: vm.typeaheadUrl + typeaheadQueryString,
            }], function(resp, typeaheadResp) {
                vm.loadComplete(resp[0], typeaheadResp[0]);
            });
        },
        populateInvite: function(newAccount) {
            var vm = this;
            if( newAccount.hasOwnProperty('slug') && newAccount.slug ) {
                vm.newItem.slug = newAccount.slug;
            }
            if( newAccount.hasOwnProperty('email') && newAccount.email ) {
                vm.newItem.email = newAccount.email;
            }
            if( !vm.newItem.email ) {
                if( newAccount.hasOwnProperty('contacts') ) {
                    if( newAccount.contacts.length > 0 ) {
                        vm.newItem.email = newAccount.contacts[0].user.email;
                    }
                }
            }
            if( newAccount.hasOwnProperty('printable_name')
                && newAccount.printable_name ) {
                vm.newItem.full_name = newAccount.printable_name;
            }
            if( newAccount.hasOwnProperty('full_name')
                && newAccount.full_name ) {
                vm.newItem.full_name = newAccount.full_name;
            }
            if( newAccount.hasOwnProperty('picture')
                && newAccount.picture ) {
                vm.newItem.picture = newAccount.picture;
            }
            if( newAccount.hasOwnProperty('created_at')
                && newAccount.created_at ) {
                vm.newItem.created_at = newAccount.created_at;
            }
        },
        requestAssessment: function(campaign) {
            var vm = this;
            var data = {
                accounts: [{}],
                message: vm.message,
            }
            // We remove the blank fields such that the backend serializer
            // does not complain that "the field is not required but when
            // present it shouldn't be blank".
            for( key in vm.newItem ) {
                if( vm.newItem.hasOwnProperty(key) &&  vm.newItem[key] ) {
                    data.accounts[0][key] = vm.newItem[key];
                }
            }
            if( typeof campaign !== 'undefined' ) {
                data['campaign'] = campaign;
            }
            if( !vm.newItem.slug ) {
                vm.reqPost(vm.$urls.api_account_candidates, vm.newItem,
                function(resp) {
                    vm.newItem = resp;
                    data.accounts = [vm.newItem];
                    vm.reqPost(vm.$urls.api_accessibles, data,
                    function success(resp) {
                        vm.get();
                    });
                });
            } else {
                vm.reqPost(vm.$urls.api_accessibles, data,
                function success(resp) {
                    vm.get();
                });
            }
            return false;
        },
        remove: function ($event, idx) {
            var vm = this;
            vm.reqDelete(vm._safeUrl(vm.$urls.api_accessibles,
                vm.items.results[idx].slug),
            function success(resp) {
                vm.get();
            });
        },
        loadComplete: function(resp, typeaheadResp) {
            var vm = this;
            vm.items = {count: resp.count, results: []};
            if( typeof typeaheadResp === 'undefined' ) {
                typeaheadResp = {count: 0, results: []};
            }
            var leftIdx = 0, rightIdx = 0;
            for(; leftIdx < typeaheadResp.results.length &&
                rightIdx < resp.results.length ;) {
                if( typeaheadResp.results[leftIdx].printable_name
                    < resp.results[rightIdx].printable_name ) {
                    vm.items.results.push(typeaheadResp.results[leftIdx]);
                    ++leftIdx;
                } else if( typeaheadResp.results[leftIdx].printable_name
                    > resp.results[rightIdx].printable_name ) {
                    vm.items.results.push(resp.results[rightIdx]);
                    ++rightIdx;
                } else {
                    // equal? we favor resp.
                    vm.items.results.push(resp.results[rightIdx]);
                    ++leftIdx;
                    ++rightIdx;
                }
            }
            for(; leftIdx < typeaheadResp.results.length; ++leftIdx ) {
                vm.items.results.push(typeaheadResp.results[leftIdx]);
            }
            for(; rightIdx < resp.results.length; ++rightIdx ) {
                vm.items.results.push(resp.results[rightIdx]);
            }
            vm.itemsLoaded = true;
        },
        toggleContacts: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showContacts = vm.showContacts === toggledIdx ? -1 : toggledIdx;
            if( vm.showContacts >= 0 ) {
                const api_roles_url = vm._safeUrl(vm.api_profiles_base_url,
                    [entry.slug, 'roles']);
                vm.reqGet(api_roles_url, function(resp) {
                    entry.contacts = resp.results;
                    entry.contacts.sort(function(a, b) {
                        if( a.user.last_login ) {
                            if( b.user.last_login ) {
                                if( a.user.last_login
                                    > b.user.last_login ) {
                                    return -1;
                                }
                                if( a.user.last_login
                                    < b.user.last_login ) {
                                    return 1;
                                }
                            } else {
                                return -1;
                            }
                        } else {
                            if( b.user.last_login ) {
                                return 1;
                            } else {
                            }
                        }
                        return 0;
                    });
                    vm.$forceUpdate();
                });
            }
        },
        toggleRespondents: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showRespondents = vm.showRespondents === toggledIdx ? -1 : toggledIdx;
            if( vm.showRespondents >= 0 ) {
                const api_roles_url = vm._safeUrl(vm.$urls.api_sample_base_url,
                    [entry.sample, 'respondents']);
                vm.reqGet(api_roles_url, function(resp) {
                    entry.respondents = resp.results;
                    entry.respondents.sort(function(a, b) {
                        if( a.last_login ) {
                            if( b.last_login ) {
                                if( a.last_login
                                    > b.last_login ) {
                                    return -1;
                                }
                                if( a.last_login
                                    < b.last_login ) {
                                    return 1;
                                }
                            } else {
                                return -1;
                            }
                        } else {
                            if( b.last_login ) {
                                return 1;
                            } else {
                            }
                        }
                        return 0;
                    });
                    vm.$forceUpdate();
                });
            }
        },
        toggleRecipients: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showRecipients = vm.showRecipients === toggledIdx ? -1 : toggledIdx;
            if( vm.showRecipients >= 0 ) {
                const api_roles_url = vm._safeUrl(vm.$urls.api_activities_base,
                    [entry.slug, 'recipients']);
                vm.reqGet(api_roles_url, function(resp) {
                    entry.recipients = resp.results;
                    entry.recipients.sort(function(a, b) {
                        if( a.user.last_login ) {
                            if( b.user.last_login ) {
                                if( a.user.last_login
                                    > b.user.last_login ) {
                                    return -1;
                                }
                                if( a.user.last_login
                                    < b.user.last_login ) {
                                    return 1;
                                }
                            } else {
                                return -1;
                            }
                        } else {
                            if( b.user.last_login ) {
                                return 1;
                            } else {
                            }
                        }
                        return 0;
                    });
                    vm.$forceUpdate();
                });
            }
        },
        saveTags: function(item) {
            var vm = this;
            if( !item.extra ) {
                item.extra = {}
            }
            item.extra.tags = item.tagsAsText.split(',');
            vm.reqPatch(vm._safeUrl(vm.$urls.api_accessibles, [
                'metadata', item.slug]), {extra: {tags: item.extra.tags}});
            vm.showEditTags = -1;
        },
        toggleEditTags: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showEditTags = vm.showEditTags === toggledIdx ? -1 : toggledIdx;
            if( vm.showEditTags >= 0 ) {
                if( !entry.tagsAsText ) {
                    try {
                        entry.tagsAsText = entry.extra.tags.join(", ");
                    } catch (err) {
                        entry.tagsAsText = "";
                    }
                }
            }
        }
    },
    mounted: function(){
        this.get();
    }
});


Vue.component('djaopsp-compare-samples', {
    mixins: [
        practicesListMixin
    ],
    data: function() {
        return {
            url: this.$urls.survey_api_compare_samples,
            params: {
                o: '-created_at'
            },
            newItem: {
                title: ''
            }
        }
    },
    methods: {
    },
});


Vue.component('reporting-organizations', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        var data = {
            url: this.$urls.api_portfolio_responses,
            portfolios_received_url: this.$urls.api_portfolios_received,
            api_profiles_base_url: this.$urls.api_organizations,
            params: {
                o: 'full_name' // XXX '-created_at' in old dashboard
            },
            newItem: {
                email: "",
                full_name: "",
                type: "organization",
                printable_name: "",
                created_at: null
            },
            message: this.$defaultRequestInitiatedMessage,
            grants: {
                count: 0,
                results: []
            },
            accountExtra: {
                supply_chain: false,
                reminder: false
            },
            autoreload: false,
            getCb: 'loadComplete',
            getCompleteCb: 'populateSummaryChart',
            showContacts: -1,
            showEditTags: -1,
        };
        if( this.$accountExtra ) {
            data.accountExtra = this.$accountExtra;
        }
        return data;
    },
    methods: {
        fetch: function(cb) {
            let vm = this;
            vm.lastGetParams = vm.getParams();
            if( vm.portfolios_received_url ) {
                vm.reqMultiple([{
                    method: 'GET', url: vm.url + vm.getQueryString(),
                },{
                    method: 'GET', url: vm.portfolios_received_url +
                        "?state=grant-initiated",
                }], function(resp, typeaheadResp) {
                    vm.loadComplete(resp[0], typeaheadResp[0]);
                });
            } else {
                vm.reqGet(vm.url, vm.lastGetParams, cb);
            }
        },
        getScoreDisplay: function(score) {
            return (score !== null) ? score.toString() + "%" : "";
        },
        accept: function(portfolio, idx) {
            var vm = this;
            vm.reqPost(portfolio.api_accept,
            function(resp) { // success
                vm.grants.results.splice(idx, 1);
                vm.params.q = portfolio.account;
                vm.filterList();
            });
        },
        ignore: function(portfolio, idx) {
            var vm = this;
            vm.reqDelete(portfolio.api_accept,
            function(resp) { // success
                vm.grants.results.splice(idx, 1);
            });
        },
        shortDate: function(at_time) {
            return moment(at_time).format("MMM D, YYYY");
        },
        loadComplete: function(resp, grantsResp) {
            var vm = this;
            if( vm.mergeResults ) {
                resp.results = vm.items.results.concat(resp.results);
            } else {
                vm.items = resp;
            }
            vm.grants = grantsResp;
            vm.itemsLoaded = true;
        },
        populateSummaryChart: function() {
            var vm = this;
            if( !vm.items.summary ) return;

            // populate the completion summary chart
            var labels = [];
            var datasets = [];
            var colors = [
                'red', '#ff5555', '#9CD76B', '#69B02B', '#007C3F', '#FFD700'];
            var summaryData = vm.items.summary;
            var data = [];
            for( var idx = 0; idx < summaryData.length; ++idx ) {
                labels.push(summaryData[idx][0] + " (" + summaryData[idx][1] + ")");
                data.push(summaryData[idx][1]);
            }
            datasets.push({
                label: "completed",
                backgroundColor: colors,
                data: data
            });
            if( vm.summaryChart ) {
                vm.summaryChart.destroy();
            }
            vm.summaryChart = new Chart(
                document.getElementById('summaryChart'),
                {
                    type: 'doughnut',
                    borderWidth: 0,
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        borderWidth: 1,
                        responsive: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'right',
                                labels: {
                                    boxWidth: 20,
                                    padding: 2,
                                    fontSize: 8,
                                }
                            }
                        }
                    }
                }
            );
        },
        addAccount: function(dataset, newAccount) {
            var vm = this;
            if( newAccount ) {
                if( newAccount.hasOwnProperty('slug') && newAccount.slug ) {
                    vm.newItem.slug = newAccount.slug;
                }
                console.log()
                if( newAccount.hasOwnProperty('email') && newAccount.email ) {
                    vm.newItem.email = newAccount.email;
                }
                if( newAccount.hasOwnProperty('printable_name')
                    && newAccount.printable_name ) {
                    vm.newItem.full_name = newAccount.printable_name;
                }
                if( newAccount.hasOwnProperty('full_name')
                    && newAccount.full_name ) {
                    vm.newItem.full_name = newAccount.full_name;
                }
                if( newAccount.hasOwnProperty('created_at')
                    && newAccount.created_at ) {
                    vm.newItem.created_at = newAccount.created_at;
                }
            }
            $("#invite-reporting-entity").modal("show");
        },
        requestAssessment: function(campaign) {
            var vm = this;
            vm.$refs.account.reset();
            var data = {
                accounts: [{}],
                message: vm.message,
            }
            for( key in vm.newItem ) {
                if( vm.newItem.hasOwnProperty(key) &&  vm.newItem[key] ) {
                    data.accounts[0][key] = vm.newItem[key];
                }
            }
            if( typeof campaign !== 'undefined' ) {
                data['campaign'] = campaign;
            }
            if( !vm.newItem.slug ) {
                vm.reqPost(vm.$urls.api_account_candidates, vm.newItem,
                function(resp) {
                    vm.newItem = resp;
                    data.accounts = [vm.newItem];
                    vm.reqPost(vm.$urls.api_accessibles, data,
                    function success(resp) {
                        vm.get();
                    });
                });
            } else {
                vm.reqPost(vm.$urls.api_accessibles, data,
                function success(resp) {
                    vm.get();
                });
            }
            return false;
        },
        remove: function ($event, idx) {
            var vm = this;
            vm.reqDelete(vm._safeUrl(vm.$urls.api_accessibles,
                vm.items.results[idx].slug),
            function success(resp) {
                vm.get();
            });
        },
        savePreferences: function() {
            var vm = this;
            var updated = true;
            vm.accountExtra['o'] = vm.params.o;
            vm.accountExtra['ot'] = vm.params.ot;
            if( vm.params.start_at ) {
                vm.accountExtra['start_at'] = vm.params.start_at;
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
        toggleContacts: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showContacts = vm.showContacts === toggledIdx ? -1 : toggledIdx;
            if( vm.showContacts >= 0 ) {
                const api_roles_url = vm._safeUrl(vm.api_profiles_base_url,
                    [entry.slug, 'roles']);
                vm.reqGet(api_roles_url, function(resp) {
                    entry.contacts = resp.results;
                    entry.contacts.sort(function(a, b) {
                        if( a.user.last_login ) {
                            if( b.user.last_login ) {
                                if( a.user.last_login
                                    > b.user.last_login ) {
                                    return -1;
                                }
                                if( a.user.last_login
                                    < b.user.last_login ) {
                                    return 1;
                                }
                            } else {
                                return -1;
                            }
                        } else {
                            if( b.user.last_login ) {
                                return 1;
                            } else {
                            }
                        }
                        return 0;
                    });
                    vm.$forceUpdate();
                });
            }
        },
        saveTags: function(item) {
            var vm = this;
            if( !item.extra ) {
                item.extra = {}
            }
            item.extra.tags = item.tagsAsText.split(',');
            vm.reqPatch(vm._safeUrl(vm.$urls.api_accessibles, [
                'metadata', item.slug]), {extra: {tags: item.extra.tags}});
            vm.showEditTags = -1;
        },
        toggleEditTags: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showEditTags = vm.showEditTags === toggledIdx ? -1 : toggledIdx;
            if( vm.showEditTags >= 0 ) {
                if( !entry.tagsAsText ) {
                    try {
                        entry.tagsAsText = entry.extra.tags.join(", ");
                    } catch (err) {
                        entry.tagsAsText = "";
                    }
                }
            }
        }
    },
    mounted: function(){
        this.get();
    }
});


Vue.component('activity-summary', {
    mixins: [
        paramsMixin,
        percentToggleMixin
    ],
    data: function() {
        return this.getInitData();
    },
    methods: {
        getInitData: function(){
            var data = {
                autoreload: false
            };
             return data;
        },
        filterList: function() {
            this.get();
        },
        get: function() {
            var vm = this;
            vm.lastGetParams = vm.getParams();
            for( let key in vm.$refs ) {
                vm.$refs[key].get();
            }
        }
    },
    mounted: function(){
        this.lastGetParams = this.getParams();
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

/** Common API call logic for dashboard charts
 */
var dashboardChart = Vue.component('dashboardChart', {
    mixins: [
        itemMixin
    ],
    props: [
        'params',
    ],
    data: function(){
        return {
            url: null,
            getCb: 'chart'
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
        },
        get: function(){
            var vm = this;
            if( !vm.url ) return;
            vm.itemLoaded = false;
            var url = vm.url + vm.getQueryString();
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
    computed: {
        _start_at: {
            get: function() {
                return this.asDateInputField(this.params.start_at);
            },
        },
        _ends_at: {
            get: function() {
                // form field input="date" will expect ends_at as a String
                // but will literally cut the hour part regardless of timezone.
                // We don't want an empty list as a result.
                // If we use moment `endOfDay` we get 23:59:59 so we
                // add a full day instead.
                const dateValue = moment(this.params.ends_at).add(1,'days');
                return dateValue.isValid() ? dateValue.format("YYYY-MM-DD") : null;
            },
        },
        _unit: function() {
            return this.params.unit;
        },
    },
    watch: {
        _unit: function(newVal, oldVal) {
            this.debouncedGet();
        }
    }
});


/** Reporting completion rate
 */
Vue.component('reporting-completion-rate', dashboardChart.extend({
    data: function(){
        return {
            url: this.$urls.api_reporting_completion_rate,
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
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        var label = moment(
                            resp.results[idx].values[valIdx][0]).format(
                                'YYYY-MM-DD');
                        labels.push(label);
                    }
                    data.push(resp.results[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.results[idx].slug,
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
    },
}));


Vue.component('reporting-completion-total', dashboardChart.extend({
    data: function(){
        return {
            url: this.$urls.api_portfolio_engagement_stats,
        }
    },
    methods: {
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            var labels = [];
            var datasets = [];
            var colors = ['#ff5555', '#9CD76B', '#69B02B'];
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.results[idx].values[valIdx][0]);
                    }
                    data.push(resp.results[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.results[idx].slug,
                    backgroundColor: colors,
                    data: data
                });
            }
            if( vm.completionRate ) {
                vm.completionRate.destroy();
            }
            vm.completionRate = new Chart(
                document.getElementById('summaryChart'),
                {
                    type: 'doughnut',
                    borderWidth: 0,
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        borderWidth: 1,
                        responsive: true,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'right',
                                labels: {
                                    boxWidth: 20,
                                    padding: 2,
                                    fontSize: 8,
                                }
                            }
                        }
                    }
                }
            );
        },
    },
}));


/** Reporting planned improvements and targets
 */
Vue.component('reporting-goals', dashboardChart.extend({
    data: function(){
        return {
            url: this.$urls.api_reporting_goals,
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
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.results[idx].values[valIdx][0]);
                    }
                    data.push(resp.results[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.results[idx].slug,
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
    },
}));


/** Reporting assessments completed by segments
 */
Vue.component('reporting-by-segments', dashboardChart.extend({
    data: function(){
        return {
            url: this.$urls.api_reporting_by_segments,
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
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.results[idx].values[valIdx][0]);
                    }
                    data.push(resp.results[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.results[idx].slug,
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
    },
}));


/** Reporting GHG emissions (%)
 */
Vue.component('reporting-ghg-emissions-rate', dashboardChart.extend({
    data: function(){
        return {
            url: this.$urls.api_reporting_ghg_emissions_rate,
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
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(resp.results[idx].values[valIdx][0]);
                    }
                    data.push(resp.results[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.results[idx].slug,
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
    },
}));


/** Reporting GHG emissions (amount)
 */
Vue.component('reporting-ghg-emissions-amount', dashboardChart.extend({
    data: function(){
        return {
            url: this.$urls.api_reporting_ghg_emissions_amount,
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
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        var label = moment(
                            resp.results[idx].values[valIdx][0]).format(
                                'YYYY-MM-DD');
                        labels.push(label);
                    }
                    data.push(resp.results[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: resp.results[idx].slug,
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
    },
}));


Vue.component('active-reporting-entities', {
    mixins: [
        itemListMixin
    ],
    data: function(){
        return {
            url: this.$urls.api_active_reporting_entities,
            messagesElement: '#active-reporting-entities-content',
            scrollToTopOnMessages: false,
        }
    },
    methods: {
    },
    mounted: function(){
        this.params.start_at = null;
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
