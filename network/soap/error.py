# Classes
class SOAPError(Exception):
    def __init__(self, code: int, description: str):
        super().__init__(f'{description} ({code})')

        # Attributes
        self.code = code
        self.description = description
