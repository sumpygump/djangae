from django.db.models import Q

from .constants import (
    STOP_WORDS,
)

from .models import (
    WORD_DOCUMENT_JOIN_STRING,
    DocumentRecord,
    TokenFieldIndex,
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

    # [(None, 'test'), (None, ''"exact thing"'), (None, 'name')]

    field_queries = []

    for branch_text in branches:
        branch_queries = []

        token = []
        in_quotes = False

        def finalize_token(token):
            final_token = "".join(token)

            if not final_token:
                token.clear()
                return

            if ":" in token:
                field, final_token = final_token.split(":", 1)
            else:
                field = None
            branch_queries.append((field, final_token))
            token.clear()

        for i, c in enumerate(branch_text):
            if c == " " and not in_quotes:
                finalize_token(token)
            else:
                token.append(c)

            if c == '"':
                in_quotes = not in_quotes
        else:
            finalize_token(token)

        field_queries.append(branch_queries)

    # By this point, given the following query:
    # pikachu OR name:charmander OR name:"Mew Two" OR "Mr Mime"
    # we should have:
    # [[(None, "pikachu")], [("name", "charmander")], [("name", '"mew two"')], [(None, '"mr mime"')]]
    # Note that exact matches will have quotes around them

    result = []

    for branch in field_queries:
        branch_result = []

        for field, token in branch:
            if token[0] == '"' and token[-1] == '"':
                branch_result.append(("exact", field, token.strip('"')))
            else:
                branch_result.append(("word", field, token))

        result.append(branch_result)

    # Expand
    # For non exact matches, we may have multiple tokens separated by spaces that need
    # to be expanded into seperate entries
    for branch_result in result:
        start_length = len(branch_result)
        for i in range(start_length):
            kind, field, content = branch_result[i]
            if kind == "exact":
                continue

            # Split on punctuation, remove double-spaces
            content = tokenize_content(content)
            content = [x.replace(" ", "") for x in content]

            if len(content) == 1:
                # Do nothing, this was a single token
                continue
            else:
                # Replace this entry with the first token
                branch_result[i] = (kind, field, content[0])

                # Append the rest to branch_result
                for token in content[1:]:
                    branch_result.append(("word", field, token))

    for i, branch_result in enumerate(result):
        # Remove empty entries, and stop-words and then tuple-ify
        result[i] = [
            (kind, field, content)
            for (kind, field, content) in branch_result
            if content and content not in STOP_WORDS
        ]

    # Now we should have
    # [
    #     [("word", None, "pikachu")], [("word", "name", "charmander")],
    #     [("exact", "name", 'mew two')], [("exact", None, 'mr mime')]
    # ]

    return result


def _append_exact_word_filters(filters, prefix, field, string):
    start = "%s%s%s" % (prefix, string, WORD_DOCUMENT_JOIN_STRING)
    end = "%s%s%s%s" % (prefix, string, WORD_DOCUMENT_JOIN_STRING, chr(0x10FFFF))

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
    match_all=True,
):

    assert(index.id)

    tokenization = _tokenize_query_string(query_string)
    if not tokenization:
        return DocumentRecord.objects.none()

    if not match_all:
        # If match_all is false, we split the branches into a branch per token
        split_branches = []
        for branch in tokenization:
            for token in branch:
                split_branches.append([token])
        tokenization = split_branches

    # We now need to gather document IDs, for each branch we need to
    # look for matching tokens in a single query, then post-process them
    # to only fetch documents that match all of them.

    document_ids = set()
    for branch in tokenization:
        token_count = len(branch)

        # All queries need to prefix the index
        prefix = "%s%s" % (str(index.id), WORD_DOCUMENT_JOIN_STRING)
        filters = Q()

        for kind, field, string in branch:
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

        keys = TokenFieldIndex.objects.filter(filters).values_list("pk", flat=True)

        doc_results = {}

        for pk in keys:
            doc_id = TokenFieldIndex.document_id_from_pk(pk)
            doc_results.setdefault(doc_id, set()).add(pk.split("|")[1])

        document_ids |= set([k for k, v in doc_results.items() if len(v) == token_count])

    return DocumentRecord.objects.filter(pk__in=document_ids)
