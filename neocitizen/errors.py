class NeocitizenError(Exception):
    """
    Base class for exceptions in this module.
    """

    pass


class CredentialsRequiredError(NeocitizenError):
    pass


class ApiError(NeocitizenError):
    pass


class ArgumentError(NeocitizenError):
    pass
