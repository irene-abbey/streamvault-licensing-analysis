import time


def not_built(name):
    print(f"{name}: not built yet")


STAGES = [
    ("load ids", lambda: not_built("load ids")),
    ("fetch", lambda: not_built("fetch")),
    ("flatten", lambda: not_built("flatten")),
    ("join", lambda: not_built("join")),
    ("analyse", lambda: not_built("analyse")),
]


def main():
    timings = {}
    for name, stage in STAGES:
        start = time.perf_counter()
        stage()
        timings[name] = round(time.perf_counter() - start, 3)
    print("Seconds per stage:", timings)


if __name__ == "__main__":
    main()