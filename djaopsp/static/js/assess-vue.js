// assess-vue.js

var practicesListMixin = {
    data: function() {
        return {
            items: {
                results: this.$rows ? this.$rows : [],
                count: this.$rows ? this.$rows.length : 0
            },
            params: {},
        }
    },
    methods: {
        getEntries: function(prefix, indent) {
            var vm = this;
            var results = [];
            if( typeof indent !== 'undefined' ) {
                // dealing with tiles
                for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                    if( vm.items.results[idx].indent == indent ) {
                        results.push(vm.items.results[idx]);
                    }
                }
            } else {
                indent = -1;
                var idx = 0;
                if( typeof prefix !== 'undefined' ) {
                    for( ; idx < vm.items.results.length; ++idx ) {
                        if( vm.items.results[idx].slug == prefix ) {
                            indent = vm.items.results[idx].indent;
                            ++idx;
                            break;
                        }
                    }
                }
                for( ; idx < vm.items.results.length; ++idx ) {
                    if( vm.items.results[idx].indent <= indent ) {
                        break;
                    }
                    results.push(vm.items.results[idx]);
                }
                var fieldName = vm.params.o;
                if( fieldName ) {
                    var headerNum = 0;
                    for( var idx = 0; idx < results.length; ++idx ) {
                        if( !vm.isPractice(results[idx]) ) {
                            ++headerNum;
                        }
                        results[idx]['headerNum'] = headerNum;
                    }
                    if( fieldName && fieldName.indexOf('-') === 0 ) {
                        fieldName = fieldName.substr(1);
                        results.sort(function(left, right) {
                            if( left.headerNum < right.headerNum ) {
                                return -1;
                            }
                            if( left.headerNum === right.headerNum ) {
                                if( left[fieldName] > right[fieldName] ) {
                                    return -1;
                                }
                                if( left[fieldName] === right[fieldName] ) {
                                    if( left.rank < right.rank ) {
                                        return -1;
                                    }
                                    if( left.rank === right.rank ) {
                                        return 0;
                                    }
                                }
                            }
                            return 1;
                        });
                    } else {
                        results.sort(function(left, right) {
                            if( left.headerNum < right.headerNum ) {
                                return -1;
                            }
                            if( left.headerNum === right.headerNum ) {
                                if( left[fieldName] < right[fieldName] ) {
                                    return -1;
                                }
                                if( left[fieldName] === right[fieldName] ) {
                                    if( left.rank < right.rank ) {
                                        return -1;
                                    }
                                    if( left.rank === right.rank ) {
                                        return 0;
                                    }
                                }
                            }
                            return 1;
                        });
                    }
                }
            }
            return results;
        },

        // Rendering helpers
        _getValForActiveAccount: function(practice, fieldName) {
            if( typeof practice.accounts !== 'undefined' ) {
                for( var key in practice.accounts ) {
                    if( practice.accounts.hasOwnProperty(key) ) {
                        if( typeof practice.accounts[key][fieldName]
                            !== 'undefined' ) {
                            return practice.accounts[key][fieldName];
                        } else {
                            return 0;
                        }
                    }
                }
            }
            return 0;
        },
        asPercent: function(rate) {
            return isNaN(rate) ? "" : (rate.toFixed(0) + "%");
        },
        containsTag: function(row, tag) {
            var result = false;
            if( row && row.extra && row.extra.tags ) {
                for(var idx = 0; idx < row.extra.tags.length; ++idx ) {
                    if( row.extra.tags[idx] === tag ) {
                        result = true;
                        break;
                    }
                }
            }
            return result;
        },
        getAnswerByUnit: function(practice, unit, defaultValue) {
            if( typeof practice.answers === 'undefined' ) {
                 practice['answers'] = [];
            }
            for( var idx = 0; idx < practice.answers.length; ++idx ) {
                if( practice.answers[idx].unit === unit ) {
                    return practice.answers[idx];
                }
            }
            practice.answers.push({
                unit: unit,
                measured: (defaultValue ? defaultValue : null)
            });
            return practice.answers[practice.answers.length - 1];
        },
        getCommentsAnswer: function(practice) {
            return this.getAnswerByUnit(practice, 'freetext', "");
        },
        getOpportunity: function(practice) {
            var vm = this;
            if( vm.isNotApplicable(practice) ) {
                return "N/A";
            }
            if( practice.opportunity ) {
                return practice.opportunity.toFixed(2);
            }
            var opportunityNumerator = vm._getValForActiveAccount(
                practice, 'opportunity_numerator');
            return opportunityNumerator.toFixed(2);
        },
        getPrimaryAnswer: function(practice) {
            if( (typeof practice.answers === 'undefined') ||
                practice.answers.length < 1 ) {
                practice['answers'] = [{
                    measured: null
                }];
            }
            return practice.answers[0];
        },
        // returns the planned improvement answer for a practice
        getPrimaryPlanned: function(practice) {
            if( (typeof practice.planned !== 'undefined') &&
                practice.planned.length > 0 ) {
                for( var idx = 0; idx < practice.planned.length; ++idx ) {
                    if( practice.planned[idx].unit
                        === practice.default_unit.slug ) {
                        return practice.planned[idx];
                    }
                }
            }
            return null;
        },
        getUnit: function(answer) {
            var vm = this;
            if( vm.items.units && answer.unit ) {
                return vm.items.units[answer.unit];
            }
            return {title: "Not found"};
        },
        getPrimaryUnit: function(practice) {
            var vm = this;
            var answer = vm.getPrimaryAnswer(practice);
            return vm.getUnit(answer);
        },
        getRate: function(practice, key) {
            if( typeof practice.rate === 'undefined' ) {
                return 0;
            }
            if( typeof key !== 'undefined' ) {
                return practice.rate[key];
            }
            if( !isNaN(practice.rate) ) {
                return practice.rate;
            }
            const YES = 'Yes';
            const MOSTLY_YES = 'Mostly yes';
            const yesRate = practice.rate[YES] || 0;
            const mostlyYesRate = practice.rate[MOSTLY_YES] || 0;
            return yesRate + mostlyYesRate;
        },
        isNotApplicable: function(practice) {
            var vm = this;
            return practice.answers && (practice.answers.length > 0) &&
                (vm.getPrimaryAnswer(practice).measured === vm.NOT_APPLICABLE);
        },
        implementationRateStyle: function(rate) {
            return {width: this.asPercent(rate)};
        },
        isPagebreak: function(row) {
            var vm = this;
            return (row.extra && row.extra.pagebreak) ||
                vm.containsTag(row, vm.TAG_PAGEBREAK);
        },
        isPractice: function(row) {
            var vm = this;
            if( typeof row.default_unit !== "undefined" ) {
                return row.default_unit !== null;
            }
            return false;
        },
        isEnergyUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'energy';
        },
        isEnumUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'radio';
        },
        isFreetextUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'textarea';
        },
        // GHG Emissions - Scope 1, 2 & 3
        isGHGEmissions: function(row) {
            var vm = this;
            return vm.isPractice(row) && (row.ui_hint === 'ghg-emissions' ||
                row.ui_hint === 'ghg-emissions-scope3');
        },
        // GHG Emissions - Scope 3
        isGHGEmissionsBreakDown: function(row) {
            var vm = this;
            return vm.isPractice(row) && (
                row.ui_hint === 'ghg-emissions-scope3');
        },
        isNumberUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'number';
        },
        isWasteUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'waste';
        },
        isWaterUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'water';
        },
        isYesNoUIHint: function(row) {
            var vm = this;
            return vm.isEnumUIHint(row) &&
                row.default_unit && row.default_unit.slug === 'yes-no';
        },
    },
    computed: {
        TAG_PAGEBREAK: function() { return 'pagebreak'; },
        NOT_APPLICABLE: function() { return 'Not applicable'; },
    },
};


