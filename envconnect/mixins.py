# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from deployutils import mixins as deployutils_mixins
from answers.models import Question as AnswersQuestion
from pages.models import PageElement, RelationShip
from survey.models import SurveyModel, Question, Answer
from survey.utils import get_account_model

from .models import Consumption, Improvement
from .serializers import PageElementSerializer


class AccountMixin(deployutils_mixins.AccountMixin):

    account_queryset = get_account_model().objects.all()
    account_lookup_field = 'slug'
    account_url_kwarg = 'organization'


class PermissionMixin(deployutils_mixins.AccessiblesMixin):

    def get_context_data(self, *args, **kwargs):
        context = super(
            PermissionMixin, self).get_context_data(*args, **kwargs)
        context.update({
            'is_envconnect_manager': self.manages(settings.APP_NAME)})
        return context


class BreadcrumbMixin(PermissionMixin):

    breadcrumb_url = 'summary'

    @staticmethod
    def get_prefix():
        return None

    def get_breadcrumb_url(self):
        return self.breadcrumb_url

    def _build_tree(self, root, path=None, depth=1, nocuts=False):
        if path is None:
            path = '/' + root.slug
        results = []
        if nocuts or depth < 4:
            for edge in RelationShip.objects.filter(
                    orig_element=root).select_related('dest_element').order_by(
                    'rank', 'pk'):
                # XXX We use the fact that node ids are naturally in increasing
                # order. Without order postgres will not return the life-cycle
                # in a consistent order.
                node = edge.dest_element
                setattr(node, 'rank', edge.rank)
                results += [self._build_tree(
                    node, path='%s/%s' % (path, node.slug),
                    depth=depth, nocuts=nocuts)]
        consumption = Consumption.objects.filter(path=path).first()
        setattr(root, 'consumption', consumption)
        return (root, results)

    def _cut_tree(self, root, path='', depth=5):
        results = []
        if len(path.split('/')) < depth:
            for node in root[1]:
                results += [self._cut_tree(
                    node, path='%s/%s' % (path, node[0].slug))]
        return (root[0], results)

    def _scan_candidates(self, root, slug):
        # hardcoded icon tags
        candidates = root.relationships.all()
        try:
            candidate = candidates.get(slug=slug)
            return [candidate]
        except PageElement.DoesNotExist:
            pass
        for candidate in candidates:
            suffix = self._scan_candidates(candidate, slug)
            if len(suffix) > 0:
                return [candidate] + suffix
        return []

    @property
    def breadcrumbs(self):
        if not hasattr(self, '_breadcrumbs'):
            self._breadcrumbs = self.get_breadcrumbs(self.kwargs.get('path'))
        return self._breadcrumbs

    def get_breadcrumbs(self, path):
        #pylint:disable=too-many-locals
        results = []
        parts = path.split('/')[1:]
        if len(parts) < 1:
            return path, results
        lookup = parts[0]
        lookup_prefix = self.get_prefix() #pylint:disable=assignment-from-none
        if lookup_prefix:
            # Adds an optional lookup prefix to find the root ``PageElement``
            # used to generate the HTML page.
            if not parts[0].startswith(lookup_prefix):
                lookup = lookup_prefix + parts[0]
        root = get_object_or_404(PageElement, slug=lookup)
        from_root = None
        for root_node in PageElement.objects.get_roots():
            if root_node.slug == root.slug:
                from_root = "/%s" % root.slug
                break
            candidates = self._scan_candidates(root_node, root.slug)
            if candidates:
                from_root = "/%s/%s" % (root_node.slug, '/'.join([
                    candidate.slug for candidate in candidates]))
                break
        results += [[root, '/' + parts[0]]]
        self.icon = None
        for idx, part in enumerate(parts[1:]):
            suffix = self._scan_candidates(root, part)
            root = suffix[-1]
            for sfx in reversed(suffix):
                if sfx.text.endswith('.png'):
                    self.icon = sfx
            suffix = '/'.join([sfx.slug for sfx in suffix])
            from_root = "%s/%s" % (from_root, suffix)
            prefix = []
            for full_part in suffix.split('/'):
                if full_part != part:
                    prefix += [full_part]
            if prefix:
                results[-1][1] += "#%s" % prefix[0]
            results += [[root, '/'.join([''] + parts[:idx + 2])]]
        for crumb in results:
            anchor_start = crumb[1].find('#')
            if anchor_start > 0:
                path = crumb[1][:anchor_start]
                anchor = crumb[1][anchor_start + 1:]
            else:
                path = crumb[1]
                anchor = ""
            base_url = reverse('summary', args=(path,))
            if anchor:
                base_url += ("?active=%s" % anchor)
            crumb.append(base_url)
                # XXX Do we add the Organization in the path
                # for self-assessment to summary and back?
        return from_root, results

    def get_context_data(self, *args, **kwargs):
        context = super(BreadcrumbMixin, self).get_context_data(*args, **kwargs)
        from_root, trail = self.breadcrumbs
        page_prefix = '/'.join(from_root.split('/')[:-1])
        context.update({
            'page_prefix': page_prefix,
            'from_root': from_root,
            'breadcrumbs': trail,
            'active': self.request.GET.get('active', "")})
        urls = {
            'api_best_practices': reverse('api_detail_base'),
            'api_columns': reverse('api_column_base'),
            'api_consumptions': reverse('api_consumption_base'),
            'api_weights': reverse('api_score_base'),
            'api_page_elements': reverse('page_elements')}
        if 'organization' in context:
            urls.update({'api_improvements': reverse(
                'api_improvement_base', args=(context['organization'],))})
        self.update_context_urls(context, urls)
        return context

    def to_representation(self, root):
        results = []
        root_repr = PageElementSerializer().to_representation(root[0])
        for node in root[1]:
            results += [self.to_representation(node)]
        return [root_repr, results]


