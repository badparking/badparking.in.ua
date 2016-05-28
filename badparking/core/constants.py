CLAIM_STATUS_ENQUEUED = 'enqueued'  # Received and validated by the system, initial state
CLAIM_STATUS_ACCEPTED = 'accepted'  # Taken off by the police
CLAIM_STATUS_IN_PROGRESS = 'in_progress'  # Police started investigation
CLAIM_STATUS_COMPLETE = 'complete'  # Complete with some resolution
CLAIM_STATUS_INVALID = 'invalid'  # Deemed invalid by the police
CLAIM_STATUS_CANCELED = 'canceled'  # Canceled by the reporter

CLAIM_STATUS_CHOICES = (
    (CLAIM_STATUS_ENQUEUED, 'Enqueued'),
    (CLAIM_STATUS_ACCEPTED, 'Accepted by police'),
    (CLAIM_STATUS_IN_PROGRESS, 'In progress'),
    (CLAIM_STATUS_COMPLETE, 'Complete'),
    (CLAIM_STATUS_INVALID, 'Invalid'),
    (CLAIM_STATUS_CANCELED, 'Canceled'),
)
