/* Copyright (c) 2017, DjaoDjin inc.
   see LICENSE. */

/* Functionality related to the envconnect API.

   global jQuery,angular
*/

angular.module("envconnectApp", ["ui.bootstrap", "ngRoute", "ngDragDrop",
    "ngSanitize", "envconnectControllers"
    ]).directive('toggleCheckbox', function() {
        /**
         * Directive
         */
        return {
            restrict: 'A',
            transclude: true,
            replace: false,
            require: 'ngModel',
            link: function ($scope, $element, $attr, require) {

                var ngModel = require;

                // update model from Element
                var updateModelFromElement = function() {
                    // If modified
                    var checked = $element.prop('checked');
                    if (checked !== ngModel.$viewValue) {
                        // Update ngModel
                        ngModel.$setViewValue(checked);
                        $scope.$apply();
                    }
                };

                // Update input from Model
                var updateElementFromModel = function() {
                    // Update button state to match model
                    $element.trigger('change');
                };

                // Observe: Element changes affect Model
                $element.on('change', function() {
                    updateModelFromElement();
                });

                // Observe: ngModel for changes
                $scope.$watch(function() {
                    return ngModel.$viewValue;
                }, function() {
                    updateElementFromModel();
                });

                // Initialise BootstrapToggle
                $element.bootstrapToggle();
            }
        };
    }).directive("dndList", function() {
    // directive for a single list
    "use strict";

    return function(scope, element, attrs) {

        // variables used for dnd
        var toUpdate;
        var startIndex = -1;

        // watch the model, so we always know what element
        // is at a specific position
        scope.$watch(attrs.dndList, function(value) {
            toUpdate = value;
        }, true);

        // use jquery to make the element sortable (dnd). This is called
        // when the element is rendered
        $(element[0]).sortable({
            items: "tr",
            start: function (event, ui) {
                // on start we define where the item is dragged from
                startIndex = ($(ui.item).index());
            },
            stop: function (event, ui) {
                // on stop we determine the new index of the
                // item and store it there (-1 because index zero
                // is "Add best practice").
                var startPath = $(ui.item).data("id");
                var newIndex = ($(ui.item).index());
                var attachBelow = $(ui.item).parent().find(
                    "tr:nth-child("+newIndex+")").data("id");
                scope.moveBestPractice(startPath, attachBelow);
            },
            axis: "y"
        });
    };
});

var envconnectControllers = angular.module("envconnectControllers", []);

