// Copyright (c) 2025, DjaoDjin inc.
// see LICENSE.

// This file contains UI elements used during survey/assessment (data input).

Vue.component('newsfeed', {
    mixins: [
        itemListMixin,
        accountDetailMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_newsfeed,
            getCompleteCb: 'getCompleted',
        }
    },
    methods: {
        getCompleted: function(){
            var vm = this;
            vm.populateAccounts(vm.items.results, 'account');
            vm.populateUserProfiles();
        },
        populateUserProfiles: function() {
            var vm = this;
            var users = new Set();
            for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                for(let item of vm.items.results[idx].respondents) {
                    users.add(item);
                }
            }
            for( const key of users ) {
                vm.reqGet(vm._safeUrl(vm.$urls.api_users, key),
                function(resp) {
                    vm.accountsBySlug[resp.username] = resp;
                    vm.$forceUpdate();
                }, function() {
                    // discard errors (ex: "not found").
                });
            }
        },
    },
    mounted: function(){
        this.get();
    }
});


Vue.component('campaign-questions-list', {
    mixins: [
        practicesListMixin
    ],
    props: [
        'preloadedElements'
    ],
    data: function() {
        return {
            url: this.$urls.api_content,
            items: this.preloadedElements ? this.preloadedElements : {
                results: [], count: 0
            },
            itemsLoaded: this.preloadedElements ? true : false,
            account_benchmark_url: this.$urls.api_account_benchmark,

            api_verification_sample: this.$urls.api_verification_sample || null,
            api_improvement_sample: this.$urls.api_improvement_sample,
            api_aggregate_metric_base: this.$urls.api_aggregate_metric_base,
            valueSummaryToggle: true,
            vsPeersToggle: 0,
            activeTile: null,
            activeElement: null,
            activeTargets: "",
            isOpenComments: false,
            nbAnswers: this.$sample ? this.$sample.nbAnswers : 0,
            nbQuestions: this.$sample ? this.$sample.nbQuestions  : 0,
            nbRequiredAnswers: this.$sample ? this.$sample.nbRequiredAnswers : 0,
            nbRequiredQuestions: this.$sample ? this.$sample.nbRequiredQuestions : 0,
            api_profiles_url: this.$urls.api_profiles,
            profilesBySlug: {}
        }
    },
    methods: {
        addSegment: function(segment) {
            var vm = this;
            vm.reqGet(vm._safeUrl(vm.url, segment.path),
            function(resp) {
                vm.items.results.push(segment);
                vm.items.count += resp.count + 1;
                for( var idx = 0; idx < resp.results.length; ++idx ) {
                    resp.results[idx].path = resp.path + resp.results[idx].path;
                    resp.results[idx].indent += 1;
                    vm.items.results.push(resp.results[idx]);
                }
                for( var key in resp.units ){
                    if( resp.units.hasOwnProperty(key) ){
                        vm.items.units[key] = resp.units[key];
                    }
                }
                vm.$nextTick(function() {
                    elem = vm.$el.querySelector(
                        '[href="#' + segment.slug + '"]');
                    if( elem ) {
                        elem.parentElement.scrollIntoView({behavior: 'instant'});
                    }
                    elem = vm.$el.querySelector('#' + segment.slug);
                    if( elem ) {
                        elem.scrollIntoView(true);
                    }
                });
            });
        },
        appToolbarLinkClicked: function() {
            // XXX only if not pinned
            toggleSidebar("#app-toolbar-left");
        },
        getPracticeId: function(practice, prefix) {
            // We define this method almost identically
            // in `'campaign-questions-list'` and `'scorecard'`.
            const vm = this;
            const longId = practice.path.substr(1).replaceAll('/', '-');
            if( vm.showVsPeers && prefix ) {
                return prefix + longId;
            }
            return longId;
        },
        humanizeScoreWeight: function (value, percentage) {
            if( !value || value === 0 ) {
                return "0.00";
            }
            if( percentage ) {
                return (value * 100).toFixed(0) + "%";
            }
            return value.toFixed(2);
        },
        humanizeTimeDelta: function (at_time, ends_at) {
            var cutOff = ends_at ? moment(ends_at) : moment();
            var dateTime = moment(at_time);
            var relative = "";
            if( dateTime <= cutOff ) {
                var timeAgoTemplate = "%(timedelta)s ago";
                relative = timeAgoTemplate.replace("%(timedelta)s",
                    moment.duration(cutOff.diff(dateTime)).humanize());
            } else {
                var timeLeftTemplate = "%(timedelta)s ago";
                relative = timeLeftTemplate.replace("%(timedelta)s",
                    moment.duration(dateTime.diff(cutOff)).humanize());
            }
            return dateTime.format('MMMM Do YYYY') + " (" + relative + ")";
        },

        getChoices: function(row, icon) {
            var vm = this;
            if( !row.choices_headers ) {
                var defaultUnit = null;
                var entries = vm.getEntries(row.slug);
                if( entries.length === 0 ) {
                    // We are dealing with a single practice.
                    entries.push(row);
                }
                for( var idx = 0; idx < entries.length; ++idx ) {
                    if( entries[idx].default_unit ) {
                        if( !defaultUnit ) {
                            defaultUnit = entries[idx].default_unit;
                        } else if( defaultUnit.slug !==
                                   entries[idx].default_unit.slug ) {
                            defaultUnit = null;
                            break;
                        }
                    }
                }
                row.choices_headers = [];
                if( defaultUnit && defaultUnit.choices ) {
                    if( icon ) {
                        var iconChoices = vm.getChoices(icon);
                        var isIdentDescr = (iconChoices.length > 0);
                        if( defaultUnit.choices.length ===
                            iconChoices.length ) {
                            for( var idx = 0; idx < defaultUnit.choices.length;
                                 ++idx ) {
                                if( defaultUnit.choices[idx].descr !==
                                    iconChoices[idx].descr ) {
                                    isIdentDescr = false;
                                    break;
                                }
                            }
                        }
                        // using `isEnumHeaderShown(icon)` and `'d-md-none'`
                        // to achieve the same result.
                        if( false && isIdentDescr ) {
                            for( var idx = 0; idx < defaultUnit.choices.length;
                                 ++idx ) {
                                row.choices_headers.push({
                                    text: defaultUnit.choices[idx].text,
                                    descr: ""
                                });
                            }
                        }
                    }
                    if( row.choices_headers.length === 0 ) {
                        if( entries.length > 1 ) {
                            // We are dealing with an icon so we take
                            // the generic unit choices instead of the row ones
                            // to avoid missing `descr` in the first row.
                            var defaultUnitSlug = (
                                defaultUnit.slug || defaultUnit);
                            if( vm.items.units &&
                                vm.items.units[defaultUnitSlug] ) {
                                defaultUnit = vm.items.units[defaultUnitSlug];
                            }
                        }
                        row.choices_headers = defaultUnit.choices;
                    }
                }// if( defaultUnit && defaultUnit.choices )
            }
            return row.choices_headers;
        },
        getNbInputCols: function(practice) {
            var vm = this;
            if( (practice.choices_headers &&
                 practice.choices_headers.length > 0) ||
                (practice.default_unit &&
                 practice.default_unit.system === 'enum') ) {
                return Math.floor(6 / vm.getChoices(practice).length);
            }
            return 6;
        },
        getPrimaryCandidate: function(practice) {
            if( (typeof practice.candidates === 'undefined') ||
                practice.candidates.length < 1 ) {
                practice['candidates'] = [{
                    measured: null
                }];
            }
            return practice.candidates[0];
        },
        importFromTrackingTool: function(practice) {
            var vm = this;
            var primaryAnswer = vm.getPrimaryAnswer(practice);
            var startsAt = vm.getAnswerStartsAt(practice).measured;
            var endsAt = vm.getAnswerEndsAt(practice).measured;
            var queryParams = "";
            var sep = "";
            if( startsAt ) {
                queryParams += "start_at=" + startsAt;
                sep = "&";
            }
            if( endsAt ) {
                // Implementation note: we add 1s so that the data
                // that was recorded on the last day of the period
                // is included. (`<` vs. `<=`).
                queryParams += sep + "ends_at=" + endsAt + "T00:00:01Z";
                sep = "&";
            }
            if( primaryAnswer.unit ) {
                const rindex = primaryAnswer.unit.lastIndexOf('-');
                const unit = rindex ? primaryAnswer.unit.substr(0, rindex)
                      : primaryAnswer.unit;
                queryParams += sep + "unit=" + unit;
            }
            vm.reqGet(vm._safeUrl(vm.api_aggregate_metric_base,
                vm.prefix + practice.path) + (
                queryParams ? ("?" + queryParams) : ""),
            function(resp) {
                vm.updateAssessmentAnswer(practice, {
                    'measured': parseInt(resp.measured),
                    'unit': resp.unit + '-year'
                });
                vm.$set(primaryAnswer, 'measured', parseInt(resp.measured));
                vm.$set(primaryAnswer, 'unit', resp.unit + '-year');
            });
        },
        isEnumHeaderShown: function(icon) {
            var vm = this;
            return icon.choices_headers && icon.choices_headers.length > 0;
        },
        isActiveCommentsShown: function(practice) {
            var vm = this;
            return vm.isOpenComments && (vm.activeElement &&
                vm.activeElement.slug === practice.slug);
        },
        isNAICSUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && (
                row.default_unit && row.default_unit.slug == 'naics');
        },
        isRevenueUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'revenue'
                && (row.default_unit && (row.default_unit.slug === 'usd' ||
                    row.default_unit.slug === 'million-usd'));
        },
        isTargetBaselineUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'target-baseline';
        },

        // Helpers to check values of assessment answers
        isAtLeastYes: function(practice) {
            var vm = this;
            return practice.answers.length > 0 &&
                vm.getPrimaryAnswer(practice).measured === vm.YES;
        },
        isAtLeastNeedsModerateImprovement: function(practice) {
            var vm = this;
            return practice.answers.length > 0 &&
                ((vm.getPrimaryAnswer(practice).measured === vm.NEEDS_MODERATE_IMPROVEMENT)
                || (vm.getPrimaryAnswer(practice).measured === vm.YES));
        },
        isAtLeastNeedsSignificantImprovement: function(practice) {
            var vm = this;
            return practice.answers.length > 0 &&
            ((vm.getPrimaryAnswer(practice).measured === vm.NEEDS_SIGNIFICANT_IMPROVEMENT)
             || (vm.getPrimaryAnswer(practice).measured === vm.NEEDS_MODERATE_IMPROVEMENT)
             || (vm.getPrimaryAnswer(practice).measured === vm.YES));
        },
        isImplemented: function(practice) {
            var vm = this;
            return vm.isAtLeastNeedsSignificantImprovement(practice);
        },
        isNo: function(practice) {
            var vm = this;
            return practice.answers.length > 0 &&
                (vm.getPrimaryAnswer(practice).measured === vm.NO);
        },
        isNotAnswered: function(practice) {
            var vm = this;
            return !(vm.isAtLeastNeedsSignificantImprovement(practice)
                || vm.isNo(practice) || vm.isNotApplicable(practice));
        },
        isNumberUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'number';
        },
        isIcon: function(colHeader) {
            var search = ".png";
            var colTitle = colHeader.title;
            if( colHeader && colHeader.title ) {
                return colTitle.substring(
                    colTitle.length - search.length, colTitle.length) === search;
            }
            return false;
        },
        getPath: function(practice) {
            return practice.path;
        },

        slugify: function (choiceText, rank) {
            if( choiceText ) {
                return choiceText.toLowerCase().replace(' ', '-') + '-' + rank;
            }
            return "";
        },
        sortBy: function(field){
            var vm = this;
            var oldDir = vm.sortDir(field);
            vm.$set(vm.params, 'o', oldDir === 'asc' ? ('-' + field) : field);
        },

        // Planned improvements
        sortedBy: function(colHeader) {
            var vm = this;
            return 'fa fa-sort' + (vm.sortDir(colHeader.slug) ? ('-' + vm.sortDir(colHeader.slug)) : '');
        },
        toggleTile: function($event, tile) {
            var vm = this;
            // Change active tab
            if( vm.activeTile && vm.activeTile.slug === tile.slug ) {
                vm.activeTile = null;
            } else {
                vm.activeTile = tile;
                if( vm.containsTag(vm.activeTile, 'metrics') ) {
                    vm.valueSummaryToggle = true;
                    vm.vsPeersToggle = 0;
                }
                elem = vm.$el.querySelector('#' + tile.slug);
                vm.$nextTick(function() {
                    elem.scrollIntoView(true);
                });
            }
        },
        getCollectedByField: function(user, fieldName) {
            var vm = this;
            if( user && user.hasOwnProperty(fieldName) ) {
                return user[fieldName];
            }
            if( user ) {
                const profile = vm.profilesBySlug[user];
                if( profile && profile.hasOwnProperty(fieldName) ) {
                    return profile[fieldName];
                }
                vm.profilesBySlug[user] = {
                    picture: null,
                    printable_name: user
                };
                let queryParams = "?q_f==slug&q=" + user;
                vm.reqGet(vm.api_profiles_url + queryParams,
                function(resp) {
                    for( let idx = 0; idx < resp.results.length; ++idx ) {
                        vm.profilesBySlug[resp.results[idx].slug] =
                            resp.results[idx];
                    }
                }, function() {
                    // discard errors (ex: "not found").
                });
                return vm.profilesBySlug[user][fieldName];
            }
            return "";
        },
        getPicture: function(user) {
            return this.getCollectedByField(user, 'picture');
        },
        getPrintableName: function(user) {
            return this.getCollectedByField(user, 'printable_name');
        },
        populateUserProfiles: function() {
            var vm = this;
            for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                var row = vm.items.results[idx];
                if( row.answers ) {
                    for( var jdx = 0; jdx < row.answers.length; ++jdx ) {
                        var answer = row.answers[jdx];
                        if( !profilesBySlug[answer.collected_by] ) {
                            vm.profilesBySlug[answer.collected_by] = 1;
                        }
                    }
                }
            }
            for( var key in profilesBySlug ) {
                if( profilesBySlug.hasOwnProperty(key) ) {
                    vm.reqGet(vm._safeUrl(vm.api_profiles_url, key),
                    function(resp) {
                        vm.profilesBySlug[resp.slug] = resp;
                    });
                }
            }
        },
        resetAssessment: function($event, prefix) {
            var vm = this;
            var form = $($event.target);
            var modalDialog = form.parents('.modal');
            modalDialog.modal('hide');
            var path = (prefix ? prefix : '') + '/' + vm.activeTile.path;
            var url = vm._safeUrl(vm.$urls.api_assessment_reset ?
                vm.$urls.api_assessment_reset : vm._safeUrl(
                    vm.api_assessment_sample, '/reset'), path);
            vm.reqPost(url, function success(resp) {
              // remove answers under the active tile.
              var idx = 0;
              for( ; idx < vm.items.results.length; ++idx ) {
                  if( vm.items.results[idx].slug === vm.activeTile.slug ) {
                      ++idx;
                      break;
                  }
              }
              for( ; idx < vm.items.results.length; ++idx ) {
                  if( vm.items.results[idx].indent <= vm.activeTile.indent ) {
                      break;
                  }
                  if( vm.items.results[idx].answers ) {
                      for( var jdx = 0;
                           jdx < vm.items.results[idx].answers.length; ++jdx ) {
                          vm.items.results[idx].answers[jdx].measured = null;
                      }
                  }
              }
              // reloads is simpler.
              vm.get();
              vm.showMessages([
                  "Reset successful. Please continue with this assessment or an assessment in a different industry segment."],
                  "success");
            });
        },
        useCandidateAssessment: function($event, prefix) {
            var vm = this;
            var path = (prefix ? prefix : '') + '/' + vm.activeTile.slug;
            vm.reqPost(
                vm._safeUrl(vm.api_assessment_sample, '/candidates' + path),
            function success(resp) {
              // update answers as returned by the API.
              for( var idx = 0; idx < resp.results.length; ++idx ) {
                  for( var jdx = 0;  jdx < vm.items.results.length; ++jdx ) {
                      if( vm.items.results[jdx].path &&
                          vm.items.results[jdx].path === resp.results[idx].path ) {
                          vm.items.results[jdx].answers = resp.results[idx].answers;
                      }
                  }
              }
              // update the number of answers
              vm.nbAnswers = resp.nb_answers ? resp.nb_answers : 0;
              vm.nbRequiredAnswers = resp.nb_required_answers ?
                  resp.nb_required_answers : 0;
            });
        },

        // Call on the API to update an Answer in a Sample.
        // By passing a dict `{unit: "__slug__", measured: "__value__"}`,
        // it is possible to attach additional answers to a question
        // on top of the primary answer (i.e. the one where
        // `answer.unit == question.default_unit`). Free form text comments
        // heavily rely on this feature for example.
        _callUpdateAnswer: function(practice, measured, tag,
                                     successCallback, errorCallback) {
            var vm = this;
            const path = practice.path;
            const apiUrl = ( practice.extra &&
                             practice.extra.tags &&
                             practice.extra.tags.includes('verify') ) ?
                  vm._safeUrl(vm.api_verification_sample, '/answers') : (
                             tag === 'planned' ) ?
                  vm._safeUrl(vm.api_improvement_sample, '/answers') :
                  vm._safeUrl(vm.api_assessment_sample, '/answers');
            var data = null;
            if( typeof measured === 'undefined' || measured === null ) return;
            if( vm._isArray(measured) ) {
                data = measured;
            } else if( vm._isObject(measured) ) {
                data = measured;
                if( typeof data.measured === 'undefined' ||
                    data.measured === null ) return;
            } else {
                data = {measured: measured};
            }
            vm.reqPost(vm._safeUrl(apiUrl, vm.prefix + path), data,
            function success(resp, textStatus, jqXHR) {
                if( jqXHR.status == 201 ) {
                    vm.nbAnswers++;
                    if( resp.question && resp.question.required ) {
                        vm.nbRequiredAnswers++;
                    }
                }
                if( successCallback ) {
                    successCallback(resp);
                }
            },
            function error(resp) {
                vm.showErrorMessages(resp);
                if( errorCallback ) {
                    errorCallback(resp);
                }
            });
        },
        openCommentsAutomatically: function(practice, newValue) {
            return (practice.default_unit.slug == 'assessment' &&
                    newValue === this.NOT_APPLICABLE) ||
                (practice.ui_hint === 'yes-comments' &&
                 newValue === this.YES) ||
                practice.ui_hint === 'yes-no-comments';
        },
        updateAssessmentAnswer: function(practice, newValue, tag) {
            var vm = this;
            if( newValue == null ) { // `undefined` or `null`
                newValue = vm.getPrimaryAnswer(practice, tag);
            }
            vm._callUpdateAnswer(practice, newValue, tag,
            function success(resp) {
                if( resp.length ) {
                    for( var idx = 0; idx < resp.length; ++resp ) {
                        var answer = vm.getAnswerByUnit(practice, resp[idx].unit);
                        answer.created_at = resp[idx].created_at;
                        const user = resp[idx].collected_by;
                        answer.collected_by = user;
                        if( !vm.profilesBySlug[user] ) {
                            let queryParams = "?q_f==slug&q=" + user;
                            vm.reqGet(vm.api_profiles_url + queryParams,
                            function(resp) {
                                for( let idx = 0; idx < resp.results.length; ++idx ) {
                                    vm.profilesBySlug[resp.results[idx].slug] =
                                        resp.results[idx];
                                }
                                // We force an update after the user info
                                // is loaded, otherwise the picture of the
                                // commentator is not displayed on 'Submit'
                                // of a new comment.
                                vm.$forceUpdate();
                            }, function() {
                                // discard errors (ex: "not found").
                            });
                        }
                    }
                }
                if( vm.openCommentsAutomatically(practice, newValue) ) {
                    vm.openComments(practice, true);
                }
                if( resp.question ) {
                    practice.opportunity = resp.question.opportunity;
                }
            });
        },
        toggleNotDisclosedPublicly: function(row) {
            this.updateAssessmentAnswer(row, {
                measured: this.getAnswerByUnit(row, 'yes-no').measured === 'Yes' ?
                    'No' : 'Yes', unit: 'yes-no'})
        },
        updateStartsAt: function(practice) {
            var vm = this;
            vm.setActiveElement(practice);
            vm.updateAssessmentAnswer(practice);
            this.$nextTick(function() {
                if( !jQuery('#syncEndsAt').is(':visible') ) {
                    jQuery('#syncBaselineAt').modal("show");
                }
            });
        },
        updateEndsAt: function(practice) {
            var vm = this;
            vm.setActiveElement(practice);
            vm.updateAssessmentAnswer(practice);
            this.$nextTick(function() {
                if( !jQuery('#syncBaselineAt').is(':visible') ) {
                    jQuery('#syncEndsAt').modal("show");
                }
            });
        },
        // We update all `starts-at` in the UI and in the database.
        updateAllStartsAt: function(practice, tag) {
            var vm = this;
            const newValue = vm.getAnswerStartsAt(
                practice ? practice : vm.activeElement)
            const atTime = newValue.measured;
            var practices = vm.getEntries();
            for( var idx = 0; idx < practices.length; ++idx ) {
                var row = practices[idx];
                if( vm.isEnergyUIHint(row) || vm.isGHGEmissions(row) ||
                    vm.isWaterUIHint(row) || vm.isWasteUIHint(row) ) {
                    vm.getAnswerStartsAt(row).measured = atTime;
                    vm._callUpdateAnswer(row, newValue, tag);
                }
            }
        },
        // We update all `ends-at` in the UI and in the database.
        updateAllEndsAt: function(practice, tag) {
            var vm = this;
            var newValue = vm.getAnswerEndsAt(
                practice ? practice : vm.activeElement)
            const atTime = newValue.measured;
            var practices = vm.getEntries();
            for( var idx = 0; idx < practices.length; ++idx ) {
                var row = practices[idx];
                if( vm.isEnergyUIHint(row) || vm.isGHGEmissions(row) ||
                    vm.isWaterUIHint(row) || vm.isWasteUIHint(row) ) {
                    vm.getAnswerEndsAt(row).measured = atTime;
                    vm._callUpdateAnswer(row, newValue, tag);
                }
            }
        },
        updateComment: function(text, practice) {
            var vm = this;
            const comment = vm.getCommentsAnswer(practice);

            comment.measured = text;
            vm.updateAssessmentAnswer(practice, comment);
        },
        updateMultipleAssessmentAnswers: function (heading, newValue, tag) {
            var vm = this;
            if( newValue === vm.NOT_APPLICABLE ) {
                var trip = new Trip([{
                    sel: $("#assess-content"),
                    content: "<p class='text-left'>Did you mean to select <strong>Not applicable</strong> for all responses below.<br />If not, revise your response by selecting a response for each<br />individual row under the heading row.</p>",
                    position: "screen-center",
                    enableAnimation: false,
                    delay:-1,
                    tripTheme: "black",
                    showNavigation: true,
                    canGoPrev: false,
                    prevLabel: " ",
                    nextLabel: "OK",
                    skipLabel: " ",
                    finishLabel: "OK",
                }]);
                trip.start();
            }
            // update all answers under the active heading
              var idx = 0;
            for( ; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].slug === heading.slug ) {
                    ++idx;
                    break;
                }
            }
            for( ; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].indent <= heading.indent ) {
                    break;
                }
                var row = vm.items.results[idx];
                if( vm.isPractice(row) ) {
                    vm.getPrimaryAnswer(row, tag).measured = newValue;
                    vm._callUpdateAnswer(row, newValue, tag);
                }
            }
        },

        getPlannedChecked: function(practice) {
            var vm = this;
            return Boolean(vm.getPrimaryAnswer(practice, 'planned').measured)
        },

        // deprecated
        updatePlannedAnswer: function(practice, newValue) {
            var vm = this;
            if( vm.isPractice(practice) ) {
                var improveUrl = vm._safeUrl(vm.api_improvement_sample,
                    '/answers' + vm.prefix + practice.path);
                if( typeof newValue !== 'undefined' ) {
                    var data = {
                        measured: newValue
                    };
                    vm.setActiveElement(practice);
                    vm.reqPost(improveUrl, data,
                    function success(resp) {
                        var improvementDashboard = $("#improvement-dashboard");
                        if( improvementDashboard.length > 0 )  {
                        // XXX currently not working
                        // XXXimprovementDashboard.data('improvementDashboard').load();
                        }
                        if( vm.activeElement &&
                            vm.activeElement.extra &&
                            vm.activeElement.extra.tags ) {
                            for( var idx = 0;
                                 idx < vm.activeElement.extra.tags.length;
                                 ++idx ) {
                                if( vm.activeElement.extra.tags[idx] ===
                                    vm.TAG_ENERGY_EMISSIONS ||
                                    vm.activeElement.extra.tags[idx] ===
                                    vm.TAG_WATER ||
                                    vm.activeElement.extra.tags[idx] ===
                                    vm.TAG_WASTE) {
                                    vm.activeTargets = vm.activeElement.extra.tags[idx];
                                    var modalDialog = $('#practice-info');
                                    modalDialog.modal('show');
                                    break;
                                }
                            }
                        }
                    });
                } else {
                    var resetUrl = vm._safeUrl(vm.api_improvement_sample,
                        '/reset' + vm.prefix + practice.path)
                        + '?unit=' + vm.getPrimaryPlanned(practice).unit;
                    vm.reqPost(resetUrl,
                    function success(resp) {
                        $("#improvement-dashboard").data(
                            'improvementDashboard').load();
                    });
                }
            }
        },
        // deprecated
        updateMultiplePlannedAnswers: function (heading, newValue) {
            var vm = this;
            if( newValue === vm.NOT_APPLICABLE ) {
                var trip = new Trip([{
                    sel: $("#assess-content"),
                    content: "<p class='text-left'>Did you mean to select <strong>Not applicable</strong> for all responses below.<br />If not, revise your response by selecting a response for each<br />individual row under the heading row.</p>",
                    position: "screen-center",
                    enableAnimation: false,
                    delay:-1,
                    tripTheme: "black",
                    showNavigation: true,
                    canGoPrev: false,
                    prevLabel: " ",
                    nextLabel: "OK",
                    skipLabel: " ",
                    finishLabel: "OK",
                }]);
                trip.start();
            }
            // update all answers under the active heading
              var idx = 0;
            for( ; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].slug === heading.slug ) {
                    ++idx;
                    break;
                }
            }
            for( ; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].indent <= heading.indent ) {
                    break;
                }
                var row = vm.items.results[idx];
                if( vm.isPractice(row) ) {
                    vm.updatePlannedAnswer(row, newValue);
                }
            }
        },

        setActiveElement: function(practice) {
            this.activeElement = practice;
        },
        openComments: function(practice, opened) {
            var vm = this;
            if( vm.activeElement &&
                vm.activeElement.slug === practice.slug) {
                if( typeof opened == 'undefined' ) {
                    vm.isOpenComments = !vm.isOpenComments;
                } else {
                    vm.isOpenComments = opened;
                }
            } else {
                vm.setActiveElement(practice);
                vm.isOpenComments = true;
            }
        },
    },
    computed: {
        BEST_PRACTICE_ELEMENT: function() { return 'best-practice'; },
        HEADING_ELEMENT: function() { return 'heading'; },
        TAG_ENERGY_EMISSIONS: function() { return 'Energy & Emissions'; },
        TAG_WATER: function() { return 'Water'; },
        TAG_WASTE: function() { return 'Waste'; },
        // Helpers to check value of assessment answers
        YES: function() { return 'Yes'; },
        NEEDS_MODERATE_IMPROVEMENT: function() { return 'Mostly yes'; },
        NEEDS_SIGNIFICANT_IMPROVEMENT: function() { return 'Mostly no'; },
        NO: function() { return 'No'; },

        showVsPeers: function() {
            return parseInt(this.vsPeersToggle) > 0;
        },
    },
    mounted: function() {
        var vm = this;
        $("[id^='toggle-value-summary-']").change(function() {
            vm.valueSummaryToggle = $(this).prop('checked');
        });
    }
});


