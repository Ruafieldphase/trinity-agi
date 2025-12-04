import csv, itertools
def read_csv_head(path: str, n: int = 5):
    out = []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.reader(f)
        for i, row in zip(range(n), r):
            out.append(row)
    return out
