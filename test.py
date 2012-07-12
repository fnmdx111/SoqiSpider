from collections import defaultdict

if __name__ == '__main__':

    with open('134199756753.txt', 'r') as f:
        lines = f.readlines()

        d = defaultdict(int)
        for line in lines[1:]:
            s = line.split()

            d[s[0]] += 1

        print d

        keys = map(int, d.keys())
        print sorted(keys) == range(min(keys), max(keys) + 1)