/** Component used to display improvement charts
    as used in app/improve/_improve_charts.html

    requires Chart from chart.js
*/
Vue.component('planning-dashboard', {
    mixins: [
        practicesListMixin
    ],
    props: ['activeTile'],
    data: function() {
        return {
            url: this.$urls.api_account_benchmark,
        }
    },
});


/** Component used to display a scorecard as used in app/scorecard/index.html

    requires Chart from chart.js
*/
Vue.component('scorecard', {
    mixins: [
        itemListMixin,
        practicesListMixin
    ],
    data: function() {
        return {
            url: this.$urls.survey_api_sample_answers,
            api_assessment_freeze: this.$urls.api_assessment_freeze ?
                this.$urls.api_assessment_freeze : this._safeUrl(
                    this.$urls.api_assessment_sample, '/freeze'),
            api_assessment_reset: this.$urls.api_assessment_reset ?
                this.$urls.api_assessment_reset : this._safeUrl(
                    this.$urls.api_assessment_sample, '/reset'),
            account_benchmark_url: this.$urls.api_account_benchmark,
            upload_complete_url: this.$urls.api_asset_upload_complete,
            params: {o: ""},
            activeTile: null,
            scorecardToggle: 1,
            summaryPerformance: this.$summary_performance ? this.$summary_performance : [],
            freezeAssessmentDisabled: false,
            verificationStatus: "",
            getCompleteCb: 'scorecardLoaded'
        }
    },
    methods: {
        scorecardLoaded: function() {
            var vm = this;
            vm.buildSummaryChart();
            vm.contentLoaded();
        },
        buildSummaryChart: function() {
            // Creates the top level summary polar chart
            var vm = this;
            var labels = [];
            var data = [];
            for( let key in vm.summaryPerformance ) {
                if( vm.summaryPerformance.hasOwnProperty(key) ) {
                    labels.push(key);
                    data.push(vm.summaryPerformance[key]);
                }
            }
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
                            labels: labels,
                            datasets: [{
                                label: "score",
                                data: data,
                                backgroundColor: [
                                    'rgb(255, 99, 132)',
                                    'rgb(75, 192, 192)',
                                    'rgb(255, 205, 86)']
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: {
                                    display: true,
                                    position: 'bottom',
                                },
                                title: {
                                    display: true,
                                    text: "Improvement planning",
                                    position: 'bottom',
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
            if( vm.isPractice(practice) ) {
                // `getColHeaders` is only called when we are dealing
                // with Data metrics.
                var period = Date.parse(vm.getAnswerEndsAt(practice).measured);
                if( !isNaN(period) ) {
                    period = new Date(period);
                    headers.push(period.getFullYear());
                }
            } else {
                var totals = vm.getEntries(practice.slug);
                for( var idx = 0; idx < totals.length; ++idx ) {
                    var candidateHeaders = vm.getColHeaders(totals[idx]);
                    if( candidateHeaders.length > headers.length ) {
                        headers = candidateHeaders;
                    }
                }
            }
            if( headers.length < 1 ) {
                headers.push("N/A");
            }
            return headers;
        },
        getColValue: function(practice, colHeader) {
            var vm = this;
            var vals = [];
            // `getColValue` is only called when we are dealing
            // with Data metrics.
            var period = (new Date(vm.getAnswerEndsAt(practice).measured)).getFullYear();
            if( !isNaN(period) && period === colHeader ) {
                var measured = vm.getPrimaryAnswer(practice).measured;
                if( typeof measured !== 'undefined' && measured !== null &&
                    !isNaN(measured) ) {
                    return measured;
                }
            }
            return "-";
        },
        getCaptionTitle: function(row) {
            var vm = this;
            var captionUnit = null;
            var practices = vm.getEntries(row.slug);
            for( var idx = 0; idx < practices.length; ++idx ) {
                const unit = vm.getPrimaryUnit(practices[idx]);
                if( captionUnit && captionUnit.slug != unit.slug ) {
                    captionUnit = null;
                    break;
                }
                captionUnit = unit;
            }
            return captionUnit ? captionUnit.title : "";
        },
        getNbRespondents: function(practice) {
            var vm = this;
            if( vm.charts ) {
                var chartKeys = [practice.path, '/summary' + practice.path];
                for( var idx = 0; idx < chartKeys.length; ++idx ) {
                    var chartKey = chartKeys[idx];
                    var chart = vm.charts[chartKey];
                    if( chart ) {
                        return chart.nb_respondents ?
                            chart.nb_respondents : "?";
                    }
                }
            }
            return "?";
        },
        getPracticeId: function(practice, prefix) {
            // We define this method almost identically
            // in `'campaign-questions-list'` and `'scorecard'`.
            const longId = practice.path.substr(1).replaceAll('/', '-');
            return longId;
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
        isChartHeading: function(row) {
            var vm = this;
            return vm.containsTag(row, vm.TAG_SCORECARD);
        },
        isTilePicture: function(row) {
            return row.picture && row.indent < 2;
        },
        isAssessmentUnit: function(row) {
            return this.isEnumUnit(row) && row.default_unit.slug === 'assessment';
        },
        isFreetextUnit: function(row) {
            var vm = this;
            return vm.isPractice(row) &&
                row.default_unit && row.default_unit.slug === 'freetext';
        },
        isDatetimeUnit: function(row) {
            var vm = this;
            return vm.isPractice(row) && (row.default_unit.system === 'datetime');
        },
        isNumberUnit: function(row) {
            var vm = this;
            return !(vm.isEnergyUIHint(row) || vm.isGHGEmissions(row) ||
                    vm.isWaterUIHint(row) || vm.isWasteUIHint(row) ||
                    vm.isEmployeeCountUIHint(row)) &&
                vm.isPractice(row) &&
                (row.default_unit.system === 'standard' ||
                row.default_unit.system === 'imperial' ||
                row.default_unit.system === 'rank');
        },
        freezeAssessment: function($event) {
            var vm = this;
            vm.freezeAssessmentDisabled = true;
            vm.reqPost(vm.api_assessment_freeze, {is_frozen: true},
            function success(resp) {
                vm.freezeAssessmentDisabled = false;
                vm.$nextTick(function() {
                    var modalDialog = jQuery('#complete-assessment.modal');
                    if( modalDialog ) modalDialog.modal('hide');
                    if( resp.location ) {
                        window.location = resp.location;
                    }
                });
            },
            function error(resp) {
                vm.freezeAssessmentDisabled = false;
                vm.$nextTick(function() {
                    var modalDialog = jQuery('#complete-assessment.modal');
                    if( modalDialog ) modalDialog.modal('hide');
                    vm.showErrorMessages(resp);
                });
            });
        },
        openLink: function(event) {
            var vm = this;
            var href = event.target.getAttribute('href');
            var pathname = event.target.pathname;
            if( href ) {
                if( href.startsWith(vm.upload_complete_url) ||
                    pathname.startsWith(vm.upload_complete_url) ) {
                    // handles both cases, `upload_complete_url` is a fully
                    // qualified URL or just a path.
                    vm.reqGet(pathname,
                    function(resp) {
                        window.open(resp.location, '_blank');
                    });
                } else {
                    window.open(href, '_blank');
                }
            }
        },
        resetAssessment: function($event, prefix) {
            var vm = this;
            var form = $($event.target);
            var modalDialog = form.parents('.modal');
            modalDialog.modal('hide');
            var path = vm.activeTile.path;
            vm.reqPost(vm._safeUrl(vm.api_assessment_reset, vm.prefix + path),
            function success(resp) {
                vm.items = {results: [], count: 0};
                vm.itemsLoaded = false;
                vm.get();
            });
        },
        setActiveElement: function(practice) {
            this.activeTile = practice;
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
    },
    computed: {
        showScorecardToggle: function() {
            return parseInt(this.scorecardToggle) > 0;
        },
    },
    watch: {
        itemsLoaded: function (val) {
            // This method does not override the implementation
            // in `practicesListMixin`. Instead it runs both alongside each
            // other.
            var vm = this;
            vm.verificationStatus = vm.items.verified_status;
        },
    }
});


/** Component used to display requested scorecards

    used in app/scorecard/history.html
 */
Vue.component('scorecard-requests', {
    mixins: [
        itemListMixin,
        accountDetailMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_requests,
            params: {state: "request-initiated"},
            api_accounts_url: this.$urls.api_organizations,
            api_sample_list_url: this.$urls.api_sample_list,
            api_portfolios_grants_url: this.$urls.survey_api_portfolios_grants,
            api_requests_resend_url: this.$urls.api_requests_resend,
            getCompleteCb: 'getCompleted',
            byCampaigns: {},
            contact: {email: ""}
        }
    },
    methods: {
        accept: function(portfolio, idx) {
            var vm = this;
            vm.reqPost(portfolio.api_accept,
            function(resp) { // success
                portfolio.done = true;
                vm.$forceUpdate();
            });
        },
        ignore: function(portfolio, idx) {
            var vm = this;
            vm.reqDelete(portfolio.api_accept,
            function(resp) { // success
            // We would like to do something like `vm.items.results.splice(idx,
            // 1);`, but even with a `$forceUpdate`, there is no change on the
            // page.
                vm.reload();
            });
        },
        getCompleted: function(){
            var vm = this;
            vm.mergeResults = false;
            vm.byCampaigns = {};
            for( let idx =0; idx < vm.items.results.length; ++idx ) {
                const item = vm.items.results[idx];
                const campaign =
                      item.campaign.slug ? item.campaign.slug : item.campaign;
                if( !(campaign in vm.byCampaigns) ) {
                    vm.$set(vm.byCampaigns, campaign, {
                        campaign: item.campaign,
                        expected_behavior: 'share',//'share', 'update', 'create'
                        requests: [],
                        grantCandidates: []
                    });
                }
                if( item.expected_behavior === 'update' &&
                  vm.byCampaigns[campaign].expected_behavior === 'share' ) {
                    vm.byCampaigns[campaign].expected_behavior = 'update';
                } else if ( item.expected_behavior === 'create' &&
                  (vm.byCampaigns[campaign].expected_behavior === 'update' ||
                   vm.byCampaigns[campaign].expected_behavior === 'share') ) {
                    vm.byCampaigns[campaign].expected_behavior = 'create';
                }
                vm.byCampaigns[campaign].requests.push(item);
            }
            if( vm.api_sample_list_url ) {
                let params = Object.assign({}, vm.params);
                params.state = 'completed';
                vm.reqGet(vm.api_sample_list_url, params,
                function(resp) {
                    for( let idx = 0; idx < resp.results.length; ++idx ) {
                        const item = resp.results[idx];
                        const campaign = item.campaign.slug ?
                            item.campaign.slug : item.campaign;
                        if( !(campaign in vm.byCampaigns) ) {
                            vm.$set(vm.byCampaigns, campaign, {
                                campaign: item.campaign,
                                last_completed_at: item.created_at,
                                expected_behavior: 'share',
                                requests: [],
                                grantCandidates: []
                            });
                        }
                        if( !vm.byCampaigns[campaign].last_completed_at ||
                          vm.byCampaigns[campaign].last_completed_at
                            < item.created_at) {
                            vm.byCampaigns[campaign].last_completed_at =
                                item.created_at;
                        }
                        for( let gdx = 0; gdx < item.grantees.length;
                             ++gdx ) {
                            const granteeCandidate = item.grantees[gdx];
                            let found = false;
                            for( let rdx = 0;
                                 rdx < vm.byCampaigns[campaign].requests.length;
                                 ++rdx ) {
                                const request =
                                      vm.byCampaigns[campaign].requests[rdx];
                                if( request.grantee === granteeCandidate ) {
                                    found = true;
                                    break;
                                }
                            }
                            if( !found ) {
                                // Implementation Note: We rely on the API
                                // returning a list sorted by `created_at` here.
                                if( item.created_at <
                                  vm.byCampaigns[campaign].last_completed_at ) {
                                 vm.byCampaigns[campaign].grantCandidates.push({
                                     grantee: granteeCandidate,
                                     campaign: campaign,
                                     last_shared_at: item.created_at
                                 });
                                }
                            }
                            if( vm.byCampaigns[campaign].campaign.account === granteeCandidate ) {
                                vm.byCampaigns[campaign].skipAccountGrantCandidate = true;
                            }
                        }
                    } // /resp.results.length
                    for(fieldName in vm.byCampaigns) {
                        if( vm.byCampaigns.hasOwnProperty(fieldName) ) {
                            const item = vm.byCampaigns[fieldName];
                            // Let's see if we need to add `campaign.account`
                            // to the list of grantCandidates.
                            if( !(item.campaign.is_commons ||
                                  item.skipAccountGrantCandidate) ) {
                                const granteeCandidate =
                                      item.campaign.account;
                                item.grantCandidates.push({
                                    grantee: granteeCandidate,
                                    campaign: item.campaign.slug
                                });
                            }
                            // Loads profile information (picture and full_name)
                            vm.populateAccounts(
                                item.grantCandidates, 'grantee');
                            if( vm.$refs.grants ) {
                                // Each component has its own cache
                                // of profile details.
                                vm.$refs.grants.populateAccounts(
                                    item.grantCandidates, 'grantee');
                            }
                        }
                    }
                });
            }
            vm.populateAccounts(vm.items.results, 'grantee');
        },
        resendRequests: function($event) {
            var vm = this;
            var form = $($event.target);
            var modalDialog = form.parents('.modal');
            modalDialog.modal('hide');
            vm.reqPost(vm.api_requests_resend_url, vm.contact,
            function(resp) { // success
            });
        },
        submitGrant: function(candidate, campaign) { // XXX deprecated?
            var vm = this;
            vm.reqPost(vm.api_portfolios_grants_url, {
                grantee: {slug: candidate.grantee}, campaign:campaign.slug},
            function(resp) { // success
                candidate.done = true;
                vm.$forceUpdate();
            });
        },
    },
    computed: {
        hasPendingRequests: function() {
            return Object.keys(this.byCampaigns).length > 0;
        }
    },
    mounted: function(){
        var vm = this;
        const campaign = ( vm.$el.dataset && vm.$el.dataset.campaign ) ?
              vm.$el.dataset.campaign : null;
        if( campaign ) {
            vm.params['campaign'] = campaign;
        }
        vm.get();
    }
});


/** Component used to display historical scorecards

    used in app/scorecard/history.html
 */
Vue.component('scorecard-history', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_sample_list,
            params: {state: "completed"},
            api_profiles_url: this.$urls.api_organizations,
            getCompleteCb: 'getCompleted',
        }
    },
    methods: {
        getCompleted: function(){
            var vm = this;
            vm.mergeResults = false;
            const profiles = new Set();
            const foundCampaigns = new Set();
            for( let idx =0; idx < vm.items.results.length; ++idx ) {
                const item = vm.items.results[idx];
                for( let grantee of item.grantees ) {
                    profiles.add(grantee);
                }
                const campaign =
                      item.campaign.slug ? item.campaign.slug : item.campaign;
                if( !foundCampaigns.has(campaign) ) {
                    item.latest = true;
                    foundCampaigns.add(campaign);
                }
            }
            // decorate profiles
            if( profiles.size > 0 ) {
                let queryParams = "?q_f==slug&q=";
                let sep = "";
                for( const profile of profiles ) {
                    queryParams += sep + profile;
                    sep = ",";
                }
                vm.reqGet(vm.api_profiles_url + queryParams,
                function(resp) {
                    let profiles = {}
                    for( let idx = 0; idx < resp.results.length; ++idx ) {
                        const item = resp.results[idx];
                        profiles[item.slug] = item;
                    }
                    for( let idx =0; idx < vm.items.results.length; ++idx ) {
                        const item = vm.items.results[idx];
                        for( let jdx = 0; jdx < item.grantees.length; ++jdx ) {
                            if( item.grantees[jdx] in profiles ) {
                             item.grantees[jdx] = profiles[item.grantees[jdx] ];
                            }
                        }
                    }
                    vm.$forceUpdate();
                }, function() {
                    // Fail silently and run in degraded mode if we cannot load
                    // the profile information (picture, etc.)
                });
            }
        },
    },
    mounted: function(){
        this.get();
    }
});


Vue.component('data-tracker', {
    data: function() {
        return {
            activeTile: null,
        }
    },
    methods: {
        isActiveTile: function(tile) {
            var vm = this;
            return vm.activeTile && vm.activeTile == tile;
        },
        toggleTile: function($event, tile) {
            var vm = this;
            // Change active tab
            if( vm.isActiveTile(tile) ) {
                vm.activeTile = null;
            } else {
                vm.activeTile = tile;
            }
        },
    },
});


var dataMetricTracker = Vue.component('data-metric-tracker', {
    mixins: [
        itemListMixin,
    ],
    props: [
        'initUrl'
    ],
    data: function() {
        return {
            url: this.initUrl ? this.initUrl : null,
            starts_at: (this.$dateRange && this.$dateRange.starts_at) ? this.$dateRange.starts_at : null,
            ends_at: (this.$dateRange && this.$dateRange.ends_at) ? this.$dateRange.ends_at : null,
            newItem: this.clearNewItem(),
            activeItem: null,
            isOpenComments: false,
        }
    },
    methods: {
        clearNewItem: function() {
            return {
                full_name: "",
                extra: {}
            };
        },
        addItem: function() {
            var vm = this;
            if( vm.isInvalidNewItem ) {
                vm.showErrorMessages({"detail": "Please enter all information that defines the new row."});
                return
            }
            var data = {extra: JSON.stringify(vm.newItem.extra)};
            if( vm.newItem.full_name ) {
                data.full_name = vm.newItem.full_name;
            }
            vm.reqPost(vm.url, data,
            function(resp) {
                // XXX default unit is not passed through `resp`
                vm.items.results.push(resp);
                vm.newItem = vm.clearNewItem();
            });
        },
        asUnit: function(amount, destUnit, srcUnit) {
            if( srcUnit === destUnit ) {
                return amount;
            }
            const lookup = srcUnit + '_to_' + destUnit;

            // conversion of Mass units
            const unitEquivMass = {
                'kg_to_lb': 2.20462262,
                'kg_to_t': 0.001,

                'lb_to_g': 453.59237,
                'lb_to_kg': 0.45359237,
                'lb_to_t': 0.00045359237,

                'short-tons_to_lb': 2000,
                'short-tons_to_kg': 907.18474,

                't_to_lb': 2204.62262,
                't_to_kg': 1000,
                't_to_short-tons': 1.10231131,
            };
            const massRatio = unitEquivMass[lookup];
            if( massRatio ) {
                return amount * massRatio;
            }

            // conversion of Volume units
            const unitEquivVolume = {
                'bbl_to_gallons': 42,
                'bbl_to_liters': 158.987295,
                'bbl_to_m3': 0.158987295,

                'ccf_to_bbl': 100,

                'gallons_to_bbl': 0.0238,
                'gallons_to_ccf': 0.00133680555564839,
                'gallons_to_liters': 3.78541178,
                'gallons_to_m3': 0.00378541178,
                'gallons_to_scf': 0.133680555564839,

                'liters_to_gallons': 0.264172052,
                'liters_to_m3': 0.001,
                'liters_to_scf': 0.0353146667115116,

                'm3_to_bbl': 6.28981077,
                'm3_to_gallons': 264.172052,
                'm3_to_liters': 1000,
                'm3_to_scf': 35.3146667115116,

                'scf_to_bbl': 0.178107607,
                'scf_to_ccf': 0.01,
                'scf_to_gallons': 7.48051948,
                'scf_to_liters': 28.3168466,
                'scf_to_m3': 0.0283168466,
            };
            const volumeRatio = unitEquivVolume[lookup];
            if( volumeRatio ) {
                return amount * volumeRatio;
            }

            // conversion of Energy units
            const unitEquivEnergy = {
                'btu_to_kWh': 0.00029307107,
                'btu_to_mmbtu': 0.000001,
                'btu_to_mwh': 0.00000029307107,
                'btu_to_therm': 0.00001,

                'gj_to_kWh': 277.777778,
                'gj_to_mmbtu': 0.94781712,
                'gj_to_mwh': 0.277777778,
                'gj_to_therm': 9.4781712,

                'kWh_to_btu': 3412.14163,
                'kWh_to_gj': 0.0036,
                'kWh_to_kj': 3600,
                'kWh_to_mj': 3.6,
                'kWh_to_mmbtu': 0.00341214163,
                'kWh_to_mwh': 0.001,
                'kWh_to_therm': 0.0341214163513308,

                'mj_to_gj': 0.001,
                'mj_to_kWh': 0.277777778,
                'mj_to_mmbtu': 0.00094781712,
                'mj_to_therm': 0.0094781712,

                'mmbtu_to_btu': 1000000,
                'mmbtu_to_gj': 1.05505585,
                'mmbtu_to_kWh': 293.07107,
                'mmbtu_to_mj': 1000,
                'mmbtu_to_mwh': 0.29307107,
                'mmbtu_to_therm': 10,

                'mwh_to_mmbtu': 3.41214163,
                'mwh_to_kWh': 1000,
                'mwh_to_therm': 34.1214163513308,

                'therm_to_btu': 100000,
                'therm_to_gj': 0.105505585,
                'therm_to_kWh': 29.307107,
                'therm_to_mmbtu': 0.1,
                'therm_to_mwh': 0.029307107,
            };
            const energyRatio = unitEquivEnergy[lookup];
            if( energyRatio ) {
                return amount * energyRatio;
            }

            // conversion of Distance units
            const unitEquivDistance = {
                'km_to_mile': 0.621371192,
                'mile_to_km': 1.609344,
                'mile_to_passenger-mile': 1,
                'mile_to_vehicle-mile': 1,
                'nautical-mile_to_mile': 1.150779,
                'passenger-mile_to_mile': 1,
                'vehicle-mile_to_mile': 1,
            };
            const distanceRatio = unitEquivDistance[lookup];
            if( distanceRatio ) {
                return amount * distanceRatio;
            }

            // XXX
            // ton-mile_to_tonne-km 1.459972
            // tonne-km_to_ton-mile 0.684944642773971
            return NaN;
        },
        isActiveItem: function (row) {
            return this.isOpenComments &&
                this.activeItem && this.activeItem.slug === row.slug;
        },
        openComments: function(row, opened) {
            var vm = this;
            if( vm.activeItem &&
                vm.activeItem.slug === row.slug) {
                if( typeof opened == 'undefined' ) {
                    vm.isOpenComments = !vm.isOpenComments;
                } else {
                    vm.isOpenComments = opened;
                }
            } else {
                vm.activeItem = row;
                vm.isOpenComments = true;
            }
        },
        update: function(row) {
            var vm = this;
            console.warn("XXX update not yet implemented");
            vm.openComments(row, false);
        },
        remove: function(row) {
            var vm = this;
            vm.reqDelete(vm._safeUrl(vm.url, row.rank.toString()),
            function() {
                vm.get();
            });
        },
        _save: function(callback) {
            var vm = this;
            if( !vm.url ) {
                console.warn("url is undefined. data cannot be saved.");
                return;
            }
            if( vm.isInvalidStartsAt || vm.isInvalidEndsAt ) {
                vm.showErrorMessages({"detail": "Please specify a valid reporting period."});
                return;
            }
            vm.reqPost(vm._safeUrl(vm.url, 'values'), {
                baseline_at: vm.starts_at,
                created_at: vm.ends_at,
                items: vm.items.results
            },
            function(resp) {
                if( callback ) {
                    callback(resp);
                } else {
                    for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                        vm.items.results[idx].measured = null;
                    }
                    vm.showMessages(
                        [`${vm.items.length} datapoints have been recorded.`],
                        'success');
                }
            }, function error(resp) {
                // Typically an error is detected when some inventory is missing
                // measured data points.
                const data = resp.data || resp.responseJSON;
                if( data && data.items ) {
                    const items = data.items;
                    for( var idx = 0; idx < items.results.length; ++idx ) {
                        if( items[idx].measured ) {
                            vm.items.results[idx].missing = true;
                        }
                    }
                } else {
                    vm.showErrorMessages(resp);
                }
            });
        },
        save: function() {
            this._save();
        }
    },
    computed: {
        isInvalidStartsAt: function() {
            return isNaN(Date.parse(this.starts_at));
        },
        isInvalidEndsAt: function() {
            return isNaN(Date.parse(this.ends_at));
        },
        isInvalidNewItem: function() {
            return !this.newItem.full_name;
        }
    },
    mounted: function() {
        var vm = this;
        if( vm.url ) {
            vm.get();
        }
    }
});