envconnectControllers.controller("EnvconnectCtrl",
    ["$scope", "$http", "$timeout", "settings",
     function($scope, $http, $timeout, settings) {
    "use strict";
    $scope.dir = {};
    $scope.reverse = false;
    $scope.sortedOnKeys = 0;
    $scope.entries = settings.entries;
    $scope.valueSummaryToggle = settings.valueSummaryToggle;
    $scope.scoreToggle = settings.scoreToggle;

    $scope.TAG_HEADING = 'heading';
    $scope.TAG_SCORECARD = 'scorecard';
    $scope.TAG_SYSTEM = 'system';

    $scope.containsTag = function(bestpractise, tag) {
        return bestpractise.tag && bestpractise.tag.indexOf(tag) >= 0;
    }

    $scope.isImplemented = function (consumption) {
        return (consumption.implemented === 'Yes' || consumption.implemented === 'Work in progress');
    }

    /** Decorates the tree with two sets, ``capturable`` and ``captured``.
        ``capturable`` aggregates the total savings and cost that can be
        captured if a user was to add all best practices not yet implemented
        to the improvement plan.
     */
    $scope.calcSavingsAndCost = function(root) {
        if( typeof root[0] === 'undefined' ) return;
        if( root[0].hasOwnProperty('consumption') && root[0].consumption ) {
            var avg_energy_saving = parseInt(
                root[0].consumption.avg_energy_saving);
            if( isNaN(avg_energy_saving) ) {
                avg_energy_saving = String(root[0].consumption.avg_energy_saving);
                avg_energy_saving = (avg_energy_saving.match(/\*/g) || []).length;
                // convert multiple '*' into a percentage according
                // to the tooltip.
                if( avg_energy_saving >= 5 ) {
                    avg_energy_saving = 0.05;
                } else if( avg_energy_saving === 4 ) {
                    avg_energy_saving = 0.04;
                } else if( avg_energy_saving === 3 ) {
                    avg_energy_saving = 0.025;
                } else if( avg_energy_saving === 2 ) {
                    avg_energy_saving = 0.015;
                } else if( avg_energy_saving <= 1 ) {
                    avg_energy_saving = 0.01;
                }
            }
            var capital_cost = parseInt(root[0].consumption.capital_cost);
            if( isNaN(capital_cost) ) {
                capital_cost = String(root[0].consumption.capital_cost);
                capital_cost = (capital_cost.match(/\$/g) || []).length;
                // convert multiple '*' into a percentage according
                // to the tooltip.
                if( capital_cost >= 5 ) {
                    capital_cost = 0.10;
                } else if( capital_cost === 4 ) {
                    capital_cost = 0.075;
                } else if( capital_cost === 3 ) {
                    capital_cost = 0.035;
                } else if( capital_cost === 2 ) {
                    capital_cost = 0.015;
                } else if( capital_cost <= 1 ) {
                    capital_cost = 0.01;
                }
            }
            if( avg_energy_saving > 1 || capital_cost > 1 ) {
                console.log("error: avg_energy_saving",
                    root[0].consumption.avg_energy_saving,
                    "=>", avg_energy_saving,
                    "capital_cost", root[0].consumption.capital_cost,
                    "=>", capital_cost,
                    root[0].consumption.path);
            }
            var isAvailable = !$scope.isImplemented(root[0].consumption);
            root[0].capturable = {
                avg_energy_saving: isAvailable ? avg_energy_saving : 0,
                capital_cost: isAvailable ? capital_cost : 0
            };
            root[0].captured = {
                avg_energy_saving:
                    (isAvailable && root[0].consumption.planned) ?
                        avg_energy_saving : 0,
                capital_cost:
                    (isAvailable && root[0].consumption.planned) ?
                        capital_cost : 0
            }
        } else {
            var capturable = {avg_energy_saving: 1.0, capital_cost: 1.0};
            var captured = {avg_energy_saving: 1.0, capital_cost: 1.0};
            for( var i = 0; i < root[1].length; ++i ) {
                $scope.calcSavingsAndCost(root[1][i]);
                // available for capture
                capturable.avg_energy_saving
                    *= (1.0 - root[1][i][0].capturable.avg_energy_saving);
                capturable.capital_cost
                    *= (1.0 - root[1][i][0].capturable.capital_cost);
                // captured
                captured.avg_energy_saving
                    *= (1.0 - root[1][i][0].captured.avg_energy_saving);
                captured.capital_cost
                    *= (1.0 - root[1][i][0].captured.capital_cost);
            }
            root[0].capturable = {
                avg_energy_saving: 1.0 - capturable.avg_energy_saving,
                capital_cost: 1.0 - capturable.capital_cost};
            root[0].captured = {
                avg_energy_saving: 1.0 - captured.avg_energy_saving,
                capital_cost: 1.0 - captured.capital_cost};
        }
    };

    $scope.getEntriesRecursive = function(root, prefix) {
        if( root[0].slug === prefix.substring(1) ) {
            return root;
        }
        if( prefix.lastIndexOf(root[0].slug, 1) === 1 ) {
            var newPrefix = prefix.substring(prefix.indexOf("/", 1));
            for( var i = 0; i < root[1].length; ++i ) {
                var found = $scope.getEntriesRecursive(root[1][i], newPrefix);
                if( found ) { return found; }
            }
        } else if( prefix.length > 1 ) {
            // Skip unknown prefixes
            var found = prefix.indexOf('/', 1);
            if( found >= 0 ) {
                var newPrefix = prefix.substring(found);
                return $scope.getEntriesRecursive(root, newPrefix);
            }
        }
        return null;
    };

    $scope.getEntries = function(prefix) {
        var node = $scope.getEntriesRecursive($scope.entries, prefix);
        if( node ) {
            var results = [];
            for( var i = 0; i < node[1].length; ++i ) {
                var header_num = $scope.reverse ? (node[1].length + 1 - i) : i + 1;
                if( node[1][i][0].consumption !== null ) {
                    node[1][i][0].header_num = $scope.reverse ? node[1].length : 0;
                } else {
                    node[1][i][0].header_num = header_num;
                }
                results.push(node[1][i]);
                for( var j = 0; j < node[1][i][1].length; ++j ) {
                    node[1][i][1][j][0].header_num = ($scope.reverse ?
                        header_num - 1 : header_num);
                    results.push(node[1][i][1][j]);
                }
            }
            return results;
        }
        return [];
    };

    $scope.getEntriesByTag = function(prefix, tag) {
        var node = $scope.getEntriesRecursive($scope.entries, prefix);
        if( node ) {
            var results = [];
            for( var i = 0; i < node[1].length; ++i ) {
                if( node[1][i][1].length > 0 ) {
                    if( $scope.containsTag(node[1][i][0], tag) ) {
                        results.push(node[1][i]);
                    }
                    for( var j = 0; j < node[1][i][1].length; ++j ) {
                        if( $scope.containsTag(node[1][i][1][j][0], tag) ) {
                            results.push(node[1][i][1][j]);
                        }
                    }
                } else {
                    if( $scope.containsTag(node[1][i][0], tag) ) {
                        results.push(node[1][i]);
                    }
                }
            }
            return results;
        }
        return [];
    };

    $scope.getPath = function(practice, prefix) {
        if( practice[0].consumption ) {
            return practice[0].consumption.path;
        }
        return prefix + '/' + practice[0].slug;
    };

    /* show and hide columns */
    $scope.hidden = settings.hidden;

    $scope.showHide = function(fieldName, prefix) {
        if( prefix in $scope.hidden ) {
            if( $scope.hidden[prefix][fieldName] ) {
                $scope.hidden[prefix][fieldName] = false;
            } else {
                $scope.hidden[prefix][fieldName] = true;
            }
        }
        $http.put(settings.urls.api_columns + prefix,
            {'slug': fieldName, 'hidden': $scope.hidden[prefix][fieldName]});
    };

    $scope.sortBy = function(fieldName, dir) {
        var newDir = ($scope.dir[fieldName] === "asc") ? "desc" : "asc";
        if( typeof dir !== 'undefined' ) {
            newDir = dir;
        }
        if( newDir === "desc" ) {
            $scope.dir = {};
            $scope.dir[fieldName] = "desc";
            $scope.sortedOnKeys = 1;
            $scope.reverse = true;
        } else {
            $scope.dir = {};
            $scope.dir[fieldName] = "asc";
            $scope.sortedOnKeys = 1;
            $scope.reverse = false;
        }
    };

    // Initial sort order
    // XXX Forcing the initial sort order to ``avg_value`` will make
    // re-ordering of management best practices look random because
    // no avg_value columns is shown for management basics.
    if( settings.sortBy ) {
        for( var fieldName in settings.sortBy ) {
            if ($scope.dir.hasOwnProperty(fieldName)) {
                $scope.sortBy(fieldName, settings.sortBy[fieldName]);
            }
        }
    }

    $scope.sortedOn = function(obj) {
        var key = "" + obj[0].header_num;
        if( typeof obj[0].consumption !== 'undefined'
            && obj[0].consumption !== null ) {
            for( var fieldName in $scope.dir ) {
                if ($scope.dir.hasOwnProperty(fieldName)) {
                    key = key + "-" + obj[0].consumption[fieldName];
                }
            }
            // We always tail the `rank` such that we get a consistent ordering
            // We also "reverse" (in a way) the rank such that descending order
            // looks good.
            key = key + "-" +  (1000000 - obj[0].consumption.rank);
        }
        return key;
    };

    $scope.summaryAvgValue = function(consumption) {
        return Math.round(
            (consumption.environmental_value + consumption.business_value
             + consumption.profitability + consumption.implementation_ease)
                / 4.0);
    };

    $scope.allAnswered = function(tab) {
        var allChecked = true;
        $.each(angular.element(tab).find(".answer"), function(index, element) {
            allChecked &= angular.element(element).find("input[type='radio']").is(":checked");
        });
        return !allChecked;
    }

    // editor functionality
    $scope.prefix = null;
    $scope.tag = null;
    $scope.reload = false;
    $scope.activeElement = null;

    $scope.setPrefix = function(prefix, tag) {
        $scope.prefix = prefix;
        if( typeof tag === 'undefined' ) {
            $scope.tag = null;
        } else {
            $scope.tag = tag;
        }
    };

    $scope.addElement = function(event) {
        var form = angular.element(event.target);
        var title = form.find("[name='title']").val();
        var tag = form.find("[name='tag']").val() || $scope.tag;
        var parent = $scope.prefix.substring(
            $scope.prefix.lastIndexOf('/') + 1);
        var data = {title: title, orig_elements: [parent]};
        if( tag ===  'management' || tag === $scope.TAG_SYSTEM ) {
            data.tag = tag;
        }
        $http.post(settings.urls.api_page_elements, data).then(
            function success(resp) {
                if( $scope.tag === $scope.TAG_HEADING || $scope.tag === $scope.TAG_SYSTEM ) {
                    var node = $scope.getEntriesRecursive(
                        $scope.entries, $scope.prefix);
                    resp.data.consumption = null;
                    node[1].push([resp.data, []]);
                    form.parents('.modal').modal('hide');
                } else if( $scope.tag === 'best-practice' ) {
                    var path = $scope.prefix + '/' + resp.data.slug;
                    $http.post(settings.urls.api_consumptions,
                               {path: path, text: title}).then(
                        function success(resp_consumption) {
                            var node = $scope.getEntriesRecursive(
                                $scope.entries, $scope.prefix);
                            resp.data.consumption = resp_consumption.data;
                            node[1].push([resp.data, []]);
                            form.parents('.modal').modal('hide');
                        },
                        function error() {
                            form.parents('.modal').modal('hide');
                            showErrorMessages(resp);
                        });
                } else {
                    // icon-level are rendered by the template engine
                    // server-side.
                    window.location = window.location;
                }
            },
            function error(resp) {
                form.parents('.modal').modal('hide');
                showErrorMessages(resp);
            });
        return false;
    };

    $scope.editElement = function(event) {
        var form = angular.element(event.target);
        var title = form.find("[name='title']").val();
        var data = {title: title};
        $http.put(settings.urls.api_page_elements
                   + $scope.activeElement.slug + '/', data).then(
            function success(resp) {
                form.parents('.modal').modal('hide');
                if( $scope.reload ) {
                    var captionElement = angular.element(
                        '[href="#tab-' + $scope.activeElement.slug + '"]').find(
                        '.icon-caption');
                    captionElement.text(title);
//                    window.location = "";
                }
            }, function error(resp) {
                form.parents('.modal').modal('hide');
                showErrorMessages(resp);
            });
    };

    $scope.editElementTags = function(path, reload, element) {
        event.preventDefault();
        if( $scope.containsTag(element, $scope.TAG_SCORECARD) ) {
            $http.put(
                settings.urls.api_page_elements + element.slug + '/remove-tags',
                {"tag": $scope.TAG_SCORECARD}).then(
                function success(resp) {
                    element.tag = resp.data.tag;
                }, function error(resp) {
                    showErrorMessage(resp);
                });
        } else {
            $http.put(
                settings.urls.api_page_elements + element.slug + '/add-tags',
                {"tag": $scope.TAG_SCORECARD}).then(
                function success(resp) {
                    element.tag = resp.data.tag;
                }, function error(resp) {
                    showErrorMessage(resp);
                });
        }
    };

    $scope.editConsumption = function(event, practice) {
        angular.element(event.target).editor({
            uniqueIdentifier: "data-id",
            baseUrl : settings.urls.api_consumptions,
            rangeUpdate: function(editable, newVal) {
                editable.attr("class", "green-level-" + newVal);
                practice.consumption[editable.data("key")] = parseInt(newVal);
                $scope.$apply(function() {
                    practice.consumption['avg_value'] = $scope.summaryAvgValue(practice.consumption);
                });
            },
            focus: true
        });
    };

    $scope.nextCell = function(event, practice) {
        event.preventDefault();
        var elem = angular.element(event.target);
        while( elem[0] && elem[0].nodeName !== "TD" ) {
            elem = elem.parent();
        }
        if( elem.next().length === 0 || elem.next().hasClass("total-sep") ) {
            elem = angular.element(elem.parent().find('td')[0]);
        }
        $timeout(function() {
            elem.next().trigger('click');
        }, 0, false);
    }

    $scope.editScoreWeight = function(event) {
        angular.element(event.target).editor({
            uniqueIdentifier: "data-id",
            baseUrl: settings.urls.api_weights,
            focus: true
        });
    };

    $scope.setBestPractice = function(path, reload, element) {
        var bestPracticeId = path;
        var splitIndex = bestPracticeId.lastIndexOf('/');
        var prefix = bestPracticeId.substring(0, splitIndex);
        var slug = bestPracticeId.substring(splitIndex + 1);
        $scope.setPrefix(prefix, slug);
        if ( typeof reload !== "undefined" ) {
            $scope.reload = reload;
        } else {
            $scope.reload = false;
        }
        if( typeof element !== "undefined" ) {
            $scope.activeElement = element;
        }
    };

    $scope.deleteBestPractice = function() {
        var prefix = $scope.prefix;
        var slug = $scope.tag;
        $http.delete(
            settings.urls.api_best_practices + prefix + '/' + slug + '/').then(
            function success(resp) {
                var node = $scope.getEntriesRecursive(
                    $scope.entries, prefix);
                var found = -1;
                for( var i = 0; i <  node[1].length; ++i ) {
                    if( node[1][i][0].slug == slug ) {
                        found = i;
                        break;
                    }
                }
                if( found >= 0 ) {
                    node[1].splice(found, 1);
                }
                if( $scope.reload ) {
                    window.location = "";
                }
            },
            function error(resp) {
                showErrorMessages(resp);
            });
    };

    $scope.bestpractice = null;

    $scope.getBestPracticeCandidates = function(val) {
        if( typeof settings.urls.api_page_elements === "undefined" ) {
            return [];
        }
        return $http.get(settings.urls.api_page_elements, {
            params: {q: val}
        }).then(function(res){
            return res.data.results;
        });
    };

    $scope.copyBestpracticeContent = function() {
        angular.element('#duplicate-content').modal("hide");
        angular.element('[data-key="text"]').html($scope.bestpractice.text);
        angular.element('[data-key="text"]').trigger('blur');
    };

    $scope.moveBestPractice = function(path, attachBelow) {
        $http.patch(settings.urls.api_best_practices + path + '/',
            {attach_below: attachBelow}).then(
            function success(resp) {
                $http.get(
                    settings.urls.api_best_practices + settings.root_prefix + '/').then(
                        function success(resp) {
                            $scope.entries = resp.data;
                        }, function(resp) { // error
                            showErrorMessages(resp);
                        });
            }, function(resp) { // error
                showErrorMessages(resp);
            });
    };


    $scope.score = function(node) {
        if( node.nb_answers == node.nb_questions ) {
            return node.normalized_score;
        }
        return "N/A";
    };

    $scope.toggleMyTSP = function(event, defaultUrl) {
        if( !$scope.scoreToggle ) {
            window.location = settings.urls.totals_chart;
        } else {
            window.location = defaultUrl;
        }
    };

    /** Called when a user clicks on the "Improvement Planning" checkbox.
     */
    $scope.updateImprovement = function(consumption) {
        if( consumption ) {
            if( consumption.planned ) {
                $http.post(settings.urls.api_improvements + consumption.path
                ).then(function success(resp) {
                    $("#improvement-dashboard").data('improvementDashboard').load();
                }, function(resp) { // error
                    showErrorMessages(resp);
                });
            } else {
                $http.delete(settings.urls.api_improvements + consumption.path).then(function success(resp) {
                    $("#improvement-dashboard").data('improvementDashboard').load();
                }, function(resp) { // error
                    showErrorMessages(resp);
                });
            }
        }
        $scope.calcSavingsAndCost($scope.entries);
        if( $scope.savingsChart ) {
            $scope.savingsChart.update(
                $scope.entries[0].captured.avg_energy_saving * 100,
                {maxValue: $scope.entries[0].capturable.avg_energy_saving * 100});
        }
        if( $scope.costChart ) {
            $scope.costChart.update(
                $scope.entries[0].captured.capital_cost * 100,
                {maxValue: $scope.entries[0].capturable.capital_cost * 100});
        }
    };

    var savingsElements = angular.element("#improvement-dashboard").find(".savings");
    if( savingsElements.length > 0 ) {
        $scope.savingsChart = speedometer(savingsElements[0]);
        $scope.savingsChart.render();
    }
    var costElements = angular.element("#improvement-dashboard").find(".cost");
    if( costElements.length > 0 ) {
        $scope.costChart = speedometer(costElements[0]);
        $scope.costChart.render();
    }
    $scope.updateImprovement();
}]);