Vue.component('campaign-questions-list', {
    mixins: [
        itemListMixin,
        practicesListMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_content,
            valueSummaryToggle: true,
            vsPeersToggle: 0,
            activeTile: null,
            activeElement: null,
            activeTargets: "",
            freezeAssessmentDisabled: false,
            isOpenComments: false,
            nbAnswers: this.$sample ? this.$sample.nbAnswers : 0,
            nbQuestions: this.$sample ? this.$sample.nbQuestions  : 0,
            nbRequiredAnswers: this.$sample ? this.$sample.nbRequiredAnswers : 0,
            nbRequiredQuestions: this.$sample ? this.$sample.nbRequiredQuestions : 0,
        }
    },
    methods: {
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
        indentHeader: function(practice) {
            var vm = this;
            var indentSpace = practice.indent > 0 ? (practice.indent - 1) : 0;
            if( vm.isPractice(practice) ) {
                return "bestpractice indent-header-" + indentSpace;
            }
            return "heading-" + indentSpace + " indent-header-" + indentSpace;
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
                        var isIdentDescr = true;
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
                        if( isIdentDescr ) {
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
                        row.choices_headers = defaultUnit.choices;
                    }
                }
            }
            return row.choices_headers;
        },
        getNbInputCols: function(icon) {
            var colSpan = this.getChoices(icon).length;
            return colSpan > 0 ? colSpan : 3;
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
        getPicture: function(user) {
            if( user.picture ) {
                return user.picture;
            }
            return "";
        },
        getPrintableName: function(user) {
            if( user.printable_name ) {
                return user.printable_name;
            }
            return user;
        },
        isEnumHeaderShown: function(icon) {
            var vm = this;
            return !vm.containsTag(icon, 'metrics');
        },
        isRequiredShown: function(row) {
            var vm = this;
            return row.required && !vm.getPrimaryAnswer(row).measured;
        },
        isActiveCommentsShown: function(practice) {
            var vm = this;
            return vm.isOpenComments && (vm.activeElement &&
                vm.activeElement.slug === practice.slug);
        },
        isRevenueUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'number'
                && (row.default_unit && (row.default_unit.slug === 'usd' ||
                    row.default_unit.slug === 'million-usd'));
        },
        isTargetByUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) &&
                row.answers && row.answers.length > 0 &&
                vm.getPrimaryAnswer(row).ui_hint === 'target-by';
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
            }
        },
        freezeAssessment: function() {
            var vm = this;
            vm.freezeAssessmentDisabled = true;
            vm.reqPost(vm.$urls.api_assessment_freeze, {is_frozen: true},
            function success(resp) {
                if( resp.location ) {
                    vm.freezeAssessmentDisabled = false;
                    window.location = resp.location;
                }
            },
            function error(resp) {
                vm.freezeAssessmentDisabled = false;
                showErrorMessages(resp);
            });
        },
        populateUserProfiles: function() {
            var profilesBySlug = {};
            for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                var row = vm.items.results[idx];
                if( row.answers ) {
                    for( var jdx = 0; jdx < row.answers.length; ++jdx ) {
                        var answer = row.answers[jdx];
                        if( !profilesBySlug[answer.collected_by] ) {
                            profilesBySlug[answer.collected_by] = 1;
                        }
                    }
                }
            }
            for( var key in profilesBySlug ) {
                if( profilesBySlug.hasOwnProperty(key) ) {
                    vm.reqGet(vm.$urls.api_profiles + '/' + key,
                    function(resp) {
                        profilesBySlug[resp.slug] = resp;
                    });
                }
            }
        },
        resetAssessment: function($event, prefix) {
            var vm = this;
            var form = $($event.target);
            var modalDialog = form.parents('.modal');
            modalDialog.modal('hide');
            var path = (prefix ? prefix : '') + '/' + vm.activeTile.slug;
            vm.reqPost(vm.$urls.api_assessment_sample + '/reset' + path,
            function success(resp) {
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
              // update the number of answers
              vm.nbAnswers = (resp.data && resp.data.nb_answers) ?
                    resp.data.nb_answers : 0;
              vm.nbRequiredAnswers = (
                  resp.data && resp.data.nb_required_answers) ?
                  resp.data.nb_required_answers : 0;
              showMessages([
                  "Reset successful. Please continue with this assessment or an assessment in a different industry segment."],
                  "success");
            },
            function error(resp) {
                showErrorMessages(resp);
            });
        },
        useCandidateAssessment: function($event, prefix) {
            var vm = this;
            var path = (prefix ? prefix : '') + '/' + vm.activeTile.slug;
            vm.reqPost(vm.$urls.api_assessment_sample + '/candidates' + path,
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
            },
            function error(resp) {
                showErrorMessages(resp);
            });
        },

        // Call on the API to update an assessment answer
        _callUpdateAnswer: function(path, measured,
                                     successCallback, errorCallback) {
            var vm = this;
            if( typeof measured !== 'undefined' ) {
                var data = ( vm._isArray(measured) || vm._isObject(measured) ) ?
                    measured : {measured: measured};
                vm.reqPost(vm.$urls.api_assessment_sample + '/answers' + path,
                    data,
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
                    showErrorMessages(resp);
                    if( errorCallback ) {
                        errorCallback(resp);
                    }
                });
            }
        },
        updateAssessmentAnswer: function(practice, newValue) {
            var vm = this;
            vm._callUpdateAnswer(practice.path, newValue,
            function success(resp) {
                if( newValue === vm.NOT_APPLICABLE ) {
                    vm.setActiveElement(practice);
                    vm.isOpenComments = true;
                } else {
                    vm.isOpenComments = false;
                }
                if( resp.question ) {
                    practice.opportunity = resp.question.opportunity;
                    if( resp.first &&
                        $("#assess-content").data("trip-content") ) {
                        var trip = new Trip([{
                            sel: $("#assess-content"),
                            content: $("#assess-content").data("trip-content"),
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
                }
            });
        },
        updateMultipleAssessmentAnswers: function (heading, newValue) {
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
                    vm.getPrimaryAnswer(row).measured = newValue;
                    vm._callUpdateAnswer(row.path, newValue);
                }
            }
        },
        updateImprovement: function(practice, newValue) {
            var vm = this;
            if( vm.isPractice(practice) ) {
                // prevent 2 '/' together.
                var improveUrl = vm.$urls.api_improvement_sample.replace(
                    /\/+$/, "") + '/answers' + practice.path;
                if( practice.planned ) {
                    var data = {
                        measured: newValue
                    };
                    vm.setActiveElement(practice);
                    vm.reqPost(improveUrl, data,
                    function success(resp) {
                        $("#improvement-dashboard").data(
                            'improvementDashboard').load();
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
                    }, function(resp) { // error
                        showErrorMessages(resp);
                    });
                } else {
                    var resetUrl = vm.$urls.api_improvement_sample.replace(
                        /\/+$/, "") + '/reset' + practice.path
                        + '?unit=assessment';
                    vm.reqPost(resetUrl,
                    function success(resp) {
                        $("#improvement-dashboard").data(
                            'improvementDashboard').load();
                    }, function(resp) { // error
                        showErrorMessages(resp);
                    });
                }
            }
        },
        setActiveElement: function(practice) {
            this.activeElement = practice;
        },
        openComments: function(practice) {
            var vm = this;
            if( vm.activeElement &&
                vm.activeElement.slug === practice.slug) {
                vm.isOpenComments = !vm.isOpenComments;
            } else {
                vm.setActiveElement(practice);
                vm.isOpenComments = true;
            }
        },
    },
    computed: {
        BEST_PRACTICE_ELEMENT: function() { return 'best-practice'; },
        HEADING_ELEMENT: function() { return 'heading'; },
        TAG_SCORECARD: function() { return 'scorecard'; },
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
        if( vm.items.results.length === 0 ) {
            vm.get();
        } else {
            vm.itemsLoaded = true;
        }
    }
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


/** Component used to display historical scorecards

    used in app/scorecard/history.html
 */
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



Vue.component('ghg-emissions-calculator', {
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


Vue.component('scope1-stationary-combustion', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {
            url: null,
            emissionsEstimate: 0,
            newItem: {
                facility: "",
                fuel_type: "",
                allocation: "",
            },
        }
    },
    methods: {
        addItem: function() {
            var vm = this;
            vm.items.results.push(vm.newItem);
            vm.newItem = {
                facility: "",
                fuel_type: "",
                allocation: "",
            }
        },
        humanizeFuelType: function(fuelType) {
            return fuelType;
        },
        asUnit: function(amount, destUnit, srcUnit) {
            // Energy
            if( destUnit == 'mmbtu' ) {
                if( srcUnit == 'mmbtu' ) {
                    return amount;
                }
            }
            return NaN;
        },
        estimateCO2: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.co2_factor
                * vm.asUnit(row.amount, ef_factors.unit, row.unit) / 1000;
        },
        estimateCH4: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.ch4_factor
                * vm.asUnit(row.amount, ef_factors.unit, row.unit) / 1000;
        },
        estimateN2O: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.n2o_factor
                * vm.asUnit(row.amount, ef_factors.unit, row.unit) / 1000;
        },
        estimateCO2e: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.co2_factor
                * vm.asUnit(row.amount, ef_factors.unit, row.unit) / 1000;
        },
        estimateBiogenicCO2: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.biogenic_co2_factor // XXX
                * vm.asUnit(row.amount, ef_factors.unit, row.unit) / 1000;
        },
        save: function() {
        }
    },
    computed: {
        showEmissionsEstimate: function() {
            return parseInt(this.emissionsEstimate) > 0;
        },
    },
    mounted: function() {
        var vm = this;
        vm.items.count = 1;
        vm.items.results = [{
            facility: "Main factory",
            fuel_type: "natural-gas",
            allocation: "PG&E",
            created_at: null,
            ends_at: null,
            amount: 100,
            unit: "mmbtu"
        }
        ];
        vm.itemsLoaded = true;
    }
});