Vue.component('waste-tracker', dataMetricTracker.extend({
    data: function() {
        return {
            newItem: {
                full_name: "",
                extra: {},
                unit: "t",
            },
        }
    },
    methods: {
        humanizeWasteType: function(wasteType) {
            var result = this.$waste_type[wasteType]
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return wasteType;
        },
    },
    computed: {
        isInvalidNewItem: function() {
            return !this.newItem.full_name || !this.newItem.extra.waste_type;
        }
    }
}));


Vue.component('water-tracker', dataMetricTracker.extend({
    data: function() {
        return {
            newItem: {
                full_name: "",
                extra: {}
            },
        }
    },
    methods: {
        humanizeWaterType: function(waterType) {
            var result = this.$water_type[waterType]
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return waterType;
        },
    },
    computed: {
        isInvalidNewItem: function() {
            return !this.newItem.full_name || !this.newItem.extra.water_type;
        }
    }
}));


var ghgEmissionsEstimator = Vue.component(
    'ghg-emissions-estimator', dataMetricTracker.extend({
    data: function() {
        return {
            emissionsEstimate: 0,
        }
    },
    methods: {
        getEmissionFactors: function(row) {
            return {
                co2_factor: 0,
                ch4_factor: 0,
                n2o_factor: 0,
                biogenic_co2_factor: 0
            };
        },
        estimateCO2: function(row) {
            var vm = this;
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.co2_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateCH4: function(row) {
            var vm = this;
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.ch4_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateN2O: function(row) {
            var vm = this;
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.n2o_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateBiogenicCO2: function(row) {
            var vm = this;
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.biogenic_co2_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateCO2e: function(row) {
            var vm = this;
            // GWP dataset (IPCC assessment): 2014 IPCC Fifth Assessment
            // https://ghgprotocol.org/sites/default/files/standards_supporting/Required%20gases%20and%20GWP%20values_0.pdf
            return vm.estimateCO2(row) +
                vm.estimateCH4(row) * 28 +
                vm.estimateN2O(row) * 265;
        },
       save: function() {
           // We save the energy data points and GHG Emissions estimates
           // in a single API call.
           var vm = this;
           if( !vm.url ) {
               console.warn("url is undefined. data cannot be saved.");
               return;
           }
           if( vm.isInvalidStartsAt || vm.isInvalidEndsAt ) {
               vm.showErrorMessages({
                   "detail": "Please specify a valid reporting period."});
               return;
           }
           var items = [];
           for( var idx = 0; idx < vm.items.results.length; ++idx ) {
               items.push({
                   slug: vm.items.results[idx].slug,
                   measured: vm.items.results[idx].measured,
                   unit: vm.items.results[idx].unit
               })
               items.push({
                   slug: vm.items.results[idx].slug,
                   measured: vm.estimateCO2e(vm.items.results[idx]),
                   unit: "t"
               })
           }
            vm.reqPost(vm._safeUrl(vm.url, 'values'), {
                baseline_at: vm.starts_at,
                created_at: vm.ends_at,
                items: items
            },
            function(resp) {
                for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                    vm.items.results[idx].measured = null;
                }
                vm.showMessages([
                    `${items.length} datapoints have been recorded.`],
                    'success');
            }, function error(resp) {
                // Typically an error is detected when some inventory is missing
                // measured data points.
                const data = resp.data || resp.responseJSON;
                if( data && data.items ) {
                    const results = data.items;
                    for( var idx = 0; idx < results.length; idx += 2 ) {
                        if( results[idx].measured ) {
                            vm.items.results[idx / 2].missing = true;
                        }
                    }
                    vm.$forceUpdate();
                } else {
                    vm.showErrorMessages(resp);
                }
            });
        }
    },
    computed: {
        showEmissionsEstimate: function() {
            return parseInt(this.emissionsEstimate) > 0;
        },
    },
    mounted: function() {
        var vm = this;
        vm.get();
    }
}));



Vue.component('scope1-stationary-combustion', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: this.clearNewItem(),
        }
    },
    methods: {
        clearNewItem: function() {
            return {
                full_name: "",
                extra: {
                    fuel_type: "",
                },
            };
        },
        getEmissionFactors: function(row) {
            return this.$ef_stationary_combustion[row.extra.fuel_type];
        },
        humanizeFuelType: function(fuelType) {
            var result = this.$ef_stationary_combustion[fuelType]
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return fuelType;
        },
    },
    computed: {
        isInvalidNewItem: function() {
            return !this.newItem.full_name || !this.newItem.extra.fuel_type;
        }
    }
}));