// XXX copy/pasted from djaodjin-saas-angular.js

envconnectControllers.controller("itemsListCtrl",
    ["$scope", "$http", "$timeout", "settings",
     function($scope, $http, $timeout, settings) {
    "use strict";
    $scope.dir = {};
    $scope.totalItems = 0;
    $scope.opened = { "start_at": false, "ends_at": false };
    $scope.params = {};
    if( settings.sortByField ) {
        $scope.params['o'] = settings.sortByField;
        $scope.params['ot'] = settings.sortDirection || "desc";
        $scope.dir[settings.sortByField] = $scope.params['ot'];
    }
    if( settings.date_range && settings.date_range.start_at ) {
        $scope.params['start_at'] = moment(settings.date_range.start_at).toDate();
    }
    if( settings.date_range && settings.date_range.ends_at ) {
        $scope.params['ends_at'] = moment(settings.date_range.ends_at).toDate()
    };

    $scope.filterExpr = "";
    $scope.itemsPerPage = settings.itemsPerPage; // Must match server-side
    $scope.maxSize = 5;               // Total number of direct pages link
    $scope.currentPage = 1;
    // currentPage will be saturated at maxSize when maxSize is defined.
    $scope.formats = ["dd-MMMM-yyyy", "yyyy/MM/dd", "dd.MM.yyyy", "shortDate"];
    $scope.format = $scope.formats[0];

    // calendar for start_at and ends_at
    $scope.open = function($event, date_at) {
        $event.preventDefault();
        $event.stopPropagation();
        $scope.opened[date_at] = true;
    };

    // Generate a relative date for an instance with a ``created_at`` field.
    $scope.relativeDate = function(at_time) {
        var cutOff = new Date();
        if( $scope.params.ends_at ) {
            cutOff = new Date($scope.params.ends_at);
        }
        var dateTime = new Date(at_time);
        if( dateTime <= cutOff ) {
            return moment.duration(cutOff - dateTime).humanize() + " ago";
        } else {
            return moment.duration(dateTime - cutOff).humanize() + " left";
        }
    };

    $scope.$watch("params", function(newVal, oldVal, scope) {
        var updated = (newVal.o !== oldVal.o || newVal.ot !== oldVal.ot
            || newVal.q !== oldVal.q || newVal.page !== oldVal.page );
        if( newVal.start_at !== oldVal.start_at
            && newVal.ends_at === oldVal.ends_at ) {
            updated = true;
            if( $scope.params.ends_at < newVal.start_at ) {
                $scope.params.ends_at = newVal.start_at;
            }
        } else if( newVal.start_at === oldVal.start_at
            && newVal.ends_at !== oldVal.ends_at ) {
            updated = true;
            if( $scope.params.start_at > newVal.ends_at ) {
                $scope.params.start_at = newVal.ends_at;
            }
        }
        if( updated ) {
            $scope.refresh();
        }
    }, true);

    $scope.filterList = function(regex) {
        if( regex ) {
            if ("page" in $scope.params){
                delete $scope.params.page;
            }
            $scope.params.q = regex;
        } else {
            delete $scope.params.q;
        }
    };

    $scope.pageChanged = function() {
        if( $scope.currentPage > 1 ) {
            $scope.params.page = $scope.currentPage;
        } else {
            delete $scope.params.page;
        }
    };

    $scope.sortBy = function(fieldName) {
        if( $scope.dir[fieldName] == "asc" ) {
            $scope.dir = {};
            $scope.dir[fieldName] = "desc";
        } else {
            $scope.dir = {};
            $scope.dir[fieldName] = "asc";
        }
        $scope.params.o = fieldName;
        $scope.params.ot = $scope.dir[fieldName];
        $scope.currentPage = 1;
        // pageChanged only called on click?
        delete $scope.params.page;
    };

    // True if the entry has completed a self-assessment.
    $scope.isComplete = function(entry) {
        return (typeof entry.normalized_score !== 'undefined');
    };

    $scope.refresh = function() {
        $http.get(settings.urls.api_items,
            {params: $scope.params}).then(
            function(resp) {
                // We cannot watch items.count otherwise things start
                // to snowball. We must update totalItems only when it truly
                // changed.
                if( resp.data.count != $scope.totalItems ) {
                    $scope.totalItems = resp.data.count;
                }
                $scope.items = resp.data;
                for( var idx = 0; idx < $scope.items.results.length; ++idx ) {
                    if( $scope.items.results[idx].request_key ) {
                        $scope.items.results[idx].$resolved = true;
                    }
                }
                $scope.items.$resolved = true;
                $http.get(settings.urls.api_suppliers,
                    {params: $scope.params}).then(
                    function(resp) {
                        for( var idx = 0; idx < $scope.items.results.length; ++idx ) {
                            var found = null;
                            for( var supIdx = 0; supIdx < resp.data.count; ++supIdx ) {
                                if( $scope.items.results[idx].organization.slug
                                    === resp.data.results[supIdx].slug ) {
                                    found = resp.data.results[supIdx];
                                }
                            }
                            $scope.items.results[idx].$resolved = true;
                            if( found !== null ) {
                                $scope.items.results[idx].last_activity_at = found.last_activity_at;
                                $scope.items.results[idx].normalized_score = found.normalized_score;
                            }
                        }
                   }, function(resp) { // error
                        $scope.items = {};
                        $scope.items.$resolved = false;
                        showErrorMessages(resp);
                    });
            }, function(resp) { // error
                $scope.items = {};
                $scope.items.$resolved = false;
                showErrorMessages(resp);
            });
    };

    if( settings.autoload ) {
        $scope.refresh();
    }
}]);


