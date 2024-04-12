// Copyright (c) 2024, DjaoDjin inc.
// see LICENSE.

// This file contains mixins to display formatted lists of questions.

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define(['exports'], factory);
    } else if (typeof exports === 'object' && typeof exports.nodeName !== 'string') {
        // CommonJS
        factory(exports);
    } else {
        // Browser true globals added to `window`.
        factory(root);
        // If we want to put the exports in a namespace, use the following line
        // instead.
        // factory((root.djResources = {}));
    }
}(typeof self !== 'undefined' ? self : this, function (exports) {

/** Display headings and questions/practices.
 */
var practicesListMixin = {
    mixins: [
        itemListMixin,
    ],
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
            normalizedScore: 0,
            // benchmark charts
            chartsLoaded: false,
            chartsAvailable: false,
            chartsAPIResp: null,
            charts: {},
            avgNormalizedScore: 0,
            highestNormalizedScore: 0,
            getCompleteCb: 'contentLoaded'
        }
    },
    methods: {
        contentLoaded: function() {
            var vm = this;
            vm.normalizedScore = vm.items.normalized_score;
        },
        getEntries: function(prefix, indent, includeTag) {
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
                        if( typeof includeTag == 'undefined' ||
                            (vm.items.results[idx].extra &&
                            vm.items.results[idx].extra.tags &&
                            vm.items.results[idx].extra.tags.includes(
                                includeTag))) {
                            results.push(vm.items.results[idx]);
                        }
                    }
                } else {
                    if( typeof includeTag == 'undefined' ||
                        (vm.items.results[idx].extra &&
                        vm.items.results[idx].extra.tags &&
                        vm.items.results[idx].extra.tags.includes(
                            includeTag))) {
                        results.push(vm.items.results[idx]);
                    }
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

        chunkBy: function(rows, nbRowsPerBlock) {
            var results = [];
            var block = [];
            for( var idx = 0; idx < rows.length; ++idx ) {
                if( idx % nbRowsPerBlock == 0) {
                    if( block.length > 0 ) results.push(block);
                    block = [];
                }
                block.push(rows[idx]);
            }
            if( block.length > 0 ) results.push(block);
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
            try {
                return (
                    isNaN(rate) || rate === null) ? "" : (rate.toFixed(0) + "%");
            } catch( error ) {
            }
            return "";
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
        getSecondaryAnswers: function(practice) {
            let vm = this;
            if( !practice ) return {};
            if( typeof practice.answers === 'undefined' ||
              practice.answers.length < 1 ) {
                return [];
            }
            if( vm.isUnitEquivalent(
                practice.answers[0].unit, practice.default_unit.slug) ) {
                return practice.answers.slice(1);
            }
            let results = []
            for( let idx = 0; idx < practice.answers.length; ++idx ) {
                if( !vm.isUnitEquivalent(
                    practice.answers[idx].unit, practice.default_unit.slug) ) {
                    results.push(practice.answers[idx]);
                }
            }
            return results;
        },
        // Returns comments from the auditor that verifies the accuracy
        // of an answer.
        getVerificationComments: function(practice) {
            if( typeof practice.notes === 'undefined' ) {
                 practice['notes'] = [];
            }
            if( practice.notes.length < 1 ) {
                practice.notes.push({
                    unit: 'freetext',
                    measured: ""
                });
            }
            return practice.notes[practice.notes.length - 1];
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

        getIntrinsicValue: function(practice, fieldName) {
            if( !(practice.extra && practice.extra.intrinsic_values) ) {
                return 0;
            }
            if( fieldName === 'avg_value' ) {
                if( practice.extra.intrinsic_values.length == 0 ) {
                    return 0;
                }
                if( practice.extra.intrinsic_values['avg_value'] ) {
                    return practice.extra.intrinsic_values['avg_value'];
                }
                let total = 0;
                let nbIntrinsicValues = 0;
                for( var key in practice.extra.intrinsic_values ) {
                    if( practice.extra.intrinsic_values.hasOwnProperty(key) ) {
                        total += practice.extra.intrinsic_values[key];
                        ++nbIntrinsicValues;
                    }
                }
                return Math.round(total / nbIntrinsicValues);
            }
            return practice.extra.intrinsic_values[fieldName] || 0;
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
        getMeasured: function(answer) {
            var vm = this;
            // We rely on enum values to be Human-friendly. We cannot use
            // the `descr` of an enum unit, because that field is used
            // for contextual help.
            return answer.measured;
        },
        getUnit: function(answer) {
            var vm = this;
            if( vm.items.units && answer.unit ) {
                var unit = vm.items.units[answer.unit];
                if( typeof unit !== 'undefined' ) {
                    return vm.items.units[answer.unit];
                }
            }
            return {title: "Not found", system: ""};
        },
        getPrimaryUnit: function(practice) {
            var vm = this;
            var answer = vm.getPrimaryAnswer(practice);
            return vm.getUnit(answer);
        },
        getRate: function(practice, key) {
            if( typeof practice.rate === 'undefined' ) {
                if( typeof practice.values === 'undefined' ) {
                    return 0;
                }
                var total = 0;
                var amount = 0;
                for( var idx = 0; idx < practice.values.length; ++idx ) {
                    total += practice.values[idx][1];
                    if( practice.values[idx][0] === key ) {
                        amount = practice.values[idx][1];
                    }
                }
                if( total <= 0 ) {
                    return 0;
                }
                return Math.round(amount * 100 / total);
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
        indentHeader: function(practice) {
            var vm = this;
            var indentSpace = practice.indent > 0 ? (practice.indent - 1) : 0;
            if( vm.isPractice(practice) ) {
                return "bestpractice indent-header-" + indentSpace;
            }
            return "heading-" + indentSpace + " indent-header-" + indentSpace;
        },
        isDataMetricsHeader: function(row) {
            var vm = this;
            return !vm.isPractice(row) && (
                row.extra && row.extra.tags &&
                (row.extra.tags.includes('data-metrics-header')));
        },
        isEmployeeCountUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'employee-count';
        },
        isEnergyUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) && row.ui_hint === 'energy';
        },
        isEnumUnit: function(row) {
            var vm = this;
            return vm.isPractice(row) &&
                row.default_unit && row.default_unit.system === 'enum';
        },
        isEnumRadioUIHint: function(row) {
            var vm = this;
            return vm.isEnumUnit(row) && (row.ui_hint === 'radio' ||
                row.ui_hint === 'yes-no-comments' ||
                row.ui_hint === 'yes-comments');
        },
        isEnumSelectUIHint: function(row) {
            var vm = this;
            return vm.isEnumUnit(row) && row.ui_hint === 'select'
                && row.default_unit.slug !== 'verifiability';
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
        isGHGEmissionsScope3: function(row) {
            var vm = this;
            return vm.isPractice(row) && (row.ui_hint === 'ghg-emissions-scope3');
        },
        isVerifiabilityUIHint: function(row) {
            var vm = this;
            return vm.isPractice(row) &&
                row.default_unit.slug === 'verifiability';
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
            return row.required && !this.isRequiredAnswered(row);
        },
        isRequiredAnswered: function(row) {
            return row.required && this.getPrimaryAnswer(row).measured;
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
            } else if( default_unit === 'btu-year' ||
                default_unit === 'mmbtu-year' ||
                default_unit === 'kwh-year' ||
                default_unit === 'mwh-year' ||
                default_unit === 'kj-year' ||
                default_unit === 'mj-year' ||
                default_unit === 'gj-year' ) {
                return unit === 'btu-year' ||
                    unit === 'mmbtu-year' ||
                    unit === 'kwh-year' ||
                    unit === 'mwh-year' ||
                    unit === 'kj-year' ||
                    unit === 'mj-year' ||
                    unit === 'gj-year';
            } else if( default_unit === 'tons-year' ||
                default_unit === 'lbs-year' ||
                default_unit === 'm3-year' ||
                default_unit === 'kiloliters-year' ||
                default_unit === 'ft3-year' ||
                default_unit === 'gallons-year' ) {
                return unit === 'tons-year' ||
                unit === 'lbs-year' ||
                unit === 'm3-year' ||
                unit === 'kiloliters-year' ||
                unit === 'ft3-year' ||
                unit === 'gallons-year';
            } else if( default_unit === 'btu' ||
                default_unit === 'mmbtu' ||
                default_unit === 'kWh' ||
                default_unit === 'mwh' ||
                default_unit === 'kj' ||
                default_unit === 'mj' ||
                default_unit === 'gj' ) {
                return unit === 'btu' ||
                    unit === 'mmbtu' ||
                    unit === 'kWh' ||
                    unit === 'mwh' ||
                    unit === 'kj' ||
                    unit === 'mj' ||
                    unit === 'gj';
            } else if( default_unit === 't' ||
                default_unit === 'lbs' ||
                default_unit === 'm3' ||
                default_unit === 'kiloliters' ||
                default_unit === 'ft3' ||
                default_unit === 'gallons' ) {
                return unit === 't' ||
                unit === 'lbs' ||
                unit === 'm3' ||
                unit === 'kiloliters' ||
                unit === 'ft3' ||
                unit === 'gallons';
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

        // benchmark charts
        buildChart: function(data) {
            var vm = this;
            var labels = [];
            var values = [];
            var organizationX = -1;
            const benchmarkValues = (
                data.benchmarks && data.benchmarks.length > 0) ?
                  data.benchmarks[0].values : [];
            if( benchmarkValues.length === 0 ) return;

            for( var idx = 0; idx < benchmarkValues.length; ++idx ) {
                const label = benchmarkValues[idx][0];
                labels.push(label);
                const val = benchmarkValues[idx][1];
                values.push(val);
                if( data.organization_rate == label ) {
                    organizationX = idx;
                }
            }
            var datasets = [];
            var colors = [
                '#f0ad4e', '#f0ad4e',
                '#f0ad4e', '#f0ad4e'];
            datasets.push({
                label: "peers",
                backgroundColor: '#f0ad4e',
                borderColor: '#f0ad4e',
                data: values
            });

            var chartKeys = [data.path, '/summary' + data.path];
            for( var idx = 0; idx < chartKeys.length; ++idx ) {
                var chartKey = chartKeys[idx];
                var element = vm.$el.querySelector('[data-id="' + chartKey + '"]');
                if( element ) {
                    if( vm.charts[chartKey] ) {
                        vm.charts[chartKey].destroy();
                        vm.charts[chartKey] = null;
                    }
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
                                    },
                                    annotation: {
                                      annotations: {
                                        line1: {
                                            type: 'line',
                                            xMin: organizationX,
                                            xMax: organizationX,
                                            borderColor: 'rgb(255, 99, 132)',
                                            borderWidth: 2,
                                        }
                                      }
                                    }
                                }
                            },
                        }
                    );
                } else {
                    vm.charts[chartKey] = {}; // to add `nb_respondents`
                }
                if( data.nb_respondents ) {
                    if( vm.charts[chartKey] ) {
                        vm.charts[chartKey].nb_respondents =
                            data.nb_respondents;
                    }
                }
            }
        },
        isChartAvailable: function (practice) {
            return practice.path in this.charts;
        },
        buildCharts: function(resp) {
            var vm = this;
            if( resp ) {
                for( var idx = 0; idx < resp.length; ++idx ) {
                    for( var jdx = 0; jdx < vm.items.results.length; ++jdx ) {
                        if( vm.items.results[jdx].slug === resp[idx].slug ) {
                            if( !(isNaN(resp[idx].normalized_score) ||
                                  resp[idx].normalized_score == null) ) {
                                vm.items.results[jdx].normalized_score =
                                    resp[idx].normalized_score;
                            }
                            if( !(isNaN(resp[idx].highest_normalized_score) ||
                                 resp[idx].highest_normalized_score == null) ) {
                                vm.items.results[jdx].highest_normalized_score =
                                    resp[idx].highest_normalized_score;
                            }
                            if( !(isNaN(resp[idx].avg_normalized_score) ||
                                 resp[idx].avg_normalized_score == null) ) {
                                vm.items.results[jdx].avg_normalized_score =
                                    resp[idx].avg_normalized_score;
                            }
                            if( resp[idx].hasOwnProperty('benchmarks') ) {
                                vm.items.results[jdx].benchmarks =
                                    resp[idx].benchmarks;
                            }
                            vm.buildChart(resp[idx]);
                            break;
                        }
                    }
                }
            }
            vm.chartsAvailable = true;
            vm.$forceUpdate();
        },
        describeArc: function(x, y, radius, startAngle, endAngle) {
            var innerRadius = radius - this.baseWidth;
            var outerStart = this.polarToCartesian(x, y, radius, startAngle);
            var outerEnd = this.polarToCartesian(x, y, radius, endAngle);
            var innerStart = this.polarToCartesian(x, y, innerRadius, startAngle);
            var innerEnd = this.polarToCartesian(x, y, innerRadius, endAngle);
            var d = [
                "M", outerStart.x, outerStart.y,
                "A", radius, radius, 0, 0, 1, outerEnd.x, outerEnd.y,
                "L", innerEnd.x, innerEnd.y,
                "A", innerRadius, innerRadius, 0, 0, 0, innerStart.x, innerStart.y,
                "Z"
            ].join(" ");
            return d;
        },
        polarToCartesian: function (centerX, centerY, radius, angleInDegrees) {
            var angleInRadians = (angleInDegrees - 180) * Math.PI / 180.0;
            return {
                x: centerX + (radius * Math.cos(angleInRadians)),
                y: centerY + (radius * Math.sin(angleInRadians))
            };
        },
        practiceStyle: function(practice) {
            var vm = this;
            if( practice.extra &&
                practice.extra.tags &&
                practice.extra.tags.includes('verify') ) {
                return 'verifier-notes';
            }
            return '';
        },
        topScoreBottomPath: function(percentage) {
            // path drawing percentage
            return this.describeArc(this.arcWidth / 2, 0,
                this.radiusOuterAngle, 0, (percentage / 100) * 180);
        },
        avgScoreBottomPath: function(percentage) {
            return this.describeArc(this.arcWidth / 2, 0,
                this.radiusOuterAngle - this.baseWidth,
                0, (percentage / 100) * 180);
        },
        ownScoreBottomPath: function(percentage) {
            return this.describeArc(this.arcWidth / 2, 0,
                this.radiusOuterAngle - 2 * this.baseWidth,
                0, (percentage / 100) * 180);
        },
    },
    computed: {
        TAG_PAGEBREAK: function() { return 'pagebreak'; },
        TAG_SCORECARD: function() { return 'scorecard'; },
        NOT_APPLICABLE: function() { return 'Not applicable'; },

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
            // path to write text
//            return this.describeArc(this.arcWidth / 2, this.arcHeight, this.radiusOuterAngle, 0, 180);
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
        if( !vm.itemsLoaded && vm.items.results.length === 0 ) {
            vm.get();
        } else {
            vm.itemsLoaded = true;
        }
        if( vm.account_benchmark_url ) {
            vm.reqGet(vm.account_benchmark_url,
            function(resp) {
                vm.avgNormalizedScore = resp.avg_normalized_score;
                vm.highestNormalizedScore = resp.highest_normalized_score;
                vm.chartsAPIResp = resp.results;
                vm.chartsLoaded = true;
            });
            vm.buildSummaryChart();
        } else {
            vm.chartsLoaded = true;
        }
    }
};

    // attach properties to the exports object to define
    // the exported module properties.
    exports.practicesListMixin = practicesListMixin;
}));


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
