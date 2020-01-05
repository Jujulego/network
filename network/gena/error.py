# Classes
class GENAError(Exception):
    def __init__(self, code: int, description: str):
        super().__init__(f'{code}: {description}')

        # Attributes
        self.code = code
        self.description = description