Vue.component('scope1-mobile-combustion', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: this.clearNewItem(),
        }
    },
    methods: {
        clearNewItem: function() {
            return {
                full_name: "",
                extra: {
                    activity_type: "",
                    fuel_type: "",
                    vehicle_type: "",
                },
            };
        },
        getEmissionFactors: function(row) {
            const lookup = row.extra.fuel_type + '-' + row.extra.vehicle_type;
            return this.$ef_mobile_combustion[lookup];
        },
        asFuelUse: function(row) {
            var vm = this;
            if( row.extra.activity_type === 'fuel-use' ) {
                return {measured: row.measured, unit: row.unit};
            }
            const lookup = row.extra.fuel_type + '-' + row.extra.vehicle_type;
            const ef_factors = vm.$ef_default_average_fuel_efficiency[lookup];
            if( typeof ef_factors == 'undefined' ) {
                return {measured: NaN};
            }
            const measured = (
                vm.asUnit(row.measured, ef_factors.numerator_unit, row.unit)
                / ef_factors.fuel_efficiency);
            return {measured: measured, unit: ef_factors.denominator_unit};
        },
        estimateCO2: function(row) {
            var vm = this;
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            const fuelUse = vm.asFuelUse(row);
            return ef_factors.co2_factor
                * vm.asUnit(fuelUse.measured, ef_factors.unit, fuelUse.unit) / 1000;
        },
        estimateCH4: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            const fuelUse = vm.asFuelUse(row);
            return ef_factors.ch4_factor
                * vm.asUnit(fuelUse.measured, ef_factors.unit, fuelUse.unit) / 1000;
        },
        estimateN2O: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            const fuelUse = vm.asFuelUse(row);
            return ef_factors.n2o_factor
                * vm.asUnit(fuelUse.measured, ef_factors.unit, fuelUse.unit) / 1000;
        },
        estimateBiogenicCO2: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            const fuelUse = vm.asFuelUse(row);
            return ef_factors.biogenic_co2_factor
                * vm.asUnit(fuelUse.measured, ef_factors.unit, fuelUse.unit) / 1000;
        },

        humanizeActivityType: function(activityType) {
            var result = this.$activity_types[activityType];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return activityType;
        },
        humanizeFuelSource: function(fuelType) {
            var result = this.$fuel_types[fuelType];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return fuelType;
        },
        humanizeVehicleType: function(vehicleType) {
            var result = this.$vehicle_types[vehicleType];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return vehicleType;
        },
    },
    computed: {
        isInvalidNewItem: function() {
            return !this.newItem.full_name ||
                !this.newItem.extra.activity_type ||
                !this.newItem.extra.fuel_type ||
                !this.newItem.extra.vehicle_type;
        }
    }
}));


