# encoding: utf-8


last_page_found = 0


def partition(iterable, by=10):
    """按每by个把iterable分成若干组"""
    if not by:
        return [iterable]
    return [iterable[i * by:(i + 1) * by] for i in range(len(iterable) / by  + (1 if len(iterable) % by != 0 else 0))]


def take(iterable, by=5):
    while iterable:
        if len(iterable) < by:
            yield iterable
        else:
            yield iterable[:by]
        iterable = iterable[by:]


if __name__ == '__main__':
    for item in take(range(71), by=10):
        print item

