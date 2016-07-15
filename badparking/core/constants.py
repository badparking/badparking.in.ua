CLAIM_STATUS_RECEIVED = 'received'  # Received by the system but not yet ready for collection, initial state
CLAIM_STATUS_COMPLETE = 'complete'  # Has all required parts set, ready for pre-moderation
CLAIM_STATUS_ENQUEUED = 'enqueued'  # Validated and ready for collection by the police
CLAIM_STATUS_ACCEPTED = 'accepted'  # Taken off by the police
CLAIM_STATUS_IN_PROGRESS = 'in_progress'  # Police started investigation
CLAIM_STATUS_RESOLVED = 'resolved'  # Complete with some resolution
CLAIM_STATUS_INVALID = 'invalid'  # Deemed invalid by the police (or our pre-moderation)
CLAIM_STATUS_CANCELED = 'canceled'  # Canceled by the reporter

CLAIM_STATUS_CHOICES = (
    (CLAIM_STATUS_RECEIVED, 'Received'),
    (CLAIM_STATUS_COMPLETE, 'Complete'),
    (CLAIM_STATUS_ENQUEUED, 'Enqueued'),
    (CLAIM_STATUS_ACCEPTED, 'Accepted by police'),
    (CLAIM_STATUS_IN_PROGRESS, 'In progress'),
    (CLAIM_STATUS_RESOLVED, 'Resolved'),
    (CLAIM_STATUS_INVALID, 'Invalid'),
    (CLAIM_STATUS_CANCELED, 'Canceled'),
)

CLAIM_ACTIVE_STATUSES = (CLAIM_STATUS_ENQUEUED, CLAIM_STATUS_ACCEPTED, CLAIM_STATUS_IN_PROGRESS)
