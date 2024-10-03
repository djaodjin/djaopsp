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

var portfolioTagsMixin = {
    data: function() {
        var initialData = {
            api_profile: this.$urls.api_profile,
            api_profiles_base_url: this.$urls.api_organizations,
            api_portfolio_metadata: this.$urls.api_portfolio_metadata,
            typeaheadUrl: this.$urls.api_account_candidates,
            showEditProfileKey: -1,
            showEditTags: -1,
            showPreferences: -1,
            preferenceTagsAsText: "",
            accountExtra: {},
        }
        if( this.$accountExtra ) {
            initialData.accountExtra = this.$accountExtra;
        }
        return initialData;
    },
    methods: {
        isSelectedTag: function(item, choice) {
            if( item.extra && item.extra.tags ) {
                for( let idx = 0; idx < item.extra.tags.length; ++idx ) {
                    if( choice === item.extra.tags[idx] ) return true;
                }
            }
            return false;
        },
        savePreferences: function() {
            var vm = this;
            vm.$set(vm.accountExtra, 'tags', vm.preferenceTagsAsText.split(','));
            vm.reqPatch(vm.$urls.api_profile, {
                extra: JSON.stringify(vm.accountExtra)});
        },
        getProfileKey: function(item, index) {
            var vm = this;
            if( item.extra && item.extra.supplier_key ) {
                return item.extra.supplier_key;
            }
            return index + 1 + (vm.params.page ? (vm.params.page - 1) * vm.itemsPerPage : 0);
        },
        saveProfileKey: function(item) {
            var vm = this;
            vm.reqPatch(vm._safeUrl(vm.api_portfolio_metadata, item.slug), {
                extra: item.extra});
            vm.showEditProfileKey = -1;
        },
        saveTags: function(item) {
            var vm = this;
            if( !item.extra ) {
                item.extra = {}
            }
            //XXXitem.extra.tags = item.tagsAsText.split(',');
            vm.reqPatch(vm._safeUrl(vm.api_portfolio_metadata, item.slug)
                + vm.getQueryString(), {extra: item.extra});
            vm.showEditTags = -1;
            vm.showPreferences = -1;
        },
        toggleEditProfileKey: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            if( vm.showEditProfileKey === toggledIdx ) {
                vm.saveProfileKey(entry);
            } else {
                if( !vm.items.results[toggledIdx].extra ) {
                    vm.items.results[toggledIdx].extra = {};
                }
                if( typeof vm.items.results[toggledIdx].extra === 'string' ) {
                    vm.items.results[toggledIdx].extra = JSON.parse(vm.items.results[toggledIdx].extra);
                }
                if( !vm.items.results[toggledIdx].extra.supplier_key ) {
                    vm.items.results[toggledIdx].extra.supplier_key = "";
                }
                vm.showEditProfileKey = toggledIdx;
            }
        },
        toggleEditTags: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            if( vm.showEditTags === toggledIdx ) {
                vm.saveTags(entry);
                vm.showEditTags = -1;
            } else {
                vm.showEditTags = vm.showEditTags = toggledIdx;
            }
            if( vm.showEditTags >= 0 ) {
                if( !entry.tagsAsText ) {
                    try {
                        entry.tagsAsText = entry.extra.tags.join(", ");
                    } catch (err) {
                        entry.tagsAsText = "";
                    }
                }
                vm.showPreferences = ( vm.tagChoices && vm.tagChoices.length === 0 ) ? 1 : -1;
            }
        },
        togglePreferences: function(toggleIdx) {
            var vm = this;
            vm.showPreferences = vm.showPreferences > 0 ? -1 : 1;
            if( !vm.preferenceTagsAsText ) {
                try {
                    vm.preferenceTagsAsText = vm.tagChoices.join(", ");
                } catch (err) {
                    vm.preferenceTagsAsText = "";
                }
            }
        }
    },
    computed: {
        tagChoices: function() {
            const vm = this;
            if( vm.accountExtra && vm.accountExtra.tags ) {
                return vm.accountExtra.tags;
            }
            return [];
        }
    }
};

/** Component to list, add and remove profiles that are currently invited
    to a campaign.
 */
