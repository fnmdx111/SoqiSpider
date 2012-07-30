# encoding: utf-8
from reaper.constants import cities, areas, municipalities, municipality_areas, total_areas
from reaper.misc import take

city_list = sorted(list(cities))

succ = 0x0
prev = 0x1

def get_adjacent_id(id, which_one=succ):
    def _(f, cmp):
        return (item for item in f(sorted(total_areas)) if cmp(item, id)).next()

    _cond = {
        succ: (lambda x: x, lambda item, id: item > id),
        prev: (reversed, lambda item, id: item < id)
    }
    return apply(_, _cond[which_one])


def get_counties(city_id):
    _ = lambda where: lambda item: item.startswith(city_id[:where])
    if city_id in municipalities:
        collection = municipality_areas
        predicate = _(2)
    else:
        collection = areas
        predicate = _(-2)

    return sorted((item for item in collection if predicate(item)))


def get_proper_id(id, which_one):
    idx = 0 if which_one == succ else -1
    if id in cities:
        return get_counties(id)[idx]
    elif id in total_areas:
        return id
    else:
        return get_adjacent_id(id, which_one)


def get_ids(start, end):
    if start == end:
        if start in cities:
            return get_counties(start)
        elif start in total_areas:
            return start,
        else:
            return ()

    start, end = get_proper_id(start, succ), get_proper_id(end, prev)

    return (item for item in total_areas if start <= item <= end)



if __name__ == '__main__':
    assert sorted(get_ids('000000', '999999')) == sorted(total_areas)
    for item1, item2 in zip(take(sorted(list(get_ids('000000', '999999')))), take(sorted(total_areas))):
        print '%s\t\t%s' % (item1, item2)
    # print sorted(list(get_ids('150000', '170000')))


