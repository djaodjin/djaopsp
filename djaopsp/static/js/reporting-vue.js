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
            api_metadata: this.$urls.api_metadata,
            api_portfolio_metadata: this.$urls.api_portfolio_metadata,
            typeaheadUrl: this.$urls.api_account_candidates,
            showEditProfileKey: -1,
            showEditTags: -1,
            tagsTagify: null,
            accountExtra: {},
        }
        if( this.$accountExtra ) {
            initialData.accountExtra = this.$accountExtra;
        }
        return initialData;
    },
    methods: {
        updateTagChoices: function(tags) {
            var vm = this;
            var choices = vm.accountExtra?.tags?.slice() || [];
            var before = choices.length;
            for( var i = 0; i < tags.length; ++i ) {
                if( choices.indexOf(tags[i]) === -1 ) {
                    choices.push(tags[i]);
                }
            }
            if( choices.length > before ) {
                vm.$set(vm.accountExtra, 'tags', choices);
                vm.reqPatch(vm.$urls.api_profile || vm.$urls.api_organization_profile, {
                    extra: JSON.stringify(vm.accountExtra)});
            }
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
            vm.reqPatch(vm._safeUrl(vm.api_metadata, item.slug)
                + vm.getQueryString(), {extra: item.extra});
            vm.showEditTags = -1;
        },
        searchByTag: function(tag) {
            var vm = this;
            if( vm.tagify ) {
                vm.tagify.addTags([tag], false, true);
            } else {
                vm.params.q = tag;
                vm.reload();
            }
        },
        toggleEditProfileKey: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            if( vm.showEditProfileKey === toggledIdx ) {
                vm.saveProfileKey(entry);
            } else {
                if( vm.showEditTags >= 0 ) {
                    vm.blurEditTags(vm.showEditTags);
                }
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
                vm.$nextTick(function() {
                    if( vm.$refs.profileKeyInput ) {
                        vm.$refs.profileKeyInput[0].focus();
                    }
                });
            }
        },
        toggleEditTags: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            if( vm.showEditTags === toggledIdx ) {
                if( vm.tagsTagify ) {
                    if( !entry.extra ) { entry.extra = {}; }
                    entry.extra.tags = vm.tagsTagify.value.map(
                        function(item) { return item.value; });
                    vm.tagsTagify.destroy();
                    vm.tagsTagify = null;
                }
                vm.saveTags(entry);
                vm.updateTagChoices(entry.extra.tags);
                vm.showEditTags = -1;
            } else {
                if( vm.showEditProfileKey >= 0 ) {
                    vm.toggleEditProfileKey(vm.showEditProfileKey);
                }
                vm.showEditTags = toggledIdx;
                var inputEl = vm.$refs.tagsInput[toggledIdx];
                inputEl.value = entry.extra?.tags?.join(',') || '';
                vm.tagsTagify = new Tagify(inputEl, {
                    whitelist: vm.tagChoices,
                    dropdown: {
                        enabled: 0
                    }
                });
                vm.tagsTagify.DOM.scope.addEventListener('mousedown', function(e) {
                    if( !vm.tagsTagify.DOM.input.contains(e.target) ) {
                        e.preventDefault();
                    }
                });
                vm.tagsTagify.on('blur', function() {
                    vm.blurEditTags(toggledIdx);
                });
                vm.$nextTick(function() {
                    vm.tagsTagify.DOM.input.focus();
                });
            }
        },
        blurEditTags: function(idx) {
            var vm = this;
            if( vm.showEditTags === idx ) {
                vm.toggleEditTags(idx);
            }
        },
        cancelEditTags: function(idx) {
            var vm = this;
            if( vm.showEditTags !== idx ) return;
            if( vm.tagsTagify ) {
                vm.tagsTagify.destroy();
                vm.tagsTagify = null;
            }
            vm.showEditTags = -1;
        },
    },
    computed: {
        tagChoices: function() {
            var vm = this;
            var allTags = vm.accountExtra?.tags?.slice() || [];
            if( vm.items && vm.items.results ) {
                for( var i = 0; i < vm.items.results.length; ++i ) {
                    var entry = vm.items.results[i];
                    if( entry.extra?.tags ) {
                        for( var j = 0; j < entry.extra.tags.length; ++j ) {
                            if( allTags.indexOf(entry.extra.tags[j]) === -1 ) {
                                allTags.push(entry.extra.tags[j]);
                            }
                        }
                    }
                }
            }
            return allTags;
        }
    }
};

