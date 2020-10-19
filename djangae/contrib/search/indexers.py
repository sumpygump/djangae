

def starts_with(word, min_index_length, **options):
    results = []

    for i in range(min_index_length, len(word)):
        results.append(word[:i])

    return results
