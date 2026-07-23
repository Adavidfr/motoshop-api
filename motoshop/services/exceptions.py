"""Excepciones de negocio del dominio MotoShop."""


class BusinessError(Exception):
    """Error de regla de negocio con mensaje legible para la API."""

    def __init__(self, message, code=None, field=None):
        self.message = message
        self.code = code
        self.field = field
        super().__init__(message)

    def as_dict(self):
        if self.field:
            return {self.field: self.message}
        return {'error': self.message}