Vue.component('scope1-mobile-combustion', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {
            url: null,
            emissionsEstimate: 0,
            newItem: {
                fuel_type: "",
                activity_type: ""
            },
        }
    },
    methods: {
    },
    computed: {
        showEmissionsEstimate: function() {
            return parseInt(this.emissionsEstimate) > 0;
        },
    },
});


Vue.component('scope1-refrigerants', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {
            url: null,
            emissionsEstimate: 0,
            newItem: {}
        }
    },
    methods: {
    },
    computed: {
        showEmissionsEstimate: function() {
            return parseInt(this.emissionsEstimate) > 0;
        },
    },
});


Vue.component('scope2-purchased-electricity', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {
            url: null,
            emissionsEstimate: 0,
            newItem: {
                type_of_emission_factor: ""
            },
        }
    },
    methods: {
    },
    computed: {
        showEmissionsEstimate: function() {
            return parseInt(this.emissionsEstimate) > 0;
        },
    },
});


Vue.component('scope3-transportation', {
    mixins: [
        itemListMixin,
    ],
    data: function() {
        return {
            url: null,
            emissionsEstimate: 0,
            newItem: {}
        }
    },
    methods: {
    },
    computed: {
        showEmissionsEstimate: function() {
            return parseInt(this.emissionsEstimate) > 0;
        },
    },
});
