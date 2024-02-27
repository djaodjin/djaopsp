Accessing Portfolio/Shared Samples
==================================

A respondent profile (``account``) to a questionnaire will access its response
through the URL `/app/<slug:profile>/scorecard/<slug:sample>/` and the API
calls used to build the page (i.e. `/api/<slug:profile>/sample/<slug:sample>`
`/api/<slug:profile>/sample/<slug:sample>/content`,
`/api/<slug:profile>/sample/<slug:sample>/benchmarks`,
`/api/<slug:profile>/assets/<path:path>`) using ``account`` for profile slug.

When the respondent shares a completed questionnaire with a receiving profile
(``grantee``), the grantee will access the response through the same URL
and APIs but using ``grantee`` instead for profile slug.

Therefore permissions are checked in two steps:

1. The `Web/API Gateway <https://djaoapp.readthedocs.io/>`_ checks
   that the HTTP ``request.user`` has a direct role on `<slug:profile>`.
2. The Practices Survey Platform itself checks that the `<slug:sample>` belongs
   to `<slug:profile>` or that `<slug:profile>` has a `Portfolio` that extends
   past the date the sample was created
   (see `survey.mixins.SampleMixin.get_sample`).