envconnectControllers.controller("relationListCtrl",
    ["$scope", "$controller", "$http", "$timeout", "settings",
    function($scope, $controller, $http, $timeout, settings) {
    "use strict";
    $controller("itemsListCtrl", {
        $scope: $scope, $http: $http, $timeout:$timeout, settings: settings});

    $scope.item = null;

    $scope.getCandidates = function(val) {
        return $http.get(settings.urls.api_candidates, {
            params: {q: val}
        }).then(function(res){
            return res.data.results;
        });
    };

    $scope.create = function() {
        $scope.item.invite = angular.element(
            settings.modalId + " [name='message']").val();
        $http.post(settings.urls.api_items + "?force=1", $scope.item).then(
            function success(resp) {
                // XXX Couldn't figure out how to get the status code
                //   here so we just reload the list.
                $scope.refresh();
                $scope.item = null;
            },
            function error(resp) {
                showErrorMessages(resp);
            });
    };

    $scope.save = function($event) {
        $event.preventDefault();
        $http.post(settings.urls.api_items, $scope.item).then(
            function(success) {
                // XXX Couldn't figure out how to get the status code
                // here so we just reload the list.
                $scope.refresh();
                $scope.item = null;
            },
            function(resp) {
                if( resp.status === 404 ) {
                    $scope.item.email = $scope.item.slug;
                    angular.element(settings.modalId).modal("show");
                } else {
                    showErrorMessages(resp);
                }
            });
    };

    $scope.remove = function ($event, idx) {
        $event.preventDefault();
        $http.delete(settings.urls.api_items
                + $scope.items.results[idx].organization.slug).then(
            function success(resp) {
                $scope.items.results.splice(idx, 1);
            },
            function error(resp) {
                showErrorMessages(resp);
            });
    };
}]);

