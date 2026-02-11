Data Entry
==========

GHG Emissions Calculator
------------------------

When visiting the page at URL "/app/{profile}/track/energy-ghg-emissions/"
(``djaopsp.views.assess.TrackMetricsView``),
the server will populate the template
"djaopsp/templates/app/track/energy-ghg-emissions.html" with
a ``context`` that includes API endpoints dynamically generated
by ``get_editable_filter_context(self, context, candidate_paths, title=None)``.

The first ``path`` in ``candidate_paths`` matching a ``Question``
and the slugified ``title`` are used to retrieve or create
an ``EditableFilter`` for the profile with
``extra ~= {"path": path, "tags": [slugify(title)]}``.

The name of the dynamic endpoint is created out of the `slugify(title)`
or the last part of the `path` such that it is associated properly in the
template. The value of the endpoint is ``reverse('survey_api_accounts_filter',
args=(self.account, editable_filter.slug,)``.


In the browser, the Vue components ``scope1-stationary-combustion``,
``scope1-mobile-combustion``, ``scope1-refrigerants``,
``scope2-purchased-electricity``, ``scope3-transportation`` (all defined
in "assess.js"; extending ``ghg-emissions-estimator``, itself extending
``data-metric-tracker``) will call their respective dynamic API endpoint
"/api/{profile}/filters/accounts/{editable_filter}" (
``survey.api.matrix.AccountsFilterDetailAPIView``) to load the list
of facilities/profiles in that category (``scope1-stationary-combustion``,
``scope1-mobile-combustion``, etc.) to enter data for.

CRUD on list in a category
~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding, updating and deleting a row is done through
the `Adds a profile to a group`_, `Updates a selector in a group`_,
and `Removes a selector from a group`_ respectively.

When creating a new row in the calculator, both the facility and fuel
type are required. The ``profile.full_name`` is set as the facility name,
and the fuel type is saved in the ``extra`` field
(ex: ``{"fuel_type":"natural-gas"}``).


Recording energy use and GHG Emissions calculated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a user clicks on the "Record" button, the Vue component will
use the parent 'ghg-emissions-estimator' `save` method to calculated
GHG Emissions and persist both the energy use and GHG Emissions calculated
through the `Records quantitative measurements API`_.

For example:

    .. code-block:: http

        POST /api/supplier-1/filters/accounts/scope1-stationary-combustion/values HTTP/1.1

    .. code-block:: json

        {
            "baseline_at":"2025-01-01",
            "created_at":"2025-12-31",
            "items":[{
                "slug": "office",
                "measured": 10,
                "unit": "btu"
            }, {
                "slug": "office",
                "measured": 0.0000010756,
                "unit": "t"
            }]
        }

`"Encoding answers in the database"`_ in the `djaodjin-survey`_ documentation
has details on how the quantitative values are stored in the database.


Using the calculator results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the GHG Emissions calculated have been recorded in the database, it is
possible to aggregate them to answer questions that require to a total
GHG Emissions. The "Use calculator result" button in a questionnaire
assess step does just that.

For example:

    .. code-block:: http

        GET /api/supplier-1/metrics/aggregate/sustainability/environmental-reporting/ghg-emissions-reporting/ghg-emissions-scope1-measured/ghg-emissions-scope1?start_at=2025-01-01&ends_at=2025-12-31&unit=t HTTP/1.1

    .. code-block:: json

        {
          "measured": 0.0000010756,
          "unit":"t"
        }

`"Aggregates"`_ in the `djaodjin-survey`_ documentation
has details on how aggregates of quantitative values are retrieved
from the database.


.. _Records quantitative measurements API: https://www.djaodjin.com/docs/reference/djaopsp/2022-09-14/api/#createAccountsFilterValues
.. _Adds a profile to a group: https://www.djaodjin.com/docs/reference/djaopsp/2022-09-14/api/#createAccountsFilterList
.. _Updates a selector in a group: https://www.djaodjin.com/docs/reference/djaopsp/2022-09-14/api/#createAccountsFilterList
.. _Removes a selector from a group: https://www.djaodjin.com/docs/reference/djaopsp/2022-09-14/api/#createAccountsFilterList
.. _"Encoding answers in the database": https://djaodjin-survey.readthedocs.io/en/latest/encoding.html
.. _"Aggregates": https://djaodjin-survey.readthedocs.io/en/latest/analytics.html
.. _djaodjin-survey: https://djaodjin-survey.readthedocs.io/en/latest/