Vue.component('engage-profiles', {
    mixins: [
        itemListMixin,
        percentToggleMixin,
        portfolioTagsMixin,
        accountDetailMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_portfolios_requests,
            api_profile: this.$urls.api_profile,
            api_profiles_base_url: this.$urls.api_organizations,
            typeaheadUrl: this.$urls.api_account_candidates,
            autoreload: false,
            params: {
                o: 'full_name',
                status: ''
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
            if( !vm.autoreload ) {
                for( let key in vm.$refs ) {
                    vm.$refs[key].get();
                }
            }
        },
        populateInvite: function(newAccount) {
            var vm = this;
            vm.newItem = {};
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
            if( !vm.newItem.email && vm.params.q &&
                vm.params.q.indexOf('@') > 0 ) {
                vm.newItem.email = vm.params.q;
            }
            if( newAccount.hasOwnProperty('printable_name')
                && newAccount.printable_name ) {
                vm.newItem.full_name = newAccount.printable_name;
            }
            if( newAccount.hasOwnProperty('full_name')
                && newAccount.full_name ) {
                vm.newItem.full_name = newAccount.full_name;
            }
            if( !vm.newItem.full_name && vm.params.q &&
                vm.params.q.indexOf('@') < 0 ) {
                vm.newItem.full_name = vm.params.q;
            }
            if( newAccount.hasOwnProperty('picture')
                && newAccount.picture ) {
                vm.newItem.picture = newAccount.picture;
            }
            if( newAccount.hasOwnProperty('created_at')
                && newAccount.created_at ) {
                vm.newItem.created_at = newAccount.created_at;
            }
            vm.params.q = "";
        },
        hideModal: function($event) {
            var form = jQuery($event.target);
            var modalDialog = form.parents('.modal');
            if( modalDialog ) modalDialog.modal('hide');
        },
        requestAssessment: function($event, campaign) {
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
                        const now = new Date(Date.now());
                        const endsAt = new Date(vm.params.ends_at);
                        if( isNaN(endsAt) || endsAt < now ) {
                            vm.params.ends_at = now.toISOString();
                        }
                        vm.params.q = vm.newItem.full_name;
                        vm.get();
                        vm.hideModal($event);
                    });
                });
            } else {
                vm.reqPost(vm.$urls.api_accessibles, data,
                function success(resp) {
                    const now = new Date(Date.now());
                    const endsAt = new Date(vm.params.ends_at);
                    if( isNaN(endsAt) || endsAt < now ) {
                        vm.params.ends_at = now.toISOString();
                    }
                    vm.params.q = vm.newItem.full_name;
                    vm.get();
                    vm.hideModal($event);
                });
            }
            return false;
        },
        remove: function ($event, idx) {
            var vm = this;
            if( vm.items.results[idx].api_remove ) {
                vm.reqDelete(vm.items.results[idx].api_remove,
                function success(resp) {
                    vm.get();
                });
            }
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
                let item = resp.results[rightIdx];
                if( !item.extra ) {
                    item.extra = {}
                }
                if( !item.extra.tags ) {
                    item.extra.tags = []
                }
                vm.items.results.push(item);
            }
            vm.populateAccounts(vm.items.results);
            vm.itemsLoaded = true;
        },
        toggleContacts: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showContacts = vm.showContacts === toggledIdx ? -1 : toggledIdx;
            if( vm.showContacts >= 0 ) {
                const api_roles_url = vm._safeUrl(vm.api_profiles_base_url,
                    [entry.slug, 'roles']);
                vm.reqGet(api_roles_url + "?role_status=active", function(resp) {
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
    },
    mounted: function(){
        this.get();
    }
});