// XXX end of copy/paste

envconnectControllers.controller("envconnectRequestListCtrl",
    ["$scope", "$controller", "$http", "$timeout", "settings",
    function($scope, $controller, $http, $timeout, settings) {
    "use strict";
    var opts = angular.merge({
        autoload: true,
        sortByField: "full_name",
        sortDirection: "desc",
        modalId: "#new-user-relation",
        urls: {api_items: settings.urls.api_accessibles,
               api_candidates: settings.urls.api_organizations}}, settings);
    $controller("relationListCtrl", {
        $scope: $scope, $http: $http, $timeout:$timeout,
        settings: opts});
}]);


(function ($) {
    "use strict";

    /** Plug-in to connect the self-assessment UI to the API.

        HTML requirements:

        <tr data-id="*consumption.path*">
          <td>
              <input type="radio" name="implemented-*?*" value="Yes">Yes
          </td>
          <td><input type="radio" name="implemented-*?*" value="No">No
          </td>
          <td><input type="checkbox"></td>
        </tr>
    */
    function SelfAssessment(el, options){
        this.element = $(el);
        this.options = options;
        this.init();
    }

    SelfAssessment.prototype = {
        init: function () {
            var self = this;

            self.element.find("input[type=\"radio\"]").change(function(event) {
                var element = $(this);
                var name = element.attr("name").replace("implemented-", "");
                var answer = element.val();
                $.ajax({
                    url: self.options.survey_api_response + "/" + name + "/",
                    method: "PUT",
                    data: JSON.stringify({text: answer}),
                    datatype: "json",
                    contentType: "application/json; charset=utf-8",
                    success: function() { return true; },
                    error: function(resp) { showErrorMessages(resp); }
                });
            });

            self.element.find("input[type=\"checkbox\"]").change(
            function(event) {
                var elem = $(this);
                var consumption = elem.parents("tr").data("id");
                if( !self.options.api_improvement_base ) {
                    showErrorMessages({status: 404});
                    return;
                }
                $.ajax({
                    url: self.options.api_improvement_base + consumption + "/",
                    type: elem.is(":checked") ? "PUT" : "DELETE",
                    contentType: "application/json; charset=utf-8",
                    success: function(data) { return true; },
                    error: function(resp) {  showErrorMessages(resp); }
                });
            });
        },
    };

    $.fn.selfAssessment = function(options) {
        var opts = $.extend( {}, $.fn.selfAssessment.defaults, options );
        return this.each(function() {
            if (!$.data(this, "selfAssessment")) {
                $.data(this, "selfAssessment", new SelfAssessment(this, opts));
            }
        });
    };

    $.fn.selfAssessment.defaults = {
        survey_api_response: null,
        api_improvement_base: null
    };

    /** Plug-in to connect the self-assessment UI to the API.

        HTML requirements:

        <div>
          <div id="#total-score"></div>
          <div class="benchmark"></div>
          <div class="cost"></div>
          <div class="savings"></div>
        </div>
    */
    function ImprovementDashboard(el, options){
        this.element = $(el);
        this.options = options;
        this.init();
    }

    ImprovementDashboard.prototype = {
        init: function () {
            var self = this;
            self.load();
        },

        populate: function (data) {
            var self = this;
            for( var idx = 0; idx < data.length; ++idx ) {
                if( data[idx].slug === "total-score" ) {
                    var totalScoreElement = self.element.find(
                        "#" + data[idx].slug);
                    if( data[idx].scores ) {
                        radialProgress(totalScoreElement[0])
                            .value1(data[idx].scores.highest_normalized_score)
                            .value2(data[idx].scores.avg_normalized_score)
                            .value3(data[idx].scores.normalized_score)
                            .render();
                    } else {
                        totalScoreElement.append("<div class=\"total-score-chart\"><div>N/A - Self assessment questions incomplete</div></div>");
                    }
                    var nbRespondentsElem = self.element.find(
                        "#nb-respondents");
                    if( nbRespondentsElem ) {
                        nbRespondentsElem.text(data[idx].nb_respondents);
                    }
                    var improvementScore = self.element.find(
                        "#improvement-score");
                    if( improvementScore ) {
                        improvementScore.text(data[idx].improvement_score);
                    }
                } else {
                    // distribution chart
                    var benchmarkElement = self.element.find(
                        "#" + data[idx].slug);
                    if( benchmarkElement ) {
                        benchmarkElement.find(
                            ".chart-content").benchmarkChart({
                                title: data[idx].title,
                                scores: data[idx].distribution,
                                nb_answers: data[idx].nb_answers,
                                nb_questions: data[idx].nb_questions});
                    }
                    // score
                    var elemPath = "#" + data[idx].slug + "-score .rollup-score";
                    benchmarkElement = self.element.find(elemPath);
                    if( benchmarkElement ) {
                        if( data[idx].nb_questions > 0
                            && data[idx].nb_answers >= data[idx].nb_questions ) {
                            benchmarkElement.text("" + data[idx].normalized_score + "%");
                        } else {
                            benchmarkElement.text("N/A");
                        }
                    }
                    // score weight
                    elemPath = "#" + data[idx].slug + "-score .rollup-weight";
                    benchmarkElement = self.element.find(elemPath);
                    if( benchmarkElement ) {
                        benchmarkElement.text(data[idx].score_weight.toFixed(1));
                    }
                }
            }
            // XXX update speedometers?
        },

        load: function() {
            var self = this;
            $.ajax({
                type: "GET",
                url: self.options.api_account_benchmark,
                datatype: "json",
                contentType: "application/json; charset=utf-8",
                success: function(data) {
                    self.populate(data);
                },
                error: function(resp) { showErrorMessages(resp); }
            });
        },
    };

    $.fn.improvementDashboard = function(options) {
        var opts = $.extend( {}, $.fn.improvementDashboard.defaults, options );
        return this.each(function() {
            var self = $(this);
            if (!$.data(this, "improvementDashboard")) {
                $.data(this, "improvementDashboard",
                    new ImprovementDashboard(this, opts));
            }
        });
    };

    $.fn.improvementDashboard.defaults = {
        api_account_benchmark: null,
        benchmark: null
    };

})(jQuery);
