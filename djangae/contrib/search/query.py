from django.db.models import Q

from .constants import (
    STOP_WORDS,
)

from .models import (
    WORD_DOCUMENT_JOIN_STRING,
    DocumentRecord,
    WordFieldIndex,
)

from .tokens import tokenize_content


def _tokenize_query_string(query_string):
    """
        Returns a list of WordDocumentField keys to fetch
        based on the query_string
    """

    # We always lower case. Even Atom fields are case-insensitive
    query_string = query_string.lower()

    branches = query_string.split(" or ")

    # Split into [(fieldname, query)] tuples for each branch
    field_queries = [
        tuple(x.split(":", 1)) if ":" in x else (None, x)
        for x in branches
    ]

    # Remove empty queries
    field_queries = [x for x in field_queries if x[1].strip()]

    # By this point, given the following query:
    # pikachu OR name:charmander OR name:"Mew Two" OR "Mr Mime"
    # we should have:
    # [(None, "pikachu"), ("name", "charmander"), ("name", '"mew two"'), (None, '"mr mime"')]
    # Note that exact matches will have quotes around them

    result = [
        [
            "exact" if x[1][0] == '"' and x[1][-1] == '"' else "word",
            x[0],
            x[1].strip('"')
        ]
        for x in field_queries
    ]

    # Expand
    # For non exact matches, we may have multiple words separated by spaces that need
    # to be expanded into seperate entries

    start_length = len(result)
    for i in range(start_length):
        kind, field, content = result[i]
        if kind == "exact":
            continue

        # Split on punctuation, remove double-spaces
        content = tokenize_content(content)
        content = [x.replace(" ", "") for x in content]

        if len(content) == 1:
            # Do nothing, this was a single word
            continue
        else:
            # Replace this entry with the first word
            result[i][-1] = content[0]

            # Append the rest to result
            for word in content[1:]:
                result.append(("word", field, word))

    # Remove empty entries, and stop-words and then tuple-ify
    result = [
        (kind, field, content)
        for (kind, field, content) in result
        if content and content not in STOP_WORDS
    ]

    # Now we should have
    # [
    #     ("word", None, "pikachu"), ("word", "name", "charmander"),
    #     ("exact", "name", 'mew two'), ("exact", None, 'mr mime')
    # ]

    return result


def _append_exact_word_filters(filters, prefix, field, string):
    start = "%s%s%s" % (prefix, string, WORD_DOCUMENT_JOIN_STRING)
    end = "%s%s%s%s" % (prefix, string, chr(0x10FFFF), WORD_DOCUMENT_JOIN_STRING)
    if not field:
        filters |= Q(pk__gte=start, pk__lt=end)
    else:
        filters |= Q(pk__gte=start, pk__lt=end, field_name=field)

    return filters


def _append_startswith_word_filters(filters, prefix, field, string):
    start = "%s%s" % (prefix, string)
    end = "%s%s%s" % (prefix, string, chr(0x10FFFF))

    if not field:
        filters |= Q(pk__gte=start, pk__lt=end)
    else:
        filters |= Q(pk__gte=start, pk__lt=end, field_name=field)

    return filters


def _append_stemming_word_filters(filters, prefix, field, string):
    # FIXME: Implement
    return filters


def build_document_queryset(
    query_string, index,
    use_stemming=False,
    use_startswith=False,
):

    assert(index.id)

    tokenization = _tokenize_query_string(query_string)
    if not tokenization:
        return DocumentRecord.objects.none()

    filters = Q()

    # All queries need to prefix the index
    prefix = "%s%s" % (str(index.id), WORD_DOCUMENT_JOIN_STRING)

    for kind, field, string in tokenization:
        if kind == "word":
            filters = _append_exact_word_filters(filters, prefix, field, string)
            if use_startswith:
                filters = _append_startswith_word_filters(
                    filters, prefix, field, string
                )

            if use_stemming:
                filters = _append_stemming_word_filters(
                    filters, prefix, field, string,
                )
        else:
            raise NotImplementedError("Need to implement exact matching")

    document_ids = set([
        WordFieldIndex.document_id_from_pk(x)
        for x in WordFieldIndex.objects.filter(filters).values_list("pk", flat=True)
    ])

    return DocumentRecord.objects.filter(pk__in=document_ids)