Vue.component('scope1-refrigerants', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: this.clearNewItem()
        }
    },
    methods: {
        getEmissionFactors: function(row) {
            return this.$ef_refrigerants[row.extra.refrigerant_used];
        },
        humanizeRefrigerantUsed: function(refrigerantUsed) {
            var result = this.$ef_refrigerants[refrigerantUsed];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return refrigerantUsed;
        },
        estimateCO2e: function(row) {
            var vm = this;

            // Decrease in Refrigerant Inventory E = C - D
            const decreaseInRefrigerantInventory = (
                row.begin_inventory_measured - row.end_inventory_measured);
            // Total Refrigerant Purchases/ Acquisitions I = E + F + G
            const totalRefrigerantPurchases = (
                parseFloat(row.purchased_measured) +
                parseFloat(row.returned_by_users_measured) +
                parseFloat(row.returned_after_recycling_measured));
            // Total Refrigerant Sales/Disbursements O = H + I + J + K + L
            const totalRefrigerantSales = (
                parseFloat(row.charged_into_equipment_measured) +
                (parseFloat(row.delivered_to_users_measured) || 0) +
                (parseFloat(row.returned_to_producers_measured) || 0) +
                (parseFloat(row.sent_offsite_for_recycling_measured) || 0) +
                (parseFloat(row.sent_offsite_for_destruction_measured) || 0));
            // Refrigerant Emissions (kilograms) P = E + I - O
            const refrigerantEmissions = (
                decreaseInRefrigerantInventory +
                    totalRefrigerantPurchases -
                    totalRefrigerantSales);

            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            const rowUnit = "t";
            return ef_factors.ar5_factor
                * vm.asUnit(refrigerantEmissions, ef_factors.unit, rowUnit) / 1000;
        },
    },
}));


