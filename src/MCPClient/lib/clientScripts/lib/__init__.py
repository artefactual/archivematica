import dicts


def setup_dicts(settings):
    dicts.setup(
        shared_directory=settings.SHARED_DIRECTORY,
        processing_directory=settings.PROCESSING_DIRECTORY,
        watch_directory=settings.WATCH_DIRECTORY,
        rejected_directory=settings.REJECTED_DIRECTORY,
    )
