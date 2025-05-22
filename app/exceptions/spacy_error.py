class SpacyError(Exception):
    """Exceção base para erros relacionados ao spaCy."""
    pass

class SpacyModelLoadError(SpacyError):
    """Exceção lançada quando o modelo spaCy não pode ser carregado."""
    pass

class SpacyProcessingError(SpacyError):
    """Exceção lançada durante o processamento da mensagem com spaCy."""
    pass