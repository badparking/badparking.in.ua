class BankIdError(Exception):
    def __init__(self, code=None, description=None):
        self.code = code
        self.description = description
        super(BankIdError, self).__init__('Code: {}, Message: {}'.format(code, description))
