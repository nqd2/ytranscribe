from __future__ import annotations


class YTranscribeError(Exception):
    pass


class DependencyError(YTranscribeError):
    pass


class DownloadError(YTranscribeError):
    pass


class AudioProcessError(YTranscribeError):
    pass


class TranscribeError(YTranscribeError):
    pass