class ReportMixin(BreadcrumbMixin, AccountMixin):

    report_title = 'Best Practices Report'

    def get_survey(self):
        return get_object_or_404(SurveyModel,
            account=self.account, title=self.report_title)

    def consumptions_to_answers(self, consumptions):
        answers = {}
        consumptions = [x.id for x in consumptions]
        questions = Question.objects.filter(
            survey=self.get_survey(),
            text__in=consumptions)
        if questions.count() > 0:
            for question in questions:
                try:
                    answer = Answer.objects.get(question_id=question.pk)
                    if int(question.text) not in answers:
                        answers[int(question.text)] = answer.text
                except Answer.DoesNotExist:
                    pass
        return answers

    def system_to_answers(self, system):
        answers = {}
        for equipment in system:
            answers.update(
                self.consumptions_to_answers(equipment['consumptions']))
        return answers


class ImprovementQuerySetMixin(ReportMixin):
    """
    best practices which are part of an improvement plan for an ``Account``.
    """
    model = Improvement

    def get_queryset(self):
        return self.model.objects.filter(account=self.account)

    def get_reverse_kwargs(self):
        """
        List of kwargs taken from the url that needs to be passed through
        to ``get_success_url``.
        """
        return ['path', self.interviewee_slug, 'survey']


class BestPracticeMixin(BreadcrumbMixin):

    def get_breadcrumbs(self, path):
        full, results = super(BestPracticeMixin, self).get_breadcrumbs(path)
        results[-1][2] = reverse(
            'best_practice_detail', kwargs={
                'path': results[-1][1]})
        return full, results

    def get_best_practice_url(self):
        return reverse('best_practice_detail', kwargs={
            'path': self.kwargs.get('path')})

    def get_context_data(self, *args, **kwargs):
        context = super(
            BestPracticeMixin, self).get_context_data(*args, **kwargs)
        context.update({'best_practice': self.best_practice})
        return context

    @property
    def best_practice(self):
        if not hasattr(self, '_best_practice'):
            _, trail = self.breadcrumbs
            self._best_practice = trail[-1][0]
        return self._best_practice

    @property
    def question(self):
        if not hasattr(self, '_question'):
            if not self.best_practice:
                raise Http404()
            self._question = get_object_or_404(AnswersQuestion,
                slug=self.best_practice.slug)
        return self._question