Vue.component('scope2-purchased-electricity', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: this.clearNewItem()
        }
    },
    methods: {
        clearNewItem: function() {
            return {
                full_name: "",
                extra: {
                    grid: "",
                    calculation_approach: "",
                    type_of_emission_factor: ""
                },
            };
        },
        getEmissionFactors: function(row) {
            if( row.extra.calculation_approach == 'heat-steam' ) {
                return this.$ef_heat_steam[row.extra.calculation_approach];
            }
            if( row.extra.type_of_emission_factor == 'residual-mix' ) {
                return this.$ef_residual_mix_market_based[row.extra.grid];
            }
            return this.$ef_grid_region_location_based[row.extra.grid];
        },
        humanizeGrid: function(grid) {
            var result = this.$ef_grid_region_location_based[grid];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return grid;
        },
        humanizeCalculationApproach: function(calculationApproach) {
            var result = this.$calculation_approach_types[calculationApproach];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return calculationApproach;
        },
        humanizeTypeOfEmissionFactor: function(typeOfEmissionFactor) {
            var result = this.$type_of_emission_factor_types[typeOfEmissionFactor];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return typeOfEmissionFactor;
        },
    },
    computed: {
        isInvalidNewItem: function() {
            return !this.newItem.full_name ||
                !this.newItem.extra.grid ||
                !this.newItem.extra.calculation_approach ||
                !this.newItem.extra.type_of_emission_factor;
        }
    }
}));


