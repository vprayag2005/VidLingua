class VidLinguaError(Exception):
    """Base exception for all VidLingua errors."""

    pass


class DownloadError(VidLinguaError):
    """Raised when media downloading fails."""

    pass


class TranslationError(VidLinguaError):
    """Raised when text translation fails."""

    pass


class AudioGenerationError(VidLinguaError):
    """Raised when generating audio from text fails."""

    pass


class MergeError(VidLinguaError):
    """Raised when merging audio and video fails."""

    pass