var DoughnutLinesPlugin = {
    id: 'doughnutLines',
    afterDraw: function(chart) {
        if( chart.config.type !== 'doughnut' ) return;
        var ctx = chart.ctx;
        chart.data.datasets.forEach(function(dataset, di) {
            var meta = chart.getDatasetMeta(di);
            meta.data.forEach(function(arc, i) {
                if( dataset.data[i] <= 0 ) return;
                var midAngle = (arc.startAngle + arc.endAngle) / 2;
                var dlOpts = chart.options.plugins.datalabels;
                var labelOffset = dlOpts.offset || 0;
                var labelBorder = dlOpts.borderWidth || 0;
                var labelPadding = dlOpts.padding || 0;
                var bw = arc.options.borderWidth || 0;
                var startR = arc.outerRadius - Math.floor(bw / 2);
                var endR = arc.outerRadius + labelOffset + labelBorder + labelPadding;
                ctx.beginPath();
                ctx.moveTo(
                    arc.x + Math.cos(midAngle) * startR,
                    arc.y + Math.sin(midAngle) * startR
                );
                ctx.lineTo(
                    arc.x + Math.cos(midAngle) * endR,
                    arc.y + Math.sin(midAngle) * endR
                );
                var bg = dataset.backgroundColor;
                ctx.strokeStyle = Array.isArray(bg) ? bg[i] : bg;
                ctx.lineWidth = 1;
                ctx.stroke();
            });
        });
    }
};

// generate distinct colors using golden angle.
function goldenAngleColor(index, offset) {
    var hue = ((offset || 0) + index * 137) % 360;
    return 'hsl(' + hue + ', 65%, 50%)';
}

function getChartColor(index, unitSystem) {
    var colors = [EUISSCA_COLOR, UTILITY_COLOR];
    if( index < 0 ) {
        return NO_RESPONSE_COLOR;
    }
    if( unitSystem === 'datetime' ) {
        return goldenAngleColor(index);
    }
    if( index < colors.length ) {
        return colors[index];
    }
    // offset 200 (blue) to avoid green (~120)
    // and amber (~40) already in colors.
    return goldenAngleColor(index, 200);
}

var baseDatalabelsConfig = {
    backgroundColor: function(context) {
        var bg = context.dataset.backgroundColor;
        return Array.isArray(bg) ? bg[context.dataIndex] : bg;
    },
    borderColor: 'white',
    borderRadius: 25,
    borderWidth: 2,
    color: 'white',
    font: {
        weight: 'bold',
    },
    padding: 6,
    display: function(context) {
        var dataset = context.dataset;
        var value = dataset.data[context.dataIndex];
        return value > 0;
    }
};

function unitFormatter(unit) {
    return function(value) {
        var rounded = Math.round(value);
        if( unit === 'percentage' ) {
            return rounded + '%';
        }
        return rounded < 10 ? ' ' + rounded + ' ' : rounded;
    };
}

function unitTooltip(unit) {
    return {
        boxPadding: 6,
        callbacks: {
            label: function(context) {
                var isDoughnut = typeof context.parsed === 'number';
                var label = isDoughnut
                    ? (context.label || '')
                    : (context.dataset.label || '');
                var value = Math.round(context.raw);
                if( unit === 'percentage' ) {
                    return label + ': ' + value + '%';
                }
                return label + ': ' + value;
            }
        }
    };
}

function doughnutLabelFormatter(unit) {
    return function(value, context) {
        var label = context.chart.data.labels[context.dataIndex];
        if( label.length > 12 ) {
            label = label.substring(0, 10) + '...';
        }
        var rounded = Math.round(value);
        if( unit === 'percentage' ) {
            return rounded + '% ' + label;
        }
        return rounded + ' ' + label;
    };
}

