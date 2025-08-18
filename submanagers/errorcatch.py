class ErrorCatch:
    CATCH_ERRORS = True

    @staticmethod
    def set_catch_errors(catch: bool):
        ErrorCatch.CATCH_ERRORS = catch