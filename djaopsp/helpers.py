# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE.

from .compat import six


class ContentCut(object):
    """
    Visitor that cuts down a content tree whenever TAG_PAGEBREAK is encountered.
    """
    TAG_PAGEBREAK = 'pagebreak'

    def __init__(self, tag=TAG_PAGEBREAK):
        self.match = tag

    def enter(self, tag):
        if tag and self.match:
            if isinstance(tag, dict):
                return self.match not in tag.get('tags', [])
            return self.match not in tag
        return True

    @staticmethod
    def leave(attrs, subtrees):
        #pylint:disable=unused-argument
        return True


def as_valid_sheet_title(title):
    """
    Prevents 'Invalid character / found in sheet title' errors.
    """
    return title.replace('/', '-')


def flatten(rollup_trees, sort_by_key=True, depth=0):
    """
    Flatten a content tree represented as a dictionnary into a list.
    """
    result = []
    children = six.iteritems(rollup_trees)
    if sort_by_key:
        children = sorted(children,
            key=lambda node: (
                node[1][0].get('rank', 0)
                if node[1][0].get('rank') is not None else 0,
                node[1][0].get('title', "")))
    for key, values in children:
        elem, nodes = values
        extra = elem.get('extra', elem.get('tag', {}))
        try:
            tags = extra.get('tags', [])
        except AttributeError:
            tags = extra
        pagebreak = ('pagebreak' in tags)
        if nodes:
            if not pagebreak:  # XXX create scorecardcache
                path = None
            else:
                path = elem.get('path', key)
        else:
            path = elem.get('path', key)
        #XXXitem = elem.copy()
        item = elem
        item.update({'path': path, 'indent': depth})
        result += [item]
        if not pagebreak:
            result += flatten(nodes, sort_by_key=sort_by_key, depth=depth + 1)
    return result
