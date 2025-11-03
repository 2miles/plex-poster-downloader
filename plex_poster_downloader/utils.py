def increment_counter(result, counters):
    if result == "skipped":
        counters["skipped"] += 1
    elif result == "downloaded":
        counters["downloaded"] += 1
