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
                // item and store it there.
                // XXX startIndex and newIndex will look bigger than expected
                // because of the way the Value/Profitability table is built.
                // (i.e. twice the number of rows).
                var rank = 0;
                var movedPath = $(ui.item).data("id");
                var movedNode = scope.getEntriesRecursive(
                    scope.entries, movedPath);

                var newIndex = ($(ui.item).index());
                // We use `nth-child` here because `children().eq(newIndex)`
                // will return our dropped element. We need to add +1 because
                // `nth-child` starts counting at one, not zero. Even then
                // still picks up the dropped element.
                // We thus use the data itself.
                var attachPath = $(ui.item).parents("table").data("prefix");
                if( newIndex > 0 ) {
                    var entries = scope.getEntries(attachPath);
                    var attachNode = entries[newIndex - ((newIndex < startIndex) ? 1 : 0)];
                    attachPath = attachNode[0].path;
                    if( movedNode[0].consumption ) {
                        if( attachNode[0].consumption ) {
                            // Case 1
                            // move best-practice A below best-practice B
                            // => A and B share same heading. A.rank > B.rank
                            var posPath = attachPath;
                            var rank = -1;
                            var parts = attachPath.split('/');
                            parts.pop();
                            attachPath = parts.join('/');
                            var headingNode = scope.getEntriesRecursive(
                                scope.entries, attachPath);
                            for( var idx = 0;
                                 idx < headingNode[1].length; ++idx ) {
                                if( headingNode[1][idx][0].path === posPath ) {
                                    if( movedPath.lastIndexOf(attachPath, 0) === 0 && startIndex < newIndex ) {
                                        // Moving under the same root.
                                        // Furthermore we are going down.
                                        rank = idx;
                                    } else {
                                        rank = idx + 1;
                                    }
                                    break;
                                }
                            }
                            if( rank < 0 ) {
                                showErrorMessages("Cannot find '"
                                    + posPath + "'  under '"
                                    + attachPath + "' in the table.");
                            }
                        } else {
                            // Case 2
                            // move best-practice A below heading H
                            // => A shows under heading H. A.rank == 0
                            rank = 0;
                        }
                    } else {
                        // Case 3 and 4 have only slight differences
                        // Case 3
                        //   move heading H below best-practice A
                        // Case 4
                        //   move heading H below heading K
                        // => H and K share same heading. H.rank > K.rank
                        var movedParts = movedPath.split('/');
                        var attachParts = attachPath.split('/');
                        var posPath = attachPath;
                        if( attachNode[0].consumption ) {
                            posPath = attachParts.join('/');
                            attachParts.pop(); // specific to case 3
                        }
                        while( attachParts.length > movedParts.length ) {
                            posPath = attachParts.join('/');
                            attachParts.pop();
                        }
                        if( attachParts.length === movedParts.length ) {
                            posPath = attachParts.join('/');
                            attachParts.pop();
                        }
                        attachPath = attachParts.join('/');
                        var rank = -1;
                        var headingNode = scope.getEntriesRecursive(
                            scope.entries, attachPath);
                        for( var idx = 0;
                             idx < headingNode[1].length; ++idx ) {
                            if( headingNode[1][idx][0].path === posPath ) {
                                if( movedPath.lastIndexOf(attachPath, 0) === 0 && startIndex < newIndex ) {
                                    // Moving under the same root.
                                    // Furthermore we are going down.
                                    rank = idx;
                                } else {
                                    rank = idx + 1;
                                }
                                break;
                            }
                        }
                        if( rank < 0 ) {
                            showErrorMessages("Cannot find '"
                                + posPath + "'  under '"
                                + attachPath + "' in the table.");
                        }
                    }
                }
                scope.moveBestPractice(movedPath, attachPath, rank, "drag-n-drop");
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

    $scope.BEST_PRACTICE_ELEMENT = 'best-practice';
    $scope.HEADING_ELEMENT = 'heading';

    $scope.TAG_SCORECARD = 'scorecard';
    $scope.TAG_SYSTEM = 'system';

    $scope.containsTag = function(bestpractise, tag) {
        return bestpractise.tag && bestpractise.tag.indexOf(tag) >= 0;
    }

    $scope.isImplemented = function (consumption) {
        return (consumption.implemented === 'Yes' || consumption.implemented === 'Work in progress');
    }

    $scope.implementationRateWidth = function(practice) {
        return {width: "" + practice[0].rate  + "%"};
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
                    "=>", capital_cost, root[0].path);
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
            for( var key in root[1] ) {
                if( root[1].hasOwnProperty(key) ) {
                    var node = root[1][key];
                    $scope.calcSavingsAndCost(node);
                    // available for capture
                    capturable.avg_energy_saving
                        *= (1.0 - node[0].capturable.avg_energy_saving);
                    capturable.capital_cost
                        *= (1.0 - node[0].capturable.capital_cost);
                    // captured
                    captured.avg_energy_saving
                        *= (1.0 - node[0].captured.avg_energy_saving);
                    captured.capital_cost
                        *= (1.0 - node[0].captured.capital_cost);
                }
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
        if( root[0].path === prefix ) {
            return root;
        }
        if( prefix.lastIndexOf(root[0].path, 0) === 0 ) {
            // startsWith - the prefix is deeper into the tree.
            for( var key in root[1] ) {
                if( root[1].hasOwnProperty(key) ) {
                    var node = root[1][key];
                    var found = $scope.getEntriesRecursive(node, prefix);
                    if( found ) { return found; }
                }
            }
        }
        return null;
    };


    /** Linearize the tree into a list of rows.
     */
    $scope.getEntriesAsRows = function(root, results) {
        var header_num = results.length;
        root[0].header_num = header_num;
        for( var key in root[1] ) {
            if( root[1].hasOwnProperty(key) ) {
                var node = root[1][key];
                if( node[0].consumption ) {
                    node[0].header_num = header_num;
                    results.push(node);
                } else {
                    results.push(node);
                    $scope.getEntriesAsRows(node, results);
                }
            }
        }
    };


    /** Extract a subtree rooted at *prefix* and linearize it
        into a list of rows.
     */
    $scope.getEntries = function(prefix) {
        var results = [];
        var node = $scope.getEntriesRecursive($scope.entries, prefix);
        if( node ) {
            $scope.getEntriesAsRows(node, results);
        }
        return results;
    };

    $scope.getEntriesByTag = function(prefix, tag) {
        var root = $scope.getEntriesRecursive($scope.entries, prefix);
        if( root ) {
            var results = [];
            for( var key in root[1] ) {
                if( root[1].hasOwnProperty(key) ) {
                    var node = root[1][key];
                    if( node[1].length > 0 ) { // XXX will work?
                        if( $scope.containsTag(node[0], tag) ) {
                            results.push(node);
                        }
                        for( var key2 in node[1] ) {
                            if( node[1].hasOwnProperty(key2) ) {
                                var node2 = node[1][key2];
                                if( $scope.containsTag(node2[0], tag) ) {
                                    results.push(node2);
                                }
                            }
                        }
                    } else {
                        if( $scope.containsTag(node[0], tag) ) {
                            results.push(node);
                        }
                    }
                }
            }
            return results;
        }
        return [];
    };

    $scope.getPath = function(element) {
        return element.path;
    };

    $scope.getHeadingPath = function(element) {
        if( element.consumption ) {
            var parts = element.path.split('/');
            parts.pop();
            return parts.join('/');
        }
        return element.path;
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
        $http.put(settings.urls.api_columns + prefix, {'slug': fieldName,
            'hidden': $scope.hidden[prefix][fieldName]}).then(
            function(resp) { // success
                // The columns API returns the updated portion of the content
                // tree used on the page.
                var node = $scope.getEntriesRecursive($scope.entries, prefix);
                node[0] = resp.data[0];
                node[1] = resp.data[1];
                // XXX unsure we can use `node`. Do we need to update
                // from the root?
                $scope.calcSavingsAndCost($scope.entries);
            },
            function(resp) {   // error
                showErrorMessages(resp);
            }
        );
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
        if( $scope.reverse ) {
            key = "" + (999 - obj[0].header_num);
        }
        if( typeof obj[0].consumption !== 'undefined'
            && obj[0].consumption !== null ) {
            for( var fieldName in $scope.dir ) {
                if ($scope.dir.hasOwnProperty(fieldName)) {
                    // XXX This only works if the consumption we sort by
                    //     is an integer less than 100.
                    key = key + "-" + ('000000000' +  obj[0].consumption[fieldName]).substr(-3);
                }
            }
            // We always tail the `rank` such that we get a consistent ordering
            // We also "reverse" (in a way) the rank such that descending order
            // looks good.
            key = key + "-" + (1000000 - obj[0].rank - 1);
        } else {
            if( $scope.reverse ) {
                key = key + "-" + 999;
            }
        }
        return key;
    };

    $scope.allAnswered = function(prefix) {
        var entries = $scope.getEntries(prefix);
        var allChecked = true;
        for( var idx = 0; idx < entries.length; ++idx ) {
            if( entries[idx][0].consumption ) {
                allChecked &= (entries[idx][0].consumption.implemented
                               && entries[idx][0].consumption.implemented.length > 0);
            }
        }
        return allChecked;
    };

    // editor functionality

    $scope.newElement = {
        reload: false,
        prefix: null,
        elementType: $scope.HEADING_ELEMENT,
        elementTypeModal: $scope.HEADING_ELEMENT,
        tag: "",
        value: {title: "", tag: ""}
    };

    // Prepares to add a specific type of element
    $scope.setNewElement = function(prefix, elementType, tag, reload) {
        $scope.newElement.prefix = prefix;
        if( typeof elementType === 'undefined' ) {
            $scope.newElement.elementTypeModal = $scope.HEADING_ELEMENT;
        } else {
            $scope.newElement.elementTypeModal = elementType;
        }
        if ( typeof tag !== "undefined" ) {
            $scope.newElement.tag = tag;
        } else {
            $scope.newElement.tag = null;
        }
        if ( typeof reload !== "undefined" ) {
            $scope.newElement.reload = reload;
        } else {
            $scope.newElement.reload = false;
        }
    };

    $scope.addElement = function(event, prefix) {
        if( typeof $scope.newElement.value === "string" ) {
             $scope.newElement.value = {
                 title: $scope.newElement.value, tag: null};
        }
        var elementType = $scope.newElement.elementType;
        if( typeof prefix === "undefined" ) {
            // Only the table inline form calls addElement($event, prefix).
            // The popup dialog calls addElement($event) and relies on
            // the *prefix* to be previously set.
            prefix = $scope.newElement.prefix;
            // XXX We use elementTypeModal in order to avoid unnatural
            //     UI updates when clicking on "+ Add..."
            elementType = $scope.newElement.elementTypeModal;
        } else {
            $scope.newElement.tag = null;
        }
        var form = angular.element(event.target);
        var modalDialog = form.parents('.modal');
        var title = $scope.newElement.value.title;
        var tag = $scope.newElement.value.tag || $scope.newElement.tag;
        var parent = prefix.substring(prefix.lastIndexOf('/') + 1);
        var data = {title: title, orig_elements: [parent]};
        if( tag ) {
            data.tag = {"tags": [tag]};
        }
        $http.post(settings.urls.api_page_elements, data).then(
            function success(resp) {
                var path = prefix + '/' + resp.data.slug;
                if( elementType === $scope.BEST_PRACTICE_ELEMENT ) {
                    $http.post(settings.urls.api_consumptions,
                               {path: path, text: title}).then(
                        function success(resp_consumption) {
                            var node = $scope.getEntriesRecursive(
                                $scope.entries, prefix);
                            resp.data.path = path;
                            resp.data.consumption = resp_consumption.data;
                            node[1].push([resp.data, []]);
                            $scope.newElement.value = "";
                            modalDialog.modal('hide');
                        },
                        function error() {
                            $scope.newElement.value = "";
                            modalDialog.modal('hide');
                            showErrorMessages(resp);
                        });
                } else {
                    var node = $scope.getEntriesRecursive(
                        $scope.entries, prefix);
                    resp.data.path = path;
                    resp.data.consumption = null;
                    node[1].push([resp.data, []]);
                    $scope.newElement.value = "";
                    modalDialog.modal('hide');
                    if( $scope.newElement.reload ) {
                        // icon-level are rendered by the template engine
                        // server-side.
                        window.location = window.location;
                    }
                }
            },
            function error(resp) {
                $scope.newElement.value = "";
                modalDialog.modal('hide');
                showErrorMessages(resp);
            });
        return false;
    };

    $scope.mirrorElement = function(event, prefix) {
        if( typeof prefix === "undefined" ) {
            // Only the table inline form calls mirrorElement($event, prefix).
            // The popup dialog calls mirrorElement($event) and relies on
            // the *prefix* to be previously set.
            prefix = $scope.newElement.prefix;
        }
        var form = angular.element(event.target);
        var modalDialog = form.parents('.modal');
        var data = {source: $scope.newElement.value.path};
        var postUrl = settings.urls.api_mirror_node.replace(/\/+$/, "")
            + prefix + '/';
        $http.post(postUrl, data).then(
        function success(resp) {
            var node = $scope.getEntriesRecursive($scope.entries, prefix);
            node[1].push(resp.data);
            // XXX unsure we can use `node`. Do we need to update
            // from the root?
            $scope.calcSavingsAndCost($scope.entries);
            $scope.newElement.value = "";
            modalDialog.modal('hide');

        }, function(resp) { // error
            $scope.newElement.value = "";
            modalDialog.modal('hide');
            showErrorMessages(resp);
        });
    };

    $scope.activeElement = {
        reload: false,
        value: {title: "", tag: ""}
    };

    // Prepares to edit or delete an element.
    $scope.setActiveElement = function(element, reload) {
        $scope.activeElement.value = element;
        if ( typeof reload !== "undefined" ) {
            $scope.activeElement.reload = reload;
        } else {
            $scope.activeElement.reload = false;
        }
    };

    $scope.editElement = function(event) {
        var form = angular.element(event.target);
        var data = {title: $scope.activeElement.value.title};
        $http.put(settings.urls.api_page_elements
                   + $scope.activeElement.value.slug + '/', data).then(
            function success(resp) {
                form.parents('.modal').modal('hide');
                if( $scope.activeElement.reload ) {
                    var captionElement = angular.element(
                        '[href="#tab-' + $scope.activeElement.value.slug + '"]').find(
                        '.icon-caption');
                    captionElement.text($scope.activeElement.value.title);
                }
            }, function error(resp) {
                form.parents('.modal').modal('hide');
                showErrorMessages(resp);
            });
    };

    $scope.toggleScorecard = function(path, reload, element) {
        event.preventDefault();
        if( $scope.containsTag(element, $scope.TAG_SCORECARD) ) {
            $http.put(
                settings.urls.api_scorecard_disable + element.slug).then(
                function success(resp) {
                    element.tag = resp.data;
                    if( reload ) { window.location = ""; }
                }, function error(resp) {
                    showErrorMessage(resp);
                });
        } else {
            $http.put(
                settings.urls.api_scorecard_enable + element.slug).then(
                function success(resp) {
                    element.tag = resp.data;
                    if( reload ) { window.location = ""; }
                }, function error(resp) {
                    showErrorMessage(resp);
                });
        }
    };

    $scope.editConsumption = function(event, practice) {
        angular.element(event.target).editor({
            uniqueIdentifier: "data-id",
            baseUrl : settings.urls.api_consumptions,
            onSuccess: function(element, data) {
                $scope.$apply(function() {
                    practice.consumption = data;
                });
            },
            rangeUpdate: function(editable, newVal) {
                editable.removeClass(function (index, className) {
                    var removedClasses = (className.match(/(^|\s)green-level-\S+/g) || []).join(' ');
                    return removedClasses
                });
                editable.addClass("green-level-" + newVal);
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

    $scope.deleteBestPractice = function() {
        var path = $scope.getPath($scope.activeElement.value);
        var splitIndex = path.lastIndexOf('/');
        var prefix = path.substring(0, splitIndex);
        $http.delete(settings.urls.api_best_practices
                + $scope.getPath($scope.activeElement.value) + '/').then(
            function success(resp) {
                var root = $scope.getEntriesRecursive($scope.entries, prefix);
                delete root[1][path];
                if( $scope.activeElement.reload ) {
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

    $scope.moveBestPractice = function(movedPath, attachPath, rank, externalKey) {
        var postUrl = settings.urls.api_move_node;
        var data = {source: movedPath};
        if( typeof rank !== 'undefined' && rank !== null ) {
            data['rank'] = rank;
        }
        if( typeof externalKey !== 'undefined' && externalKey !== null ) {
            data['external_key'] = externalKey;
        }
        $http.post(postUrl + attachPath + '/', data).then(
            function success(resp) {
                $http.get(settings.urls.api_best_practices
                    + $scope.entries[0].path + '/').then(
                        function success(resp) {
                            $scope.calcSavingsAndCost(resp.data);
                            $scope.entries = resp.data;

                        }, function(resp) { // error
                            showErrorMessages(resp);
                        });
            }, function(resp) { // error
                showErrorMessages(resp);
            });
    };

    $scope.indentHeader = function(practice, prefix) {
        var parts = practice[0].path.replace(prefix, '').split("/");
        var indentSpace = 0
        if( parts.length > 2 ) {
            indentSpace = parts.length - 2;
        }
        if( practice[0].consumption ) {
            return "bestpractice indent-header-" + indentSpace;
        }
        return "heading-" + indentSpace + " indent-header-" + indentSpace;
    }

    $scope.toLowerLevel = function($event, prefix) {
        $event.preventDefault();
        var row = angular.element($event.target).parents("tr");
        var startPath = row.data('id');
        var movedDepth = startPath.split("/").length;
        var entries = $scope.getEntries(prefix);
        var attachPath = null;
        for( var idx = 0; idx < entries.length; ++idx ) {
            var candidatePath = entries[idx][0].path;
            var candidateDepth = candidatePath.split("/").length;
            if( startPath === candidatePath ) {
                break;
            }
            if( candidateDepth == movedDepth ) {
                attachPath = candidatePath;
            }
        }
        if( attachPath ) {
            $scope.moveBestPractice(startPath, attachPath, null, "toLowerLevel");
        } else {
            showErrorMessages("Cannot find a heading above " + startPath);
        }
    };

    $scope.toUpperLevel = function($event, prefix) {
        $event.preventDefault();
        var row = angular.element($event.target).parents("tr");
        var startPath = row.data('id');
        var movedDepth = startPath.split("/").length - 2; // -1 is same anchor
        var entries = $scope.getEntries(prefix);
        var attachPath = null;
        for( var idx = 0; idx < entries.length; ++idx ) {
            var candidatePath = entries[idx][0].path;
            var candidateDepth = candidatePath.split("/").length;
            if( startPath === candidatePath ) {
                break;
            }
            if( candidateDepth == movedDepth ) {
                attachPath = candidatePath;
            }
        }
        if( !attachPath ) {
            attachPath = prefix;
        }
        $scope.moveBestPractice(startPath, attachPath, null, "toUpperLevel");
    };


    // Select all answers
    $scope.selectAll = function ($event, answer) {
        $event.preventDefault();
        var element = angular.element($event.target);
        var prefix = element.parents('table').find('tbody').data('prefix');
        var prefixElements = element.parents("tr[data-id]");
        if( prefixElements ) {
            prefix = prefixElements.data('id');
        }
        var practices = $scope.getEntries(prefix);
        for( var idx = 0; idx < practices.length; ++idx ) {
            if( practices[idx][0].consumption ) {
                practices[idx][0].consumption.implemented = answer;
                $http.put(settings.urls.api_self_assessment_response + "/" + practices[idx][0].consumption.rank + "/",
                    {text: answer}).then(
                    function success() {
                    },
                    function error(resp) {
                        showErrorMessages(resp);
                    });
            }
        }
    }

    $scope.score = function(node) {
        if( node.nb_answers == node.nb_questions ) {
            return node.normalized_score;
        }
        return "N/A";
    };

    $scope.toggleMyTSP = function(event, defaultUrl) {
        var urlParts = window.location.href.split('/');
        urlParts.pop();
        if( window.location.href[window.location.href.length - 1] === '/' ) {
            urlParts.pop();
        }
        if( !$scope.scoreToggle ) {
            urlParts.push('portfolios', 'totals');
            window.location = urlParts.join('/') + '/';
        } else {
            window.location = defaultUrl;
        }
    };

    /** Called when a user clicks on the "Improvement Planning" checkbox.
     */
    $scope.updateImprovement = function(practice) {
        if( practice && practice[0].consumption ) {
            if( practice[0].consumption.planned ) {
                $http.post(settings.urls.api_improvements + practice[0].path
                ).then(function success(resp) {
                    $("#improvement-dashboard").data('improvementDashboard').load();
                }, function(resp) { // error
                    showErrorMessages(resp);
                });
            } else {
                $http.delete(settings.urls.api_improvements + practice[0].path).then(function success(resp) {
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

    $scope.activeIcon = null;
    $scope.toggleIcons = function(event, iconSlug) {
        if( $scope.activeIcon === iconSlug ) {
            $scope.activeIcon = null;
        } else {
            $scope.activeIcon = iconSlug;
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
                                $scope.items.results[idx].last_activity_at
                                    = found.last_activity_at;
                                $scope.items.results[idx].normalized_score
                                    = found.normalized_score;
                                $scope.items.results[idx].nb_answers
                                    = found.nb_answers;
                                $scope.items.results[idx].nb_questions
                                    = found.nb_questions;
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
        if( typeof $scope.item.email === "undefined" ) {
            // If we don't select from the drop-down list of candidates
            // we only get an e-mail string.
            $scope.item = {email: $scope.item, printable_name: $scope.item};
        }
        $http.post(settings.urls.api_items, $scope.item).then(
            function(success) {
                // XXX Couldn't figure out how to get the status code
                // here so we just reload the list.
                $scope.refresh();
                $scope.item = null;
            },
            function(resp) {
                if( resp.status === 404 ) {
                    angular.element(settings.modalId).modal("show");
                } else {
                    showErrorMessages(resp);
                }
            });
    };

    $scope.remove = function ($event, idx) {
        $event.preventDefault();
        var removeUrl = settings.urls.api_items
            + $scope.items.results[idx].organization.slug;
        if( $scope.items.results[idx].role_description ) {
            removeUrl += '/' + $scope.items.results[idx].role_description
        }
        $http.delete(removeUrl).then(
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
                    type: elem.is(":checked") ? "POST" : "DELETE",
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
            // Distribution charts
            var elems = self.element.find(".chart-container");
            var defaultElem = self.element.find(
                ".chart-container.chart-container-default");
            var defaultChartId = defaultElem.attr("id");
            var defaultChart = null;
            for( var chartIdx = 0; chartIdx < data.length; ++chartIdx ) {
                if( (data[chartIdx].slug + '-chart') === defaultChartId ) {
                    defaultChart = data[chartIdx];
                    break;
                }
            }
            for( var idx = 0; idx < elems.length; ++idx ) {
                var chartId = $(elems[idx]).attr('id');
                var found = defaultChart;
                for( var chartIdx = 0; chartIdx < data.length; ++chartIdx ) {
                    if( (data[chartIdx].slug + '-chart') === chartId ) {
                        found = data[chartIdx];
                        break;
                    }
                }
                if( found ) {
                    var title0 = "";
                    var title1 = "";
                    var title2 = "";
                    if( found.breadcrumbs && found.breadcrumbs.length > 0 ) {
                        title0 = found.breadcrumbs[0];
                    }
                    if( found.breadcrumbs && found.breadcrumbs.length > 1 ) {
                        title1 = found.breadcrumbs[1];
                    }
                    if( found.breadcrumbs && found.breadcrumbs.length > 2 ) {
                        title2 = found.breadcrumbs[found.breadcrumbs.length - 1];
                    }
                    $(elems[idx]).find(".title h3").text(title0);
                    $(elems[idx]).find(".title h4").text(title1);
                    $(elems[idx]).find(".title h5").text(title2);
                    $(elems[idx]).find(".chart-content").benchmarkChart({
                        title: found.title,
                        scores: found.distribution,
                        nb_answers: found.nb_answers,
                        nb_questions: found.nb_questions});
                }
            }
            // Scores
            for( var idx = 0; idx < data.length; ++idx ) {
                if( data[idx].slug === "total-score" ) {
                    var totalScoreElement = self.element.find(
                        "#" + data[idx].slug);
                    if( typeof data[idx].normalized_score !== 'undefined'
                        && typeof data[idx].avg_normalized_score !== 'undefined'
                        && typeof data[idx].highest_normalized_score !== 'undefined') {
                        radialProgress(totalScoreElement[0])
                            .value1(data[idx].highest_normalized_score)
                            .value2(data[idx].avg_normalized_score)
                            .value3(data[idx].normalized_score)
                            .render();
                    } else {
                        if( totalScoreElement.find(".total-score-chart").length === 0 ) {
                            // N/A Could already been added. We will call
                            // the benchmark API multiple times
                            // on the improvement dashboard.
                            totalScoreElement.append(
                    "<div class=\"total-score-chart\">" +
                      "<div>N/A - Self assessment questions incomplete</div>" +
                    "</div>");
                        }
                    }
                    var nbRespondentsElem = self.element.find(
                        "#nb-respondents");
                    if( nbRespondentsElem ) {
                        nbRespondentsElem.text(data[idx].nb_respondents);
                    }
                    var improvementScore = self.element.find(
                        "#improvement-score");
                    if( improvementScore && data[idx].improvement_score ) {
                        improvementScore.text(
                         "(+" + data[idx].improvement_score.toFixed(0) + "%)");
                    }
                } else {
                    // score
                    var elemPath = "#" + data[idx].slug + "-score .rollup-score";
                    var benchmarkElement = self.element.find(elemPath);
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
