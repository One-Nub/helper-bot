class HelperError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidTriggerFormat(HelperError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
