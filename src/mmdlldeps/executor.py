import concurrent.futures


_EXECUTOR = None


def executor():
    # Shared thread-pool executor
    global _EXECUTOR
    if not _EXECUTOR:
        _EXECUTOR = concurrent.futures.ThreadPoolExecutor()
    return _EXECUTOR
