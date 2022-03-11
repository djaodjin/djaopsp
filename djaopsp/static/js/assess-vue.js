Vue.component('campaign-questions-list', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        return {
            url: this.$urls.pages.api_content,
            rows: this.$rows,
            valueSummaryToggle: true,
            scoreToggle: false,
            vsPeersToggle: 0,
            activeTile: null,
            activeElement: null,
            activeTargets: "",
            freezeAssessmentDisabled: false,
            isOpenComments: false,
            nbAnswers: this.$sample.nbAnswers,
            nbQuestions: this.$sample.nbQuestions,
            nbRequiredAnswers: this.$sample.nbRequiredAnswers,
            nbRequiredQuestions: this.$sample.nbRequiredQuestions,
        }
    },
    methods: {
        humanizeScoreWeight: function (value, percentage) {
            if( value === 0 ) {
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
        slugify: function (choiceText, rank) {
            if( choiceText ) {
                return choiceText.toLowerCase().replace(' ', '-') + '-' + rank;
            }
            return "";
        },
        containsTag: function(row, tag) {
            if( row && row.extra && row.extra.tags ) {
                for(var idx = 0; idx < row.extra.tags.length; ++idx ) {
                    if( row.extra.tags[idx] === tag ) return true;
                }
            }
            return false;
        },
        getEntries: function(prefix, indent) {
            var vm = this;
            var results = [];
            var idx = 0;
            if( typeof indent !== 'undefined' ) {
                // dealing with tiles
                for( var idx = 0; idx < vm.rows.length; ++idx ) {
                    if( vm.rows[idx].indent == indent ) {
                        results.push(vm.rows[idx]);
                    }
                }
            } else {
                for( ; idx < vm.rows.length; ++idx ) {
                    if( vm.rows[idx].slug == prefix ) {
                        indent = vm.rows[idx].indent;
                        ++idx;
                        break;
                    }
                }
                for( ; idx < vm.rows.length; ++idx ) {
                    if( vm.rows[idx].indent <= indent ) {
                        break;
                    }
                    results.push(vm.rows[idx]);
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
        sortBy: function(field){
            var vm = this;
            var oldDir = vm.sortDir(field);
            vm.$set(vm.params, 'o', oldDir === 'asc' ? ('-' + field) : field);
        },
        asPercent: function(rate) {
            return (!isNaN(rate) ? rate.toFixed(1) : "" + 0) + "%";
        },
        implementationRateStyle: function(rate) {
            return {width: this.asPercent(rate)};
        },
        indentHeader: function(practice, prefix) {
            var indentSpace = practice.indent > 0 ? (practice.indent - 1) : 0;
            if( practice.path ) {
                return "bestpractice indent-header-" + indentSpace;
            }
            return "heading-" + indentSpace + " indent-header-" + indentSpace;
        },
        getAnswerByUnit: function(practice, unit) {
            for( var idx = 0; idx < practice.answers.length; ++idx ) {
                if( practice.answers[idx].unit === unit ) {
                    return practice.answers[idx];
                }
            }
            practice.answers.push({
                unit: unit,
                measured: null
            });
            return practice.answers[practice.answers.length - 1];
        },
        getCommentsAnswer: function(practice) {
            for( var idx = 0; idx < practice.answers.length; ++idx ) {
                if( practice.answers[idx].unit == 'freetext' ) {
                    return practice.answers[idx];
                }
            }
            practice.answers.push({
                measured: "",
                unit: "freetext"
            });
            return practice.answers[practice.answers.length - 1];
        },
        getPrimaryAnswer: function(practice) {
            if( practice.answers.length < 1 ) {
                practice['answers'] = {
                    measured: null
                }
            }
            return practice.answers[0];
        },
        getPrimaryCandidate: function(practice) {
            if( practice.candidates && practice.candidates.length > 0 ) {
                return practice.candidates[0];
            }
            return {measured: null};
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
        isRequiredShown: function(row) {
            var vm = this;
            return row.required && !vm.getPrimaryAnswer(row).measured;
        },
        isActiveCommentsShown: function(practice) {
            var vm = this;
            return vm.isOpenComments && (vm.activeElement &&
                vm.activeElement.slug === practice.slug);
        },
        isNumberUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'number';
        },
        isRevenueUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'number'
                && (row.default_unit.slug === 'usd' ||
                    row.default_unit.slug === 'million-usd');
        },
        isEnergyUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'energy';
        },
        isWaterUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'water';
        },
        isWasteUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'waste';
        },
        isTargetByUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) &&
               row.answers.length > 0 &&
                vm.getPrimaryAnswer(row).ui_hint === 'target-by';
        },
        isTargetBaselineUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'target-baseline';
        },
        isFreetextUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'textarea';
        },
        isYesNoUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.default_unit.slug === 'yes-no';
        },
        isEnumUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && (row.ui_hint === 'radio' ||
                // XXX need to update the database with ui_hint = 'radio'
                row.default_unit.slug === 'assessment' ||
                row.default_unit.slug === 'framework');
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
        isNotApplicable: function(practice) {
            var vm = this;
            return practice.answers.length > 0 &&
                (vm.getPrimaryAnswer(practice).measured === vm.NOT_APPLICABLE);
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
        isPractice: function(row) {
            var vm = this;
            if( row.path !== null ) {
                if( row.extra && row.extra.tags ) {
                    for( var idx = 0; idx < row.extra.tags.length; ++idx ) {
                        if( row.extra.tags[idx] === vm.TAG_PAGEBREAK ) {
                            return false;
                        }
                    }
                }
                return true;
            }
            return false;
        },
        getPath: function(practice) {
            return practice.path;
        },

        // Planned improvements
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
                    vm.scoreToggle = false;
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
            for( var idx = 0; idx < vm.rows.length; ++idx ) {
                var row = vm.rows[idx];
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
              for( ; idx < vm.rows.length; ++idx ) {
                  if( vm.rows[idx].slug === vm.activeTile.slug ) {
                      ++idx;
                      break;
                  }
              }
              for( ; idx < vm.rows.length; ++idx ) {
                  if( vm.rows[idx].indent <= vm.activeTile.indent ) {
                      break;
                  }
                  if( vm.rows[idx].answers ) {
                      for( var jdx = 0;
                           jdx < vm.rows[idx].answers.length; ++jdx ) {
                          vm.rows[idx].answers[jdx].measured = null;
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
                  for( var jdx = 0;  jdx < vm.rows.length; ++jdx ) {
                      if( vm.rows[jdx].path &&
                          vm.rows[jdx].path === resp.results[idx].path ) {
                          vm.rows[jdx].answers = resp.results[idx].answers;
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
            for( ; idx < vm.rows.length; ++idx ) {
                if( vm.rows[idx].slug === heading.slug ) {
                    ++idx;
                    break;
                }
            }
            for( ; idx < vm.rows.length; ++idx ) {
                if( vm.rows[idx].indent <= heading.indent ) {
                    break;
                }
                var row = vm.rows[idx];
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
        TAG_PAGEBREAK: function() { return 'pagebreak'; },
        TAG_ENERGY_EMISSIONS: function() { return 'Energy & Emissions'; },
        TAG_WATER: function() { return 'Water'; },
        TAG_WASTE: function() { return 'Waste'; },
        // Helpers to check value of assessment answers
        YES: function() { return 'Yes'; },
        NEEDS_MODERATE_IMPROVEMENT: function() { return 'Mostly yes'; },
        NEEDS_SIGNIFICANT_IMPROVEMENT: function() { return 'Mostly no'; },
        NO: function() { return 'No'; },
        NOT_APPLICABLE: function() { return 'Not applicable'; },
    },
    mounted: function() {
        var vm = this;
        $("[id^='toggle-value-summary-']").change(function() {
            vm.valueSummaryToggle = $(this).prop('checked');
        });
        $("[id^='toggle-score-']").change(function() {
            vm.scoreToggle = $(this).prop('checked');
        });
        if( !vm.rows ) {
            vm.get();
        } else {
            vm.itemsLoaded = true;
        }
    }
});