function buildChartColors(labels, unit) {
    var unitSystem = unit ? unit.system : null;
    var indexByLabel = {};
    // ordered by rank on the backend, so it's safe to rely on index
    if( unit && unit.choices ) {
        for( var ci = 0; ci < unit.choices.length; ++ci ) {
            indexByLabel[unit.choices[ci].text] = ci;
        }
    }
    var bgColors = [];
    for( var li = 0; li < labels.length; ++li ) {
        var colorIdx = indexByLabel[labels[li]];
        if( colorIdx === undefined ) {
            colorIdx = labels[li] !== 'No response' ? li : -1;
        }
        bgColors.push(getChartColor(colorIdx, unitSystem));
    }
    return bgColors;
}

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
                created_at: null,
                ends_at: null
            },
            showContacts: -1,
            showRespondents: -1,
            showRecipients: -1,
            tagify: null,
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
                '?o=full_name&q_f=full_name';
            if( vm.lastGetParams['q'] ) {
                // The search fields should match ones specified
                // in `get_engaged_accounts`.
                if( vm.lastGetParams['q'].indexOf('@') !== -1 ) {
                    typeaheadQueryString += '&q_f=email';
                }
                typeaheadQueryString += ('&q=' + vm.lastGetParams['q']);
            }
            vm.reqMultiple([{
                method: 'GET', url: vm.url + vm.getQueryString(),
            },{
                method: 'GET', url: vm.typeaheadUrl + typeaheadQueryString,
            }], function(resp, typeaheadResp) {
                vm.loadComplete(resp, typeaheadResp);
            });
            if( !vm.autoreload ) {
                for( let key in vm.$refs ) {
                    vm.$refs[key].get();
                }
            }
        },
        populateInvite: function(newAccount) {
            var vm = this;
            clearMessages();
            vm.newItem = {ends_at: null};
            if( newAccount.hasOwnProperty('slug') && newAccount.slug ) {
                vm.newItem.slug = newAccount.slug;
            }
            const email = vm.getAccountField(newAccount, 'email');
            if( email ) {
                vm.newItem.email = email;
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
            if( newAccount.hasOwnProperty('expires_at') ) {
                vm.newItem.ends_at = newAccount.expires_at;
            }
            vm.params.q = "";
        },
        populateInviteExample: function(email) {
            var vm = this;
            vm.newItem = {
                isExample: true,
                slug: 'supplier-1',
                ends_at: null,
                email: email
            };
        },
        hideModal: function($event) {
            var form = jQuery($event.target);
            var modalDialog = form.parents('.modal');
            if( modalDialog ) modalDialog.modal('hide');
        },
        requestAssessment: function($event, campaign) {
            var vm = this;
            function handleError(resp) {
                var errorResp = resp;
                var data = resp.data || resp.responseJSON;
                if( data ) {
                    var flat = data;
                    if( data.accounts?.length > 0 ) {
                        var {accounts, ...rest} = data;
                        flat = {...rest, ...accounts[0]};
                    }
                    if( flat.recipients && typeof flat.recipients === 'object' ) {
                        var emailErrors = flat.email || [];
                        for( var idx in flat.recipients ) {
                            if( flat.recipients.hasOwnProperty(idx) ) {
                                flat.recipients[idx].forEach(function(msg) {
                                    emailErrors.push(
                                        `Email ${parseInt(idx) + 2}: ${msg}`);
                                });
                            }
                        }
                        flat.email = emailErrors;
                        delete flat.recipients;
                    }
                    errorResp = {responseJSON: flat};
                }
                showErrorMessages(errorResp);
            }
            var data = {
                accounts: [{}],
                message: vm.message,
                ends_at: vm.newItem.ends_at
            }
            // We remove the blank fields such that the backend serializer
            // does not complain that "the field is not required but when
            // present it shouldn't be blank".
            for( key in vm.newItem ) {
                if( vm.newItem.hasOwnProperty(key) &&  vm.newItem[key] ) {
                    data.accounts[0][key] = vm.newItem[key];
                }
            }
            if( data.accounts[0].email ) {
                var emails = data.accounts[0].email
                    .split(',').map(function(e) { return e.trim(); })
                    .filter(function(e) { return e; });
                if( emails.length > 0 ) {
                    data.accounts[0].email = emails[0];
                    data.accounts[0].recipients = emails.slice(1);
                } else {
                    showErrorMessages({responseJSON: {
                        email: ["Enter a valid email address."]}});
                    return;
                }
            }
            if( typeof campaign !== 'undefined' ) {
                data['campaign'] = campaign;
            }
            if( vm.newItem.isExample ) {
                vm.reqPost(vm._safeUrl(vm.$urls.api_accessibles, 'send'), data,
                function success(resp, textStatus, jqXHR) {
                    showMessages(resp.detail, 'info');
                    vm.hideModal($event);
                }, handleError);
            } else {
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
                            if( vm.params.page ) vm.params.page = 1;
                            vm.params.q = vm.newItem.full_name;
                            vm.get();
                            vm.hideModal($event);
                        });
                    });
                } else {
                    vm.reqPost(vm.$urls.api_accessibles, data,
                    function success(resp, textStatus, jqXHR) {
                        if( jqXHR.status == 201 ) {
                            // Check for 201 so we don't reload the page
                            // when re-sending the request.
                            const now = new Date(Date.now());
                            const endsAt = new Date(vm.params.ends_at);
                            if( isNaN(endsAt) || endsAt < now ) {
                                vm.params.ends_at = now.toISOString();
                            }
                            if( vm.params.page ) vm.params.page = 1;
                            vm.params.q = vm.newItem.full_name;
                            vm.get();
                        } else {
                            // Since we do not reload the items, we need
                            // to update the deadline for response.
                            for( let idx = 0; idx < vm.items.results.length;
                                 ++idx ) {
                                if( vm.items.results[idx].slug
                                    == vm.newItem.slug ) {
                                    vm.items.results[idx].expires_at =
                                        vm.newItem.ends_at;
                                    break;
                                }
                            }
                        }
                        vm.hideModal($event);
                    }, handleError);
                }
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
                if( !item.extra.portfolio_tags ) {
                    item.extra.portfolio_tags = []
                }
                vm.items.results.push(item);
            }
            vm.populateAccounts(vm.items.results);
            if( vm.tagify ) {
                vm.tagify.whitelist = vm.tagChoices;
            }
            vm.itemsLoaded = true;
        },
        toggleContacts: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showContacts = vm.showContacts === toggledIdx ? -1 : toggledIdx;
            if( vm.showContacts >= 0 ) {
                const api_roles_url = vm._safeUrl(vm._safeUrl(
                    vm.api_profiles_base_url, entry.slug), 'roles');
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
                    // Marks the primary contact as such
                    var found = false;
                    const email = vm.getAccountField(entry, 'email');
                    for( var idx = 0; idx < entry.contacts.length; ++idx ) {
                        if( entry.contacts[idx].user.email === email ) {
                            entry.contacts[idx].role_description = {
                                slug: 'manager',
                                title: "Primary contact"
                            };
                            found = true;
                        }
                    }
                    if( !found ) {
                        entry.contacts.push({
                            role_description: {
                                slug: 'manager',
                                title: "Primary contact"
                            },
                            user: {
                                email: email
                            }
                        });
                    }
                    vm.$forceUpdate();
                });
            }
        },
        toggleRespondents: function(toggledIdx) {
            var vm = this;
            var entry = vm.items.results[toggledIdx];
            vm.showRespondents = vm.showRespondents === toggledIdx ? -1 : toggledIdx;
            if( vm.showRespondents >= 0 ) {
                const api_roles_url = vm._safeUrl(vm._safeUrl(
                    vm.$urls.api_sample_base_url, entry.sample), 'respondents');
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
                const api_roles_url = vm._safeUrl(vm._safeUrl(
                    vm.$urls.api_activities_base, entry.slug), 'recipients');
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
    computed: {
        _expires_at: {
            get: function() {
                if( this.newItem.ends_at ) {
                    return this.asDateInputField(this.newItem.ends_at);
                }
                return null;
            },
            set: function(newVal) {
                if( newVal ) {
                    // The setter might be call with `newVal === null`
                    // when the date is incorrect (ex: 09/31/2022).
                    this.$set(this.newItem, 'ends_at',
                        this.asDateISOString(newVal));
                } else {
                    this.$set(this.newItem, 'ends_at', null);
                }
            }
        },
    },
    mounted: function(){
        var vm = this;
        vm.get();
        if( vm.$refs.tagFilter && typeof Tagify !== 'undefined' ) {
            vm.tagify = new Tagify(vm.$refs.tagFilter, {
                whitelist: vm.tagChoices || [],
                dropdown: {
                    enabled: 1
                }
            });
            vm.tagify.DOM.input.setAttribute('aria-label', 'Search');
            vm.tagify.on('change', function() {
                var tags = vm.tagify.value.map(
                    function(item) { return item.value; });
                vm.params.q = tags.join(',');
                vm.reload();
            });
        }
    }
});


