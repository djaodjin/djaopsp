Vue.component('editable-practices-list', {
    mixins: [
        itemListMixin
    ],
    data: function() {
        return {
            url: this.$urls.api_content,
            segmentsUrl: this.$urls.api_editable_segments,
            segments: [],
            addBelowIndex: -1,
            activeIndex: -1,
            activeEntry: {title: "", title: "", segment: ""},
            activeSegment: null,
            activeSibblings: [],
            params: {
                o: '-created_at'
            }
        }
    },
    methods: {
        addElementBelow: function(entry, index) {
            var vm = this;
            var parent = '';
            if( typeof entry !== 'undefined' ) {
                parent = entry.slug;
                // We differentiate practices from headings by the presence and
                // abscence, respectively, of a `url` field.
                // When adding an element below an existing practice, we attach
                // it to the preceding heading.
                if( entry.url ) {
                    var parentIndex = vm._findParentHeadingIndex(entry, index);
                    if( parentIndex > 0 ) {
                        parent = vm.items.results[parentIndex].slug;
                    }
                }
            }
            var data = {
                title: vm.activeEntry.title,
                parents: []
            };
            if( vm.activeEntry.segment ) {
                data.parents.push({title: vm.activeEntry.segment});
            }
            if( vm.activeEntry.tile ) {
                data.parents.push({title: vm.activeEntry.tile});
            }
            vm.reqPost(vm._safeUrl(vm.url, parent), data,
            function(resp) {
                vm._clearInput();
                vm._loadData();
            });
        },
        addPractice: function(practices, newPractice) {
            var vm = this;
            vm.activeEntry.title = newPractice.title;
            return false;
        },
        aliasTree: function(entry, index, segment) {
            var vm = this;
            var attachPath = segment.path;
            var mirrorPath = vm._getPath(entry, index);
            var data = {source: mirrorPath};
            vm.reqPost(vm._safeUrl(vm.$urls.api_alias_node, attachPath), data,
            function(resp) {
                vm._clearInput();
                vm._loadData();
            });
        },
        deleteTree: function(entry, index) {
            var vm = this;
            var urlBase = vm.$urls.edit.api_content;
            if( vm.activeSegment ) {
                urlBase = vm._safeUrl(urlBase, vm.activeSegment.path);
            }
            vm.reqDelete(vm._safeUrl(urlBase, vm._getPath(entry, index)));
        },
        includes: function(entry, segment) {
            if( entry.extra && entry.extra.segments ) {
                return entry.extra.segments.includes(segment.path);
            }
            if( entry.segments ) {
                return entry.segments.includes(segment.path);
            }
            return false;
        },
        indentHeader: function(row) {
            var vm = this;
            if( vm.isPractice(row) ) {
                return "bestpractice";
            }
            if( row.indent <= 0 ) {
                return "heading-tile";
            }
            var indentSpace = row.indent - 1;
            return "heading-" + indentSpace;
        },
        isPractice: function(row) {
            var vm = this;
            if( typeof row.default_unit !== "undefined" ) {
                return row.default_unit !== null;
            }
            return false;
        },
        moveTreeDown: function(entry, index) {
            var vm = this;
            var rank = 0;
            var attachPath = 1;
            var movedPath = vm._getPath(entry, index);
            // The attach point is the node one up the tree, rank is the order
            // amongst children of the attach point.
            for( var idx = index - 1; idx >= 0; --idx ) {
                if( vm.items.results[idx].indent == (entry.indent - 1) ) {
                    attachPath = vm.items.results[idx].slug;
                    break;
                }
                if( vm.items.results[idx].indent == entry.indent ) {
                    rank = rank + 1;
                }
            }
            var last = rank;
            for( var idx = index + 1; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].indent < entry.indent ) {
                    // last index with the same indent level.
                    break;
                }
                if( vm.items.results[idx].indent == entry.indent ) {
                    // Found a sibbling
                    last = last + 1;
                }
            }
            rank = rank + 1;  // move down one
            if( attachPath && rank <= last ) {
                // Couln't find a node up the tree or we are at the end of
                // the list of children for a node.
                vm._moveTree(movedPath, attachPath, rank);
            }
        },
        moveTreeRightCandidates: function(entry, index) {
            var vm = this;
            // Find all sibblings
            var rank = 0;
            var attachPath = 1;
            var movedPath = vm._getPath(entry, index);
            var sibblings = [];
            // Gather all the sibblings of the `entry` node.
            for( var idx = index - 1; idx >= 0; --idx ) {
                if( vm.items.results[idx].indent == (entry.indent - 1) ) {
                    break;
                } else if( vm.items.results[idx].indent == entry.indent ) {
                    sibblings.push({entry: vm.items.results[idx], index: idx});
                }
            }
            for( var idx = index + 1; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].indent == (entry.indent - 1) ) {
                    break;
                } else if( vm.items.results[idx].indent == entry.indent ) {
                    sibblings.push({entry: vm.items.results[idx], index: idx});
                }
            }
            // Show dialog box
            vm.activeEntry = entry;
            vm.activeIndex = index;
            vm.activeSibblings = sibblings;
            $("#move-right-dialog").modal('show');
        },
        moveTreeRight: function(candidate, index, title) {
            var vm = this;
            var rank = 0;
            var movedPath = vm._getPath(vm.activeEntry, vm.activeIndex);
            if( candidate ) {
                var attachPath = vm._getPath(candidate, index);
                // The attach point is the grandparent.
                // The rank is below the parent.
                for( var idx = index + 1; idx < vm.items.results.length; ++idx ) {
                    if( vm.items.results[idx].indent == candidate.indent ) {
                        rank = idx - index;
                        break;
                    }
                }
                if( attachPath ) {
                    // Couln't find a node up the tree or we are at the end of
                    // the list of children for a node.
                    vm._moveTree(movedPath, attachPath, rank);
                    $("#move-right-dialog").modal('hide');
                }
            } else {
                // We need to create a new element before moving the active
                // one under it.
                var parentIndex = vm._findParentHeadingIndex(
                    vm.activeEntry, vm.activeIndex);
                var parentPath = vm._getPath(
                    vm.items.results[parentIndex], parentIndex);
                vm.reqPost(vm._safeUrl(
                    vm.$urls.edit.api_content, parentPath), {
                        title: vm.activeEntry.title
                }, function(resp) {
                    var attachPath = resp.path;
                    vm._moveTree(movedPath, attachPath, rank);
                    $("#move-right-dialog").modal('hide');
                });
            }
         },
        moveTreeLeft: function(entry, index) {
            var vm = this;
            var rank = 0;
            var attachPath = 1;
            var movedPath = vm._getPath(entry, index);
            // The attach point is the grandparent.
            // The rank is below the parent.
            for( var idx = index - 1; idx >= 0; --idx ) {
                if( vm.items.results[idx].indent == (entry.indent - 2) ) {
                    attachPath = vm.items.results[idx].slug;
                    break;
                }
                if( vm.items.results[idx].indent == (entry.indent - 1) ) {
                    rank = rank + 1;
                }
            }
            if( attachPath ) {
                // Couln't find a node up the tree or we are at the end of
                // the list of children for a node.
                vm._moveTree(movedPath, attachPath, rank);
            }
        },
        moveTreeUp: function(entry, index) {
            var vm = this;
            var rank = 0;
            var attachPath = null;
            var movedPath = vm._getPath(entry, index);
            for( var idx = index - 1; idx >= 0; --idx ) {
                if( vm.items.results[idx].indent == (entry.indent - 1) ) {
                    attachPath = vm.items.results[idx].slug;
                    break;
                }
                if( vm.items.results[idx].indent == entry.indent ) {
                    rank = rank + 1;
                }
            }
            rank = rank - 1; // move up one
            if( attachPath && rank >= 0 ) {
                vm._moveTree(movedPath, attachPath, rank);
            }
        },
        setActive: function(entry, index, segment) {
            var vm = this;
            if( vm.activeIndex === index ) {
                vm._clearInput();
            } else {
                vm.activeEntry = entry;
                vm.activeIndex = index;
                vm.activeSegment = segment;
            }
        },
        toggleAddBelow: function(entry, index) {
            var vm = this;
            vm.activeIndex = -1; // edit loses input focus.
            if( typeof index == 'undefined' ) {
                vm.addBelowIndex = vm._findIndex(entry);
            } else {
                vm.addBelowIndex = index;
            }
            vm.activeEntry = {title: "", title: "", segment: ""};
        },
        toggleShowHide: function(entry, index) {
            var vm = this;
            for( var idx = index + 1; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].indent <= entry.indent ) {
                    // last index with the same indent level.
                    break;
                }
                vm.items.results[idx]['hide'] = !vm.items.results[idx]['hide'];
            }
            vm.$forceUpdate();
        },
        updateElement: function(entry, index) {
            var vm = this;
            vm.reqPut(vm._safeUrl(vm.$urls.edit.api_content,
                    vm._getPath(entry, index)), {
                title: entry.title
            }, function(resp) {
                vm._clearInput();
            });
        },
        updateItemSelected: function(item, question) {
            var vm = this;
            vm.reqPatch(vm._safeUrl(vm.url, question.path), {
                'default_unit': item.slug
            }, function() {
                question.default_unit = item.slug;
            });
        },
        _clearInput: function() {
            var vm = this;
            vm.addBelowIndex = -1;
            vm.activeIndex = -1;
            vm.activeEntry = {title: "", title: "", segment: ""};
            vm.activeSegment = null;
            vm.activeSibblings = [];
        },
        _findIndex: function(entry) {
            var vm = this;
            for( var idx = 0; idx < vm.items.results.length; ++idx ) {
                if( vm.items.results[idx].slug == entry.slug ) {
                    return idx;
                }
            }
            return -1;
        },
        _findParentHeadingIndex: function(entry, index) {
            var vm = this;
            var entryIndex = index;
            if( typeof entryIndex == 'undefined' ) {
                entryIndex = vm._findIndex(entry);
            }
            var entryIndent = entry.indent;
            for( var idx = entryIndex; idx >= 0; --idx ) {
                if( vm.items.results[idx].indent < entryIndent ) {
                    return idx;
                }
            }
            return -1;
        },
        _getPath: function(entry, index) {
            var vm = this;
            var path = '/' + entry.slug
            for( var idx = index - 1; idx >= 0; --idx ) {
                if( vm.items.results[idx].indent == (entry.indent - 1) ) {
                    path = vm._getPath(vm.items.results[idx], idx) + path
                    break;
                }
            }
            return path;
        },
        _loadData: function() {
            var vm = this;
            vm.reqGet(vm.segmentsUrl, function(resp) {
                vm.segments = resp.results;
            });
            vm.get();
        },
        _moveTree: function(movedPath, attachPath, rank, externalKey) {
            var vm = this;
            var postUrl = vm._safeUrl(vm.$urls.api_move_node, attachPath);
            var data = {source: movedPath};
            if( typeof rank !== 'undefined' && rank !== null ) {
                data['rank'] = rank;
            }
            if( typeof externalKey !== 'undefined' && externalKey !== null ) {
                data['external_key'] = externalKey;
            }
            vm.reqPost(vm._safeUrl(vm.$urls.api_move_node, attachPath), data,
            function(resp) {
                vm._clearInput();
            });
        }
    },
    mounted: function(){
        this._loadData();
    }
});
