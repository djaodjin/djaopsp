# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE.

# Implementation Note: We use the following natural order of these
# reporting_status definition in `get_engagement_by_reporting_status`
# to collapse reporting_status to a single value when an account's response
# has been requested by multiple grantees.
REPORTING_NO_PROFILE = -3 # 'no-profile'
REPORTING_NO_DATA = -2 # 'no-data'
REPORTING_INVITED_DENIED = -1
REPORTING_INVITED = 0
REPORTING_ABANDONED = 1
REPORTING_EXPIRED = 2
REPORTING_UPDATED = 3
REPORTING_NO_RESPONSE = 4 # 'no-response'
REPORTING_ASSESSMENT_PHASE = 5
REPORTING_PLANNING_PHASE = 6
REPORTING_COMPLETED_DENIED = 7
REPORTING_COMPLETED_NOTSHARED = 8
REPORTING_VERIFIED_DENIED = 9
REPORTING_VERIFIED_NOTSHARED = 10
REPORTING_RESPONDED = 11 # 'responded'
REPORTING_COMPLETED = 12 # 'completed'
REPORTING_VERIFIED = 13 # 'verified'

REPORTING_STATUSES = (
    (REPORTING_NO_PROFILE, 'no-profile'),
    (REPORTING_NO_DATA, 'no-data'),
    (REPORTING_INVITED_DENIED, 'invited-denied'),
    (REPORTING_INVITED, 'invited'),
    (REPORTING_ABANDONED, 'abandoned'),
    (REPORTING_EXPIRED, 'expired'),
    (REPORTING_UPDATED, 'updated'),
    (REPORTING_NO_RESPONSE, 'no-response'),
    (REPORTING_ASSESSMENT_PHASE, 'completed-assess-only'),
    (REPORTING_PLANNING_PHASE, 'completed-assess-planning'),
    (REPORTING_COMPLETED_DENIED, 'completed-denied'),
    (REPORTING_COMPLETED_NOTSHARED, 'completed-notshared'),
    (REPORTING_VERIFIED_DENIED, 'verified-denied'),
    (REPORTING_VERIFIED_NOTSHARED, 'verified-notshared'),
    (REPORTING_RESPONDED, 'responded'),
    (REPORTING_COMPLETED, 'completed'),
    (REPORTING_VERIFIED, 'verified'),
)


COLLAPSED_REPORTING_ENGAGE_STATUSES = {
    REPORTING_NO_PROFILE: "Invited",
    REPORTING_NO_DATA: "Invited",
    REPORTING_INVITED_DENIED: "Invited",
    REPORTING_INVITED: "Invited",
    REPORTING_ABANDONED: "Work-in-progress",
    REPORTING_EXPIRED: "Work-in-progress",
    REPORTING_UPDATED: "Work-in-progress",
    REPORTING_NO_RESPONSE: "Work-in-progress",
    REPORTING_ASSESSMENT_PHASE: "Completed",
    REPORTING_PLANNING_PHASE: "Completed",
    REPORTING_COMPLETED_DENIED: "Completed",
    REPORTING_COMPLETED_NOTSHARED: "Completed",
    REPORTING_VERIFIED_DENIED: "Verified",
    REPORTING_VERIFIED_NOTSHARED: "Verified",
    REPORTING_RESPONDED: "Completed",
    REPORTING_COMPLETED: "Completed",
    REPORTING_VERIFIED: "Verified",
}


REPORTING_ACCESSIBLE_ANSWERS = (
    REPORTING_COMPLETED_DENIED,
    REPORTING_COMPLETED_NOTSHARED,
    REPORTING_VERIFIED_DENIED,
    REPORTING_VERIFIED_NOTSHARED,
    REPORTING_COMPLETED,
    REPORTING_VERIFIED
)