/** The 'djaopsp-compare-samples' component is used for both,
    the compare.html and analyze.html views.
 */
Vue.component('djaopsp-compare-samples', {
    mixins: [
        practicesListMixin, // defines `_start_at` and `_ends_at`
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
                unit: null,
                campaign: null
            },
            visualize: 'chart', //'table',
            percentToggle: true,

            samplesBySlug: {},
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
                    // If we don't make a copy, adding missing practices
                    // from another dataset will also add answers from that
                    // additional dataset to the initial dataset loaded.
                    vm.items = JSON.parse(JSON.stringify(resp));
                } else {
                    for( let unit in resp.units ) {
                        if( resp.units.hasOwnProperty(unit) ) {
                            if( !vm.items.units[unit] ) {
                                vm.items.units[unit] = resp.units[unit];
                            }
                        }
                    }
                    // We might have practices in the additional dataset which
                    // are not in previous datasets. We thus extend the set
                    // of practices.
                    let newIdx = 0;
                    let curIdx = 0;
                    while( newIdx < resp.results.length &&
                         curIdx < vm.items.results.length ) {
                        if( resp.results[newIdx].slug ==
                            vm.items.results[curIdx].slug ) {
                            ++curIdx;
                        } else {
                            let found = false;
                            for( let idx = curIdx;
                                 idx < vm.items.results.length; ++idx ) {
                                if( resp.results[newIdx].slug ==
                                    vm.items.results[idx].slug ) {
                                    found = true;
                                    break;
                                }
                            }
                            if( !found ) {
                                vm.items.results.splice(
                                    curIdx, 0, resp.results[newIdx]);
                                ++curIdx;
                            }
                        }
                        ++newIdx;
                    }
                    if( newIdx < resp.results.length ) {
                        vm.items.results.push(...resp.results.slice(newIdx));
                    }
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
            const path = ( typeof practice.path !== 'undefined' ) ?
                  practice.path : practice;
            if( dataset.results && dataset.results.length > 0 ) {
                for( let idx = 0; idx < dataset.results.length; ++idx ) {
                    if( dataset.results[idx].path === path ) {
                        return dataset.results[idx].benchmarks || [];
                    }
                }
            }
            return [];
        },
        getCompareAnswers: function(dataset, practice) {
            var vm = this;
            if( typeof dataset.results != 'undefined' && dataset.results.length > 0 ) {
                for( let idx = 0; idx < dataset.results.length; ++idx ) {
                    if( dataset.results[idx].path === practice.path ) {
                        return dataset.results[idx];
                    }
                }
            }
            return {answers:[]};
        },
        selectMetric: function(question, dataset) {
            var vm = this;
            vm.displayMetric = question;
        },
        activateSelectAccounts: function() {
            var vm = this;
            vm.$refs.accountsTab.click();
        },
        exportData: function() { // XXX deprecate. downloading through
                                 // direct POST requests.
            var vm = this;
            const entries = vm.getEntries(vm.displayMetric.path);
            for( var entIdx = 0; entIdx < entries.length; ++entIdx ) {
                const practice = entries[entIdx];
                for( var datIdx = 0; datIdx < vm.datasets.length; ++datIdx ) {
                    const dataset = vm.datasets[datIdx];
                    const benchmarks = vm.getBenchmarks(dataset, practice);
                    const data = {
                        'benchmarks': benchmarks
                    };
                    vm.reqPost(vm.$urls.api_benchmarks_export, data,
                    function(resp) {
                    });
                }
            }
        },
        getSampleField: function(sample, fieldName) {
            var vm = this;
            if( sample ) {
                let fieldValue = sample.hasOwnProperty(fieldName) ?
                    sample[fieldName] : null;
                if( fieldValue ) {
                    return fieldValue;
                }
                const sampleSlug = sample.slug ? sample.slug : sample;
                const cached = vm.samplesBySlug[sampleSlug];
                if( cached && cached.hasOwnProperty(fieldName) ) {
                    return cached[fieldName];
                }
                // XXX disable loading individually. we need to give
                // `populateSamples` a chance to run and complete.
                if( false && vm.api_samples_url ) {
                    vm.samplesBySlug[sampleSlug] = {
                        picture: null,
                        printable_name: sampleSlug
                    };
                    vm.reqGet(vm._safeUrl(vm.$urls.api_responses, sampleSlug),
                    function(resp) {
                        vm.samplesBySlug[resp.slug] = resp;
                    }, function() {
                        // discard errors (ex: "not found").
                    });
                }
            }
            // If we don't return `undefined` here, we might inadvertently
            // post initialized fields (null, or "") in HTTP requests.
            return undefined;
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
        onDatasetSelected: function(bench) {
            // This method is called when the component needs to show
            // the list of accounts participating to a specific dataset.
            var vm = this;
            vm.populateSamples(bench);
        },
        getSampleAccountPrintableName: function(sampleSlug) {
            return this.getAccountPrintableName(
                this.getSampleField(sampleSlug, 'account'));
        },
        populateSamples: function(bench) {
            var vm = this;
            const samples = new Set();
            for( let idx = 0; idx < bench.values.length; ++idx ) {
                const vals = bench.values[idx];
                vals[2].forEach(item => samples.add(item));
            }
            if( samples.size ) {
                let httpRequests = [];
                let queryParams = "?q_f==slug&q=";
                let sep = "";
                let idx = 0;
                for( const sample of samples ) {
                    queryParams += sep + sample;
                    sep = ",";
                    idx += 1;
                    if( idx >= 25 ) { // XXX PAGE_SIZE
                        httpRequests.push(vm.$urls.api_responses + queryParams);
                        queryParams = "?q_f==slug&q=";
                        sep = "";
                        idx = 0;
                    }
                }
                if( idx > 0 ) {
                    httpRequests.push(vm.$urls.api_responses + queryParams);
                }
                for( idx = 0; idx < httpRequests.length; ++idx ) {
                    vm.reqGet(httpRequests[idx], function(resp) {
                        for( let jdx = 0; jdx < resp.results.length; ++jdx ) {
                            vm.$set(vm.samplesBySlug, resp.results[jdx].slug,
                                    resp.results[jdx]);
                        }
                        vm.populateAccounts(resp.results, 'account');
                    })
                }
            }
        },
        // display with active links
        textAsHtml: function(text, required) {
            var vm = this;
            if( !text ) {
                return required ? "&dash;" : "";
            }
            var activeLinks = text.replace(
                /(https?:\/\/\S+)/gi,
                '<a href="$1" target="_blank">external link</a>');
            if( vm.upload_complete_url ) {
                var reg = new RegExp(
                    '<a href="(' + vm.upload_complete_url +
                    '\/\\S+)" target="_blank">(external link)<\/a>', 'gi');
                activeLinks = activeLinks.replace(reg,
                    '<a href="$1">uploaded document</a>');
            }
            return activeLinks;
        },
        updateChart: function() {
            var vm = this;
            const entries = vm.getEntries(vm.displayMetric.path);
            for( var entIdx = 0; entIdx < entries.length; ++entIdx ) {
                const practice = entries[entIdx];
                var labels = [];      // labels on x-axis
                var choices = [];     // choices shown in each stack
                var datasets = [];
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
                var unit = vm.getUnit(
                    vm.displayMetric.default_unit || {});
                var choiceColors = buildChartColors(choices, unit);
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
                                    backgroundColor: choiceColors[choiceIdx],
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
                            var bgColors = buildChartColors(labels, unit);
                            datasets.push({
                                label: benchmarks[benchIdx].title, // label
                                backgroundColor: bgColors,
                                data: data,  // by account + by label
                            });
                        }  // if( choices.length )
                    } // benchIdx
                } // vm.datasets

                if( vm.compareChart ) {
                    vm.compareChart.destroy();
                }
                const chartElem = document.getElementById('summaryChart');
                if( chartElem ) {
                  if( choices.length ) {
                    labels = vm.humanizePeriods(labels);
                    var unit = vm.displayMetric.unit;
                    vm.compareChart = new Chart(chartElem, {
                            type: 'bar',
                            plugins: [ChartDataLabels],
                            borderWidth: 0,
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {
                                borderWidth: 1,
                                responsive: true,
                                maintainAspectRatio: false,
                                layout: {
                                    padding: { top: 30 }
                                },
                                plugins: {
                                    legend: {
                                        display: true,
                                        position: 'bottom'
                                    },
                                    datalabels: Object.assign({}, baseDatalabelsConfig, {
                                        display: 'auto',
                                        anchor: 'end',
                                        align: 'end',
                                        font: { weight: 'bold', size: 10 },
                                        padding: 4,
                                        formatter: unitFormatter(unit)
                                    }),
                                    tooltip: unitTooltip(unit)
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
                    var unit = vm.displayMetric.unit;
                    vm.compareChart = new Chart(chartElem, {
                            type: 'doughnut',
                            plugins: [ChartDataLabels, DoughnutLinesPlugin],
                            borderWidth: 0,
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {
                                borderWidth: 1,
                                responsive: true,
                                maintainAspectRatio: false,
                                layout: {
                                    padding: labels.length <= 3 ? 40 : Math.min(labels.length * 15, 120)
                                },
                                plugins: {
                                    legend: {
                                        display: false
                                    },
                                    datalabels: Object.assign({}, baseDatalabelsConfig, {
                                        anchor: 'end',
                                        align: 'end',
                                        offset: 8,
                                        formatter: doughnutLabelFormatter(unit)
                                    }),
                                    tooltip: unitTooltip(unit)
                                }
                            }
                        }
                    );
                  } // /type of chart
                } // /chartElem
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
        // XXX Does not override `practicesListMixin.mounted
        var vm = this;
        if( vm.$refs.query && vm.$refs.query.$refs.account ) {
            vm.$refs.query.$refs.account.$refs.input.focus();
        }
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
        getAffinityGroupDataset: function(groupSlug) {
            var vm = this;
            vm.params.start_at = vm.startAt ? vm.startAt : null;
            vm.params.ends_at = vm.endsAt ? vm.endsAt : null;
            vm.params.period_type = vm.period ? vm.period : null;
            vm.params.campaign = vm.campaign ? vm.campaign : null;
            const title = vm.$el.querySelector(
                '[value="' + groupSlug + '"]').textContent;
            const url = vm._safeUrl(vm._safeUrl(
                vm.$urls.api_account_groups, groupSlug),
                vm.prefix) + vm.getQueryString();
            return {title: title, url: url};
        },
        validate: function() {
            var vm = this;
            if( vm.affinityType === 'engaged' ||
                vm.affinityType === 'accessibles' ||
                vm.affinityType === 'all') {
                const dataset = vm._getAffinityBaseDataset();
                vm.$emit('updatedataset', dataset);
            } else {
                const dataset = vm.getAffinityGroupDataset(vm.affinityType);
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
        accountDetailMixin,
        userDetailMixin
    ],
    data: function() {
        var data = {
            url: this.$urls.api_portfolio_responses,
            portfolios_received_url: this.$urls.api_portfolios_received,
            api_sample_verification_url: this.$urls.api_sample_verification,
            api_profiles_base_url: this.$urls.api_organizations,
            verifiers: [],
            params: {
                period: 'yearly'
            },
            tagify: null,
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
                    vm.loadComplete(resp, typeaheadResp);
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
                vm.populateUsers(resp.results, 'verified_by');
                vm.items.results = vm.items.results.concat(resp.results);
            } else {
                vm.items = resp;
                vm.populateAccounts(vm.items.results);
                vm.populateUsers(resp.results, 'verified_by');
            }
            if( grantsResp ) {
                vm.grants = grantsResp;
                vm.populateAccounts(vm.grants.results, 'account');
            }
            if( vm.tagify ) {
                var allTags = (vm.tagChoices || []).slice();
                vm.items.results.forEach(function(entry) {
                    if( entry.extra && entry.extra.tags ) {
                        entry.extra.tags.forEach(function(tag) {
                            if( allTags.indexOf(tag) === -1 ) {
                                allTags.push(tag);
                            }
                        });
                    }
                });
                vm.tagify.whitelist = allTags;
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
                const api_roles_url = vm._safeUrl(vm._safeUrl(
                    vm.api_profiles_base_url, entry.slug), 'roles');
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
        updateVerifedBy: function(entry, verified_status) {
            var vm = this;
            if( verified_status ) {
                entry.verified_status = verified_status;
            }
            if( entry.verified_status === 'no-review' ) {
                entry.verified_by = null;
            }
            vm.populateUsers([entry], 'verified_by');
            if( entry.notes_url ) {
                vm.reqPut(entry.notes_url, {
                    verified_status: entry.verified_status,
                    verified_by: entry.verified_by
                }, function success(resp) {
                    entry.verified_by = resp.verified_by;
                })
            }
        },
    },
    mounted: function(){
        var vm = this;
        vm.get();
        if( vm.$urls.api_roles ) {
            vm.reqGet(vm.$urls.api_roles,
            function success(resp) {
                vm.verifiers = resp.results;
            });
        }
        if( vm.$refs.tagFilter && typeof Tagify !== 'undefined' ) {
            vm.tagify = new Tagify(vm.$refs.tagFilter, {
                whitelist: vm.tagChoices || [],
                dropdown: {
                    enabled: 1
                }
            });
            vm.tagify.DOM.input.setAttribute('aria-label', 'Search');
            vm.tagify.on('change', function() {
                var tags = vm.tagify.value.map(
                    function(item) { return item.value; });
                vm.params.q = tags.join(',');
                vm.reload();
            });
        }
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
        getUnit: function(defaultUnit) {
            var vm = this;
            if( vm.item.units && defaultUnit.slug ) {
                var unit = vm.item.units[defaultUnit.slug];
                if( typeof unit !== 'undefined' ) {
                    return vm.item.units[defaultUnit.slug];
                }
            }
            return defaultUnit;
        },
        _isArray: function(obj) {
            return obj instanceof Object && obj.constructor === Array;
        },
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
                var unit = vm.getUnit(resp.results[idx].default_unit);
                var bgColors = buildChartColors(labels, unit);
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
                        data.push(val ? val : 0);
                    }
                    datasets.push({
                        label: benchmarks[benchIdx].slug,
                        backgroundColor: bgColors,
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
                    var unit = vm.params ? vm.params.unit : null;
                    if( resp.results[idx].default_unit &&
                        resp.results[idx].default_unit.system == "datetime" ) {
                        vm.charts[chartKey] = new Chart(element, {
                            type: 'bar',
                            plugins: [ChartDataLabels],
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {
                                responsive: true,
                                layout: {
                                    padding: { top: 30 }
                                },
                                plugins: {
                                    legend: {
                                        display: false,
                                        // position: 'top',
                                    },
                                    title: {
                                        display: false
                                    },
                                    datalabels: Object.assign({}, baseDatalabelsConfig, {
                                        anchor: 'end',
                                        align: 'end',
                                        font: { weight: 'bold', size: 10 },
                                        padding: 4,
                                        formatter: unitFormatter(unit)
                                    }),
                                    tooltip: unitTooltip(unit)
                                }
                            },
                        });
                    } else {
                        vm.charts[chartKey] = new Chart(element, {
                            type: 'doughnut',
                            plugins: [ChartDataLabels, DoughnutLinesPlugin],
                            data: {
                                labels: labels,
                                datasets: datasets
                            },
                            options: {
                                layout: {
                                    // for lots of labels the chart gets cut off
                                    padding: labels.length <= 3 ? 40 : Math.min(labels.length * 15, 120)
                                },
                                plugins:{
                                    legend: {
                                        display: false
                                    },
                                    datalabels: Object.assign({}, baseDatalabelsConfig, {
                                        anchor: 'end',
                                        align: 'end',
                                        offset: 8,
                                        formatter: doughnutLabelFormatter(unit)
                                    }),
                                    tooltip: unitTooltip(unit)
                                }
                            }
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
                    label: resp.results[idx].title || resp.results[idx].slug,
                    backgroundColor: colors[idx],
                    borderColor: colors[idx],
                    data: data
                });
            }
            if( vm.completionRate ) {
                vm.completionRate.destroy();
            }
            var unit = vm.params ? vm.params.unit : null;
            vm.completionRate = new Chart(
                document.getElementById('completionRate'),
                {
                    type: 'line',
                    plugins: [ChartDataLabels],
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        plugins: {
                            datalabels: Object.assign({}, baseDatalabelsConfig, {
                                font: { weight: 'bold', size: 8 },
                                padding: 3,
                                formatter: unitFormatter(unit)
                            }),
                            tooltip: unitTooltip(unit)
                        }
                      }
                }
            );
        },
    },
}));


Vue.component('reporting-completion-total', dashboardChart.extend({
    data: function(){
        return {
            datasets: [{
                url: this.$urls.api_portfolio_engagement_stats,
            }],
            nb_verified: 0,
            nb_completed: 0,
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
            var stats = [];
            for( var idx = 0; idx < resp.results.length; ++idx ) {
                var serie = {
                    slug: resp.results[idx].slug,
                    title: resp.results[idx].title,
                    nb_verified: 0,
                    nb_completed: 0,
                    values: []
                };
                for( var valIdx = 0; valIdx < resp.results[idx].values.length;
                     ++valIdx ) {
                    const key = resp.results[idx].values[valIdx][0];
                    const val = resp.results[idx].values[valIdx][1];
                    if( key === 'Verified' ) {
                        serie.nb_verified = val;
                    } else {
                        if ( key === 'Completed' ) {
                            serie.nb_completed = val;
                        }
                        serie.values.push(resp.results[idx].values[valIdx]);
                    }
                }
                for( var valIdx = 0; valIdx < serie.values.length; ++valIdx ) {
                    const key = serie.values[valIdx][0];
                    if ( key === 'Completed' ) {
                        serie.values[valIdx][1] += serie.nb_verified;
                    }
                }
                // We rely on the first serie to be the one for the account.
                if( idx === 0 ) {
                    vm.nb_verified = serie.nb_verified;
                    vm.nb_completed = serie.nb_completed;
                }
                stats.push(serie);
            }
            for( var idx = 0; idx < stats.length; ++idx ) {
                var data = [];
                for( var valIdx = 0; valIdx < stats[idx].values.length;
                     ++valIdx ) {
                    if( idx == 0 ) {
                        labels.push(stats[idx].values[valIdx][0]);
                    }
                    data.push(stats[idx].values[valIdx][1]);
                }
                datasets.push({
                    label: stats[idx].slug,
                    backgroundColor: colors,
                    data: data
                });
            }
            if( vm.completionRate ) {
                vm.completionRate.destroy();
            }
            var unit = vm.params ? vm.params.unit : null;
            vm.completionRate = new Chart(
                document.getElementById('summaryChart'),
                {
                    type: 'doughnut',
                    plugins: [ChartDataLabels, DoughnutLinesPlugin],
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
                                position: 'bottom'
                            },
                            datalabels: Object.assign({}, baseDatalabelsConfig, {
                                formatter: unitFormatter(unit)
                            }),
                            tooltip: unitTooltip(unit)
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
        },
        verifiedRate: function() {
            const vm = this;
            if( vm.params.unit === 'percentage'){
                const total = vm.nb_verified + vm.nb_completed;
                return total > 0 ? Math.round(vm.nb_verified * 100 / total) : 0;
            } else {
                return vm.nb_verified;
            }
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
            var unit = vm.params ? vm.params.unit : null;
            vm.goals = new Chart(
                document.getElementById('goals'),
                {
                    type: 'bar',
                    plugins: [ChartDataLabels],
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
                            },
                            datalabels: Object.assign({}, baseDatalabelsConfig, {
                                formatter: unitFormatter(unit)
                            }),
                            tooltip: unitTooltip(unit)
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
            var unit = vm.params ? vm.params.unit : null;
            vm.bySegements = new Chart(
                document.getElementById('bySegements'),
                {
                    type: 'bar',
                    plugins: [ChartDataLabels],
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
                            },
                            datalabels: Object.assign({}, baseDatalabelsConfig, {
                                formatter: unitFormatter(unit)
                            }),
                            tooltip: unitTooltip(unit)
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


Vue.component('accessible-by-profiles', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {}
    },
    methods: {
    }
});
