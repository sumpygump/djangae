

def starts_with(word, min_index_length, **options):
    results = []

    for i in range(min_index_length, len(word) + 1):
        results.append(word[:i])

    return results