Vue.component('scope3-transportation', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: this.clearNewItem(),
        }
    },
    methods: {
        clearNewItem: function() {
            return {
                full_name: "",
                extra: {
                    category: "",
                    emission_factor_dataset: "",
                    mode_of_transport: "",
                    activity_type: "",
                    vehicle_type: ""
                }
            };
        },
        getEmissionFactors: function(row) {
            return this.$ef_scope3_transport[row.extra.vehicle_type];
        },
        humanizeCategory: function(category) {
            var result = this.$scope3_category_types[category];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return category;
        },
        humanizeEmissionFactorDataset: function(emissionFactorDataset) {
             var result = this.$emission_factor_dataset_types[emissionFactorDataset];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return emissionFactorDataset;
        },
        humanizeModeOfTransport: function(modeOfTransport) {
            var result = this.$mode_of_transport_types[modeOfTransport];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return modeOfTransport;
        },
        humanizeActivityType: function(activityType) {
            var result = this.$activity_types[activityType];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return activityType;
        },
        humanizeVehicleType: function(vehicleType) {
            var result = this.$ef_scope3_transport[vehicleType];
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return vehicleType;
        },

        estimateCO2: function(row) {
            var vm = this;
            const ef_factors = vm.getEmissionFactors(row);
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.co2_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
    },
    computed: {
        isInvalidNewItem: function() {
            return !this.newItem.full_name ||
                !this.newItem.extra.category ||
                !this.newItem.extra.emission_factor_dataset ||
                !this.newItem.extra.mode_of_transport ||
                !this.newItem.extra.activity_type ||
                !this.newItem.extra.vehicle_type;
        }
    }
}));