Vue.component('djaopsp-compare-samples', {
    mixins: [
        practicesListMixin,
        accountDetailMixin
    ],
    data: function() {
        return {
            url: null,
            itemsLoaded: true,
            queryType: 'individual-account',
            datasets: [],
            getCompleteCb: 'firstDatasetLoaded',
            periodType: '',
            displayMetric: {
                path: null,
                unit: null
            },
            visualize: 'chart', //'table',
            percentToggle: true,

            // when clicking on Chart
            selectedDatapoint: "",
            selectedAccounts: []
        }
    },
    methods: {
        addDataset: function(dataset) {
            var vm = this;
            vm.itemsLoaded = false;
            vm.reqGet(dataset.url, function(resp) {
                dataset.results = resp.results;
                if( vm.datasets.length == 0 ) {
                    vm.items = resp;
                }
                vm.datasets.push(dataset);
                vm.itemsLoaded = true;
                vm.updateChart();
            });
        },
        firstDatasetLoaded: function() {
            var vm = this;
            vm.datasets[0].results = vm.items.results;
            vm.updateChart();
        },
        getBenchmarks: function(dataset, practice) {
            var vm = this;
            if( dataset.results && dataset.results.length > 0 ) {
                for( let idx = 0; idx < dataset.results.length; ++idx ) {
                    if( dataset.results[idx].path === practice.path ) {
                        return dataset.results[idx].benchmarks;
                    }
                }
            }
            return [];
        },
        getCompareAnswerMeasured: function(dataset, practice) {
            var vm = this;
            if( typeof dataset.results != 'undefined' && dataset.results.length > 0 ) {
                for( let idx = 0; idx < dataset.results.length; ++idx ) {
                    if( dataset.results[idx].path === practice.path ) {
                        return vm.getPrimaryAnswer(dataset.results[idx]).measured;
                    }
                }
            }
            return '-';
        },
        selectMetric: function(dataset, question) {
            var vm = this;
            vm.displayMetric = question;
        },
        activateSelectAccounts: function() {
            var vm = this;
            vm.$refs.accountsTab.click();
        },
        humanizePeriods: function(labels) {
            var vm = this;
            var results = [];
            const dateFormat = new Intl.DateTimeFormat(
                'en-US', {
                    //                            day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                });
            for( let lblIdx = 0; lblIdx < labels.length; ++lblIdx ) {
                const dtime = new Date(labels[lblIdx]);
                results.push(
                    vm.periodType == 'yearly' ? dtime.getUTCFullYear() : (
                    vm.periodType == 'monthly' ? dateFormat.format(dtime) : dtime));
            }
            return results;
        },
        onDatasetSelected: function() {
            // This method is called when the component needs to show
            // the list of accounts participating to a specific dataset.
            var vm = this;
            vm.populateAccounts(vm.selectedAccounts);
        },
        updateChart: function() {
            var vm = this;
            const entries = vm.getEntries(vm.displayMetric.path);
            for( var entIdx = 0; entIdx < entries.length; ++entIdx ) {
                const practice = entries[entIdx];
                var labels = [];      // labels on x-axis
                var choices = [];     // choices shown in each stack
                var datasets = [];
                var colors = ['#ff5555', '#9CD76B', '#69B02B'];
                for( var datIdx = 0; datIdx < vm.datasets.length; ++datIdx ) {
                    const dataset = vm.datasets[datIdx];
                    const benchmarks = vm.getBenchmarks(dataset, practice);
                    for( var benchIdx = 0; benchIdx < benchmarks.length; ++benchIdx ) {
                        for( var valIdx = 0;
                             valIdx < benchmarks[benchIdx].values.length;
                             ++valIdx ) {
                            // Add all labels first
                            var found = false;
                            for( var idx = 0; idx < labels.length; ++idx ) {
                                if( labels[idx] === benchmarks[benchIdx].values[valIdx][0] ) {
                                    found = true;
                                    break;
                                }
                            }
                            if( !found ) {
                                labels.push(benchmarks[benchIdx].values[valIdx][0]);
                            }
                            // Add choices
                            const valChoices
                                  = benchmarks[benchIdx].values[valIdx][1];
                            if( valChoices.length ) {
                                for( var chIdx = 0; chIdx < valChoices.length;
                                     ++chIdx ) {
                                    var found = false;
                                    const valKey = valChoices[chIdx][0];
                                    for( var idx = 0;
                                         idx < choices.length; ++idx ) {
                                        if( choices[idx] === valKey ) {
                                            found = true;
                                            break;
                                        }
                                    }
                                    if( !found ) {
                                        choices.push(valKey);
                                    }
                                }
                            }
                        }
                    }
                }

                // Build chart's datasets
                for( var datIdx = 0; datIdx < vm.datasets.length; ++datIdx ) {
                    const dataset = vm.datasets[datIdx];
                    const benchmarks = vm.getBenchmarks(dataset, practice);
                    for( var benchIdx = 0; benchIdx < benchmarks.length;
                         ++benchIdx ) {
                        const values = benchmarks[benchIdx].values;
                        if( choices.length ) {
                            // We are dealing with choices per period
                            for( var choiceIdx = 0; choiceIdx < choices.length;
                                 ++choiceIdx ) {
                                const choiceKey = choices[choiceIdx];
                                var data = [];
                                for( var lblIdx = 0; lblIdx < labels.length;
                                     ++lblIdx ) {
                                    var found = false;
                                    for( var valIdx = 0; valIdx < values.length;
                                         ++valIdx ) {
                                        if( labels[lblIdx] ===
                                            values[valIdx][0] ) {
                                            found = true;
                                            const valChoices =
                                                  values[valIdx][1];
                                            var foundChoice = false;
                                            for( var idx = 0;
                                                 idx < valChoices.length;
                                                 ++idx ) {
                                                if( valChoices[idx][0]
                                                    === choiceKey ) {
                                                    data.push(
                                                        valChoices[idx][1]);
                                                    foundChoice = true;
                                                    break;
                                                }
                                            }
                                            if( !foundChoice ) {
                                                data.push(0);
                                            }
                                            break;
                                        }
                                    }
                                    if( !found ) {
                                        data.push(0);
                                    }
                                }
                                console.assert(data.length === labels.length)
                                datasets.push({
                                    label: choices[choiceIdx], // choice
                                    backgroundColor: colors[choiceIdx],
                                    data: data,  // by account + by choice
                                    stack: benchmarks[benchIdx].slug // account title
                                });
                            }
                        } else { // if( choices.length )
                            var data = [];
                            for( var lblIdx = 0; lblIdx < labels.length;
                                 ++lblIdx ) {
                                var found = false;
                                for( var valIdx = 0; valIdx < values.length;
                                     ++valIdx ) {
                                    if( labels[lblIdx] === values[valIdx][0] ) {
                                        found = true;
                                        data.push(values[valIdx][1]);
                                        break;
                                    }
                                }
                                if( !found ) {
                                    data.push(0);
                                }
                            }
                            console.assert(data.length === labels.length)
                            datasets.push({
                                label: benchmarks[benchIdx].title, // label
                                backgroundColor: colors,
                                data: data,  // by account + by label
                            });
                        }  // if( choices.length )
                    } // benchIdx
                } // vm.datasets

                if( vm.compareChart ) {
                    vm.compareChart.destroy();
                }
                labels = vm.humanizePeriods(labels);
                if( choices.length ) {
                    vm.compareChart = new Chart(
                        document.getElementById('summaryChart'), {
                            type: 'bar',
                            borderWidth: 0,
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {
                                borderWidth: 1,
                                responsive: true,
                                maintainAspectRatio: false,
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
                                },
                                scales: {
                                    x: {
                                        stacked: true,
                                    },
                                    y: {
                                        stacked: true
                                    }
                                }
                            }
                        }
                    );
                } else {
                    vm.compareChart = new Chart(
                        document.getElementById('summaryChart'), {
                            type: 'doughnut',
                            borderWidth: 0,
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {
                                borderWidth: 1,
                                responsive: true,
                                maintainAspectRatio: false,
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
                } // /type of chart
            } // /entries
        },
    },
    computed: {
        datasetLoading: function() {
            return this.datasets.length > 0 && !this.itemsLoaded;
        },
        circleLabels: function() {
            const vm = this;
            let text = "";
            let sep = "";
            for( var datIdx = 0; datIdx < vm.datasets.length; ++datIdx ) {
                const dataset = vm.datasets[datIdx];
                const benchmarks = vm.getBenchmarks(dataset, vm.displayMetric);
                for( let idx = 0; idx  < benchmarks.length; ++idx ) {
                    text += (sep + benchmarks[idx].title);
                    sep = ", ";
                }
            }
            return text;
        }
    },
    mounted: function(){
        // XXX Does not override `practicesListMixin.mounted`
    }
});


Vue.component('query-accounts-by-extended-affinity', QueryAccountsByAffinity.extend({
    data: function() {
        return {
            plans_url: this.$urls.api_plans,
            subscriptions_url: this.$urls.api_subscriptions,
            plans: [],
            alliances: []
        }
    },
    methods: {
        validate: function() {
            var vm = this;
            if( vm.affinityType === 'engaged' ||
                vm.affinityType === 'accessibles' ||
                vm.affinityType === 'all') {
                const dataset = vm._getAffinityBaseDataset();
                vm.$emit('updatedataset', dataset);
            } else {
                console.log("XXX use affinityType=", vm.affinityType);
                const dataset = vm._getAffinityBaseDataset('all'); // XXX use plan
                vm.$emit('updatedataset', dataset);
            }
        },
    },
    mounted: function() {
        var vm = this;
        vm.reqGet(vm.plans_url, function(resp) {
            vm.plans = resp.results;
        });
        vm.reqGet(vm.subscriptions_url, function(resp) {
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                vm.alliances.push(resp.results[idx].plan);
            }
        });
    }
}));


Vue.component('reporting-organizations', {
    mixins: [
        itemListMixin,
        portfolioTagsMixin,
        accountDetailMixin
    ],
    data: function() {
        var data = {
            url: this.$urls.api_portfolio_responses,
            portfolios_received_url: this.$urls.api_portfolios_received,
            api_profiles_base_url: this.$urls.api_organizations,
            params: {
                period: 'yearly'
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
        };
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
                vm.populateAccounts(resp.results);
                vm.items.results = vm.items.results.concat(resp.results);
            } else {
                vm.items = resp;
                vm.populateAccounts(vm.items.results);
            }
            if( grantsResp ) {
                vm.grants = grantsResp;
                vm.populateAccounts(vm.grants.results, 'account');
            }
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
            vm.reqDelete(vm._safeUrl(vm.url, vm.items.results[idx].slug),
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
            vm.accountExtra.tags = vm.preferenceTagsAsText.split(',');
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
        var data = {
            params: {
                unit: 'percentage',
                start_at: null,
                ends_at: null,
                // The timezone for both start_at and ends_at.
                timezone: 'local'
            },
        }
        if( this.$dateRange ) {
            if( this.$dateRange.start_at ) {
                data.params['start_at'] = this.$dateRange.start_at;
            }
            if( this.$dateRange.ends_at ) {
                data.params['ends_at'] = this.$dateRange.ends_at;
            }
            if( this.$dateRange.timezone ) {
                data.params['timezone'] = this.$dateRange.timezone;
            }
        }
        return data;
    },
    methods: {
        filterList: function() {
            this.get();
        },
        get: function() {
            var vm = this;
            vm.lastGetParams = vm.getParams();
            for( let key in vm.$refs ) {
                vm.$refs[key].get();
            }
        },
        reload: function() {
            this.get();
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
        httpRequestMixin
    ],
    props: [
        'params',
    ],
    data: function(){
        return {
            datasets: [],
            itemLoaded: false,
            loadError: null,
        }
    },
    methods: {
        chart: function(resp) {
            // override in subclasses
        },
        get: function(){
            var vm = this;
            if( !vm.datasets.length ) {
                vm.loadError = "No URL specified";
                vm.itemLoaded = true;
                return;
            }
            var queryArray = [];
            for( let idx = 0; idx < vm.datasets.length; ++idx ) {
                if( vm.datasets[idx].url ) {
                    queryArray.push({
                        method: 'GET',
                        url: vm.datasets[idx].url + vm.getQueryString(),
                        data: null
                    });
                }
            }

            vm.loadError = null;
            vm.itemLoaded = false;
            vm.reqMultiple(queryArray, function(resp) {
                vm.datasets[0].results = resp.results;
                vm.chart(resp);
                vm.itemLoaded = true;
            }, function(resp) {
                vm.loadError = "" + resp.status + " - " + resp.statusText;
                vm.itemLoaded = true;
            });
        },
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
        circleLabels: function() {
            const vm = this;
            let text = "";
            let sep = "";
            for( var datIdx = 0; datIdx < vm.datasets.length; ++datIdx ) {
                const dataset = vm.datasets[datIdx];
                const benchmarks = (dataset.results &&
                    dataset.results.length > 0) ? dataset.results[0].benchmarks
                    : [];
                for( let idx = 0; idx  < benchmarks.length; ++idx ) {
                    text += (sep + benchmarks[idx].title);
                    sep = ", ";
                }
            }
            return text;
        }
    },
    watch: {
        _unit: function(newVal, oldVal) {
            this.debouncedGet();
        },
    },
    mounted: function(){
        if( this.$el.dataset && this.$el.dataset.url ) {
            this.datasets.push({
                url: this.$el.dataset.url,
                slug: null,
                title: null,
                results: null
            });
        }
        this.get()
    },
    created: function () {
        // _.debounce is a function provided by lodash to limit how
        // often a particularly expensive operation can be run.
        this.debouncedGet = _.debounce(this.get, 500)
    }
});


/** Reporting a question aggregated answers by choice
 */
Vue.component('reporting-benchmarks', dashboardChart.extend({
    data: function(){
        return {
            charts: {},
        }
    },
    methods: {
        getRates: function(benchmark) {
            var vm = this;
            var results = [];
            if( typeof benchmark.values !== 'undefined' ) {
                if( vm._isArray(benchmark.values[0][1]) ) {
                    return benchmark.values[0][1];
                }
                return benchmark.values;
            }
            return results;
        },
        chart: function(resp) {
            var vm = this;
            vm.item = resp;
            vm.itemLoaded = true;
            // Recover memory for previous charts, and prevent cached data
            // to show up when it shouldn't.
            for( var key in vm.charts ){
                if( vm.charts.hasOwnProperty(key) ){
                    vm.charts[key].destroy();
                    delete vm.charts[key];
                }
            }
            var labelset = new Set();
            var datasets = [];
            var colors = [
                [UTILITY_COLOR, UTILITY_COLOR_LAST],
                [EUISSCA_COLOR, EUISSCA_COLOR_LAST]];
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                const benchmarks = resp.results[idx].benchmarks;
                // Series might not have exactly the same labels. Thus we need
                // to gather all defined labels first.
                for( var benchIdx = 0;
                     benchIdx < benchmarks.length; ++benchIdx ) {
                    const rates = vm.getRates(benchmarks[benchIdx]);
                    for( var valIdx = 0; valIdx < rates.length; ++valIdx ) {
                        labelset.add(rates[valIdx][0]);
                    }
                }
                const labels = Array.from(labelset).sort();
                // Make sure we have a value for each label before
                // adding serie.
                for( var benchIdx = 0;
                     benchIdx < benchmarks.length; ++benchIdx ) {
                    var dict = {};
                    const rates = vm.getRates(benchmarks[benchIdx]);
                    for( var valIdx = 0; valIdx < rates.length; ++valIdx ) {
                        dict[rates[valIdx][0]] = rates[valIdx][1];
                    }
                    var data = [];
                    for( var lblIdx = 0; lblIdx < labels.length; ++lblIdx ) {
                        const val = dict[labels[lblIdx]];
                        if( val ) {
                            data.push(val);
                        } else {
                            data.push(0);
                        }
                    }
                    datasets.push({
                        label: benchmarks[benchIdx].slug,
                        backgroundColor: colors[benchIdx],
                        data: data
                    });
                }
                var chartKey = resp.results[idx].path;
                var chart = vm.charts[chartKey];
                if( chart ) {
                    chart.destroy();
                }
                var element = vm.$refs.canvas;
                if( element ) {
                    if( resp.results[idx].default_unit &&
                        resp.results[idx].default_unit.system == "datetime" ) {
                        vm.charts[chartKey] = new Chart(element, {
                            type: 'bar',
                            data: {
                                labels: labels,
                                datasets: datasets
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
                                    },
                                }
                            },
                        });
                    } else {
                        vm.charts[chartKey] = new Chart(element, {
                            type: 'doughnut',
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {}
                        });
                    }
                }
            }
        },
    },
}));


/** Reporting completion rate
 */
Vue.component('reporting-completion-rate', dashboardChart.extend({
    data: function(){
        return {
            datasets: [{
                url: this.$urls.api_reporting_completion_rate
            }]
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
            datasets: [{
                url: this.$urls.api_portfolio_engagement_stats
            }]
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
    computed: {
        circleLabels: function() {
            const vm = this;
            let text = "";
            for( let idx = 1; idx  < vm.item.results.length; ++idx ) {
                text += ', ' + vm.item.results[idx].title
            }
            return text;
        }
    }
}));


/** Reporting planned improvements and targets
 */
Vue.component('reporting-goals', dashboardChart.extend({
    data: function(){
        return {
            datasets: [{
                url: this.$urls.api_reporting_goals
            }]
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
            datasets: [{
                url: this.$urls.api_reporting_by_segments,
            }]
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
            datasets: [{
                url: this.$urls.api_reporting_ghg_emissions_rate,
            }]
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
            datasets: [{
                url: this.$urls.api_reporting_ghg_emissions_amount,
            }]
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


Vue.component('practice-typeahead', QuestionTypeahead.extend({
  methods: {
      indentHeader: function(practice) {
          var vm = this;
          var indentSpace = practice.indent > 0 ? (practice.indent - 1) : 0;
          if( vm.isPractice(practice) ) {
              return "bestpractice indent-header-" + indentSpace;
          }
          return "heading-" + indentSpace + " indent-header-" + indentSpace;
      },
      isPractice: function(practice) {
          var vm = this;
          if( typeof practice.default_unit !== "undefined" ) {
              return practice.default_unit !== null;
          }
          return false;
      },
  }
}));
