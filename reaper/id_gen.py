# encoding: utf-8
import itertools
from reaper.constants import cities, areas, municipalities, municipality_areas

city_list = sorted(list(cities))

succ = 0x0
prev = 0x1

def get_adjacent_city_id(city_id, which_one=succ):
    def _(f, cmp):
        return (item for item in f(city_list) if cmp(item, city_id)).next()

    _cond = {
        succ: (lambda x: x, lambda item, id: item >= id),
        prev: (reversed, lambda item, id: item <= id)
    }
    return apply(_, _cond[which_one])


def get_ids(start, end):
    def get_counties(city_id):
        if city_id in municipalities:
            collection = municipality_areas
            predicate = lambda item: item.startswith(city_id[:2])
        else:
            collection = areas
            predicate = lambda item: item.startswith(city_id[:-2])

        return sorted((item for item in collection if predicate(item)))

    def get_city_id(county_id, which_one):
        # FIXME bug
        if county_id[:2] + '0000' in municipalities:
            return get_adjacent_city_id(county_id, which_one)

        probable_city_id = county_id[:-2] + '00'
        if probable_city_id in cities:
            return probable_city_id
        else:
            return get_adjacent_city_id(probable_city_id, which_one)

    def reduce_counties(chunk, city_id):
        if city_id in municipalities:
            return chunk

        chunk, counties = list(chunk), list(get_counties(city_id))
        if chunk == counties:
            return [city_id]
        else:
            return chunk

    start_city_id = get_city_id(start, succ)
    end_city_id = get_city_id(end, prev)

    counties_chunk1 = itertools.dropwhile(
        lambda county_id: county_id < start,
        get_counties(start_city_id)
    )
    counties_chunk1 = reduce_counties(counties_chunk1, start_city_id)

    cities_chunk = (item for item in cities if start_city_id < item < end_city_id)

    counties_chunk2 = itertools.takewhile(
        lambda county_id: county_id <= end,
        get_counties(end_city_id)
    )
    counties_chunk2 = reduce_counties(counties_chunk2, end_city_id)

    ids = itertools.chain(counties_chunk1, cities_chunk, counties_chunk2)

    return ids


if __name__ == '__main__':
    print sorted(list(get_ids('123333', '144499')))
    print len(sorted(list(get_ids('000000', '999999'))))
    print len(cities)


