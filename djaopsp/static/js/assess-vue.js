// assess-vue.js

var practicesListMixin = {
    data: function() {
        return {
            items: {
                results: this.$rows ? this.$rows : [],
                count: this.$rows ? this.$rows.length : 0
            },
            params: {
                e: this.$excludeQuestions ? this.$excludeQuestions : null,
            },
            prefix: this.$prefix ? this.$prefix : "",
            api_assessment_sample: this.$urls.api_assessment_sample,
        }
    },
    methods: {
        getEntries: function(prefix, indent) {
            var vm = this;
            var results = [];
            var absIndent = -1;
            var idx = 0;
            if( typeof prefix !== 'undefined' && prefix.length > 0 ) {
                for( ; idx < vm.items.results.length; ++idx ) {
                    if( vm.items.results[idx].slug == prefix ) {
                        absIndent = vm.items.results[idx].indent;
                        ++idx;
                        break;
                    }
                }
            }
            for( ; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].indent <= absIndent ) {
                    break;
                }
                if( typeof indent !== 'undefined' ) {
                    // If an offset is defined, we filter in only
                    // the items at that offset from the root prefix.
                    if( vm.items.results[idx].indent ==
                        (absIndent + indent) ) {
                        results.push(vm.items.results[idx]);
                    }
                } else {
                    results.push(vm.items.results[idx]);
                }
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
                measured: (typeof defaultValue !== 'undefined' ?
                    defaultValue : null)
            });
            return practice.answers[practice.answers.length - 1];
        },
        getAnswerStartsAt: function(practice) {
            // We need to get the dates in a "YYY-MM-DD" format
            // for the <input> tag to behave properly.
            const lastYear = new Date(Date.now()).getFullYear() - 1;
            const startsAt = (
                new Date(lastYear, 0)).toISOString().substr(0, 10);
            if( !practice ) return startsAt;
            return this.getAnswerByUnit(practice, 'starts-at', startsAt);
        },
        getAnswerEndsAt: function(practice) {
            // We need to get the dates in a "YYY-MM-DD" format
            // for the <input> tag to behave properly.
            const lastYear = new Date(Date.now()).getFullYear() - 1;
            const endsAt = (
                new Date(lastYear, 11, 31)).toISOString().substr(0, 10);
            if( !practice ) return endsAt;
            return this.getAnswerByUnit(practice, 'ends-at', endsAt);
        },
        getCommentsAnswer: function(practice) {
            return this.getAnswerByUnit(practice, 'freetext', "");
        },
        getPrimaryAnswer: function(practice) {
            if( !practice ) return {};
            if( typeof practice.answers === 'undefined' ) {
                practice['answers'] = [];
            }
            if( practice.answers.length < 1 ||
                !this.isUnitEquivalent(
                    practice.answers[0].unit, practice.default_unit.slug) ) {
                practice['answers'] = [{
                    unit: practice.default_unit.slug,
                    measured: null,
                    created_at: null
                }].concat(practice['answers']);
            }
            return practice.answers[0];
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
        // returns the planned improvement answer for a practice
        getPrimaryPlanned: function(practice) {
            if( (typeof practice.planned === 'undefined') ||
                practice.planned.length < 1 ) {
                practice['planned'] = [{
                    unit: practice.default_unit.slug,
                    measured: null,
                    created_at: null
                }];
            }
            return practice.planned[0];
        },
        getUnit: function(answer) {
            var vm = this;
            if( vm.items.units && answer.unit ) {
                var unit = vm.items.units[answer.unit];
                if( typeof unit !== 'undefined' ) {
                    return vm.items.units[answer.unit];
                }
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
        isDataMetricsHeader: function(row) {
            var vm = this;
            return !vm.isPractice(row) && (
                row.extra && row.extra.tags &&
                (row.extra.tags.includes('data-metrics-header')));
        },
        isEnergyUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'energy';
        },
        isEnumUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && (row.ui_hint === 'radio' ||
                row.ui_hint === 'yes-no-comments' ||
                row.ui_hint === 'yes-comments');
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
        isEmployeeCountUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'employee-count';
        },
        isPagebreak: function(row) {
            var vm = this;
            return (row.extra && row.extra.pagebreak) ||
                vm.containsTag(row, vm.TAG_PAGEBREAK);
        },
        isPercentageUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'percentage';
        },
        isPractice: function(row) {
            var vm = this;
            if( typeof row.default_unit !== "undefined" ) {
                return row.default_unit !== null;
            }
            if( typeof row.avg_value !== "undefined" ) {
                return row.avg_value !== null;
            }
            return false;
        },
        isRequiredShown: function(row) {
            var vm = this;
            return row.required && !vm.getPrimaryAnswer(row).measured;
        },
        isTargetByUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'target-by';
        },
        isScoredPractice: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.opportunity !== null;
        },
        isUnitEquivalent: function(unit, default_unit) {
            if( default_unit === 'usd' ||
                default_unit === 'million-usd' ||
                default_unit === 'eur' ||
                default_unit === 'million-eur' ) {
                return unit === 'usd' ||
                    unit === 'million-usd' ||
                    unit === 'eur' ||
                    unit === 'million-eur';
            }
            return unit === default_unit;
        },
        isWasteUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'waste';
        },
        isWaterUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'water';
        },
        isSustainabilityUIHint: function(row) {
            // XXX until we find a better way to display implementation
            //     rate and opportunity score on the scorecard.
            var vm = this;
            return vm.isEnumUIHint(row) &&
                row.default_unit && row.default_unit.slug === 'assessment';
        },
        isYesNoUIHint: function(row) {
            var vm = this;
            return vm.isEnumUIHint(row) &&
                row.default_unit && row.default_unit.slug === 'yes-no';
        },
    },
    computed: {
        TAG_PAGEBREAK: function() { return 'pagebreak'; },
        TAG_SCORECARD: function() { return 'scorecard'; },
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
                return 6 / vm.getChoices(practice).length;
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
        getPicture: function(user) {
            if( user && user.picture ) {
                return user.picture;
            }
            return "";
        },
        getPrintableName: function(user) {
            if( user && user.printable_name ) {
                return user.printable_name;
            }
            return user;
        },
        importFromTrackingTool: function(practice) {
            var vm = this;
            var primaryAnswer = vm.getPrimaryAnswer(practice);
            var startsAt = vm.getAnswerStartsAt(practice).measured;
            var endsAt = vm.getAnswerEndsAt(practice).measured;
            vm.reqGet(vm._safeUrl(vm.api_aggregate_metric_base, vm.prefix + practice.path) + '?created_at=' + startsAt + "&ends_at=" + endsAt,
            function(resp) {
                primaryAnswer.measured = resp.measured;
                primaryAnswer.unit = resp.unit;
                vm.$forceUpdate();
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
                    vm.reqGet(vm._safeUrl(vm.$urls.api_profiles, key),
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
            vm.reqPost(vm._safeUrl(vm.api_assessment_sample, '/reset' + path),
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

        // Call on the API to update an assessment answer
        _callUpdateAnswer: function(path, measured,
                                     successCallback, errorCallback) {
            var vm = this;
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
            vm.reqPost(vm._safeUrl(vm.api_assessment_sample, '/answers' +
                vm.prefix + path), data,
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
        updateAssessmentAnswer: function(practice, newValue) {
            var vm = this;
            if( typeof newValue === 'undefined' ) {
                newValue = vm.getPrimaryAnswer(practice);
            }
            vm._callUpdateAnswer(practice.path, newValue,
            function success(resp) {
                if( resp.length ) {
                    for( var idx = 0; idx < resp.length; ++resp ) {
                        var answer = vm.getAnswerByUnit(practice, resp[idx].unit);
                        answer.collected_by = resp[idx].collected_by;
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
        updateAllStartsAt: function(practice) {
            var vm = this;
            var atTime = vm.getAnswerStartsAt(
                practice ? practice : vm.activeElement).measured;
            var practices = vm.getEntries();
            for( var idx = 0; idx < practices.length; ++idx ) {
                var row = practices[idx];
                if( vm.isEnergyUIHint(row) || vm.isGHGEmissions(row) ||
                    vm.isWaterUIHint(row) || vm.isWasteUIHint(row) ) {
                    vm.getAnswerStartsAt(row).measured = atTime;
                }
            }
        },
        updateAllEndsAt: function(practice) {
            var vm = this;
            var atTime = vm.getAnswerEndsAt(
                practice ? practice : vm.activeElement).measured;
            var practices = vm.getEntries();
            for( var idx = 0; idx < practices.length; ++idx ) {
                var row = practices[idx];
                if( vm.isEnergyUIHint(row) || vm.isGHGEmissions(row) ||
                    vm.isWaterUIHint(row) || vm.isWasteUIHint(row) ) {
                    vm.getAnswerEndsAt(row).measured = atTime;
                }
            }
        },
        updateComment: function(text, practice) {
            var vm = this;
            vm.getCommentsAnswer(practice).measured = text;
            vm.updateAssessmentAnswer(practice, vm.getCommentsAnswer(practice))
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
        updatePlannedAnswer: function(practice, newValue) {
            var vm = this;
            if( vm.isPractice(practice) ) {
                var improveUrl = vm._safeUrl(vm.api_improvement_sample,
                    '/answers' + vm.prefix + practice.path);
                if( practice.planned ) {
                    var data = {
                        measured: newValue
                    };
                    vm.setActiveElement(practice);
                    vm.reqPost(improveUrl, data,
                    function success(resp) {
                        var improvementDashboard = $("#improvement-dashboard");
                        if( improvementDashboard.length > 0 )  {
                                improvementDashboard.data(
                                    'improvementDashboard').load();
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
            api_assessment_freeze: this.$urls.api_assessment_freeze,
            account_benchmark_url: this.$urls.api_account_benchmark,
            upload_complete_url: this.$urls.api_asset_upload_complete,
            params: {o: ""},
            chartsLoaded: false,
            chartsAvailable: false,
            chartsAPIResp: null,
            charts: {},
            activeTile: null,
            summaryPerformance: this.$summary_performance ? this.$summary_performance : [],
            freezeAssessmentDisabled: false,
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
                for( var jdx = 0; jdx < vm.items.results.length; ++jdx ) {
                    if( vm.items.results[jdx].slug === resp[idx].slug ) {
                        if( resp[idx].normalized_score ) {
                            vm.items.results[jdx].normalized_score =
                                resp[idx].normalized_score;
                        }
                        if( resp[idx].highest_normalized_score ) {
                            vm.items.results[jdx].highest_normalized_score =
                                resp[idx].highest_normalized_score;
                        }
                        if( resp[idx].avg_normalized_score ) {
                            vm.items.results[jdx].avg_normalized_score =
                                resp[idx].avg_normalized_score;
                        }
                        vm.buildChart(resp[idx]);
                        break;
                    }
                }
            }
            vm.chartsAvailable = true;
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
                                data: vm.summaryPerformance
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
            var practices = vm.getEntries(row.slug);
            for( var idx = 0; idx < practices.length; ++idx ) {
                return vm.getPrimaryUnit(practices[idx]).title;
            }
            return "";
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
        isEnumUnit: function(row) {
            var vm = this;
            return vm.isPractice(row) &&
                row.default_unit && row.default_unit.system === 'enum';
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
            vm.reqPost(vm._safeUrl(vm.api_assessment_sample,
                '/reset' + vm.prefix + path),
            function success(resp) {
                vm.items = {results: [], count: 0};
                vm.itemsLoaded = false;
                vm.get();
            });
        },
        setActiveElement: function(practice) {
            this.activeTile = practice;
        },
        scoreToRotation: function(score) {
            return '' + ((score / 100) * 180 + 180) + 'deg';
        },
        // display with active links
        textAsHtml: function(text) {
            var vm = this;
            if( !text ) {
                return "";
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
        }
    },
    computed: {
        arcWidth: function() {
            return 290;
        },
        arcHeight: function() {
            return 156;
        },
        baseWidth: function() {
            return this.arcWidth / 12;
        },
        radiusOuterAngle: function() {
            return this.arcWidth / 2;
        },
        innerRadius: function() {
            return this.radiusOuterAngle * 0.5;
        },
        topScoreTopPath: function() {
            return 'm ' + this.baseWidth + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 1 ' +
                (this.arcWidth -  this.baseWidth * 2) + ' 0';
        },
        avgScoreTopPath: function() {
            return 'm ' + (this.baseWidth * 2) + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 1 ' +
                (this.arcWidth -  this.baseWidth * 2 * 2) + ' 0';
        },
        ownScoreTopPath: function() {
            return 'm ' + (this.baseWidth * 3) + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 1 ' +
                (this.arcWidth -  this.baseWidth * 2 * 3) + ' 0';
        },
        topScoreBottomPath: function() {
            return 'm 0 0 a ' +
                this.radiusOuterAngle + ' ' +
                this.radiusOuterAngle + ' 0 0 1 ' +
                this.arcWidth + ' 0 l ' +
                (-this.baseWidth) + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 0 ' +
                (- (this.arcWidth - this.baseWidth * 2)) + ' 0 z';
        },
        avgScoreBottomPath: function() {
            return 'm ' + this.baseWidth + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 1 ' +
                (this.arcWidth - this.baseWidth * 2) + ' 0 l ' +
                (-this.baseWidth) + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 0 ' +
                (-(this.arcWidth - this.baseWidth * 2 * 2)) + ' 0  z';
        },
        ownScoreBottomPath: function() {
            return 'm ' + (this.baseWidth * 2) + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 1 ' +
                (this.arcWidth - this.baseWidth * 2 * 2) + ' 0 l ' +
                (-this.baseWidth) + ' 0 a ' +
                this.innerRadius + ' ' +
                this.innerRadius + ' 0 0 0 ' +
                (-(this.arcWidth - this.baseWidth * 2 * 3)) + ' 0 z';
        },
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
        if( vm.account_benchmark_url ) {
            vm.reqGet(vm.account_benchmark_url,
            function(resp) {
                vm.chartsAPIResp = resp;
                vm.chartsLoaded = true;
            });
            vm.buildSummaryChart();
        } else {
            vm.chartsLoaded = true;
        }
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
            url: this.$urls.api_historical_assessments,
        }
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
            url: this.initUrl ? this.initUrl : null, //XXX this.$urls.api_track,
            starts_at: null,
            ends_at: null,
            newItem: {
                facility: "",
                allocation: "",
            },
        }
    },
    methods: {
        addItem: function() {
            var vm = this;
            vm.reqPost(vm.url, {extra: JSON.stringify(vm.newItem)},
            function() {
                vm.items.results.push({extra: vm.newItem});
                vm.newItem = {
                    facility: "",
                    allocation: "",
                }
            });
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
        _save: function() {
            var vm = this;
            if( !vm.url ) {
                console.warning("url is undefined. data cannot be saved.");
                return;
            }
            vm.reqPost(vm._safeUrl(vm.url, 'values'), {
                baseline_at: vm.starts_at,
                created_at: vm.ends_at,
                items: vm.items.results
            },
            function(resp) {
                for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                    vm.items.results[idx].measured = null;
                }
                vm.showMessages(["datapoints have been recorded."], 'success');
            });
        },
        save: function() {
            this._save();
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
                facility: "",
                allocation: "",
                waste_type: "",
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
    }
}));


Vue.component('water-tracker', dataMetricTracker.extend({
    data: function() {
        return {
            newItem: {
                facility: "",
                allocation: "",
                water_type: "",
            },
        }
    },
    methods: {
        humanizeWaterType: function(waterType) {
            var result = this.$waste_type[waterType]
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
            return waterType;
        },
    }
}));


var ghgEmissionsEstimator = Vue.component('ghg-emissions-estimator', dataMetricTracker.extend({
    data: function() {
        return {
            emissionsEstimate: 0,
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
            vm.reqPost(vm.url, {extra: JSON.stringify(vm.newItem)},
            function() {
                vm.items.results.push({extra: vm.newItem});
                vm.newItem = {
                    facility: "",
                    fuel_type: "",
                    allocation: "",
                }
            });
        },
        humanizeFuelType: function(fuelType) {
            var result = this.$ef_stationary_combustion[fuelType]
            if( typeof result !== 'undefined' ) {
                return result.title;
            }
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
            const ef_factors = vm.$ef_stationary_combustion[row.extra.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.co2_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateCH4: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.extra.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.ch4_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateN2O: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.extra.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.n2o_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateCO2e: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.extra.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.co2_factor
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        estimateBiogenicCO2: function(row) {
            var vm = this;
            // Go to Data > Define range ...
            // EF_Stationary_Combustion: $'Emission Factors'.$B$10:$K$83
            // Custom_EF: $Parameters.$C$65:$N$94
            const ef_factors = vm.$ef_stationary_combustion[row.extra.fuel_type];
            if( typeof ef_factors == 'undefined' ) {
                return NaN;
            }
            return ef_factors.biogenic_co2_factor // XXX
                * vm.asUnit(row.measured, ef_factors.unit, row.unit) / 1000;
        },
        save: function() {
            // XXX Save energy inputs and GHG Emissions estimates;
            this._save();
        }
    },
}));


Vue.component('scope1-mobile-combustion', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: {
                fuel_type: "",
                activity_type: ""
            },
        }
    },
    methods: {
        humanizeActivityType: function(activityType) {
            return activityType; // XXX
        },
        humanizeFuelSource: function(fuelSource) {
            return fuelSource; // XXX
        },
        humanizeVehicleType: function(vehicleType) {
            return vehicleType; // XXX
        },
    },
}));


Vue.component('scope1-refrigerants', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: {}
        }
    },
    methods: {
        humanizeRefrigerantUsed: function(refrigerantUsed) {
            return refrigerantUsed; // XXX
        },
    },
}));


Vue.component('scope2-purchased-electricity', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: {
                calculationApproach: "",
                type_of_emission_factor: ""
            },
        }
    },
    methods: {
        humanizeCalculationApproach: function(calculationApproach) {
            return calculationApproach; // XXX
        },
        humanizeTypeOfEmissionFactor: function(typeOfEmissionFactor) {
            return typeOfEmissionFactor; // XXX
        },
    },
}));


Vue.component('scope3-transportation', ghgEmissionsEstimator.extend({
    data: function() {
        return {
            newItem: {}
        }
    },
    methods: {
        humanizeCategory: function(category) {
            return category;
        },
        humanizeModeOfTransport: function(modeOfTransport) {
            return modeOfTransport;
        },
        humanizeActivityType: function(activityType) {
            return activityType;
        },
        humanizeVehicleType: function(vehicleType) {
            return vehicleType;
        },
    },
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
            var result = "";
            var sep = "";
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