Vue.component('data-values', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {
            url: this.$urls.api_data_values,
        }
    },
    methods: {
        humanizeMeasured: function(item) {
            return item.measured + " " + item.unit;
        },
        humanizeDescription: function(item) {
            var result = (
                item.account.printable_name ? item.account.printable_name : "");
            var sep = item.account.printable_name ? ", " : "";
            var extra = item.account.extra;
            for( var fieldName in extra ) {
                if( extra.hasOwnProperty(fieldName) && extra[fieldName] ) {
                    result += sep + extra[fieldName];
                    sep = ", ";
                }
            }
            return result;
        },
    },
    mounted: function() {
        var vm = this;
        vm.get();
    }
});


/** Lists respondent accounts
 */
Vue.component('respondents-list', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_respondents
        }
    },

    mounted: function(){
        this.get()
    }
});


Vue.component('decorate-profiles', {
    mixins: [
        httpRequestMixin,
        accountDetailMixin
    ],
    props: [
        'elements'
    ],
    data: function() {
        return {
            api_accounts_url: this.$urls.api_accounts,
        }
    },
    mounted: function(){
        var vm = this;
        if( vm.elements ) {
            vm.populateAccounts(vm.elements, 'grantee');
        } else if( vm.$el.dataset && vm.$el.dataset.elements ) {
            vm.populateAccounts(JSON.parse(vm.$el.dataset.elements), 'grantee');
        }
    }
});
