from content.models import Encyclopedia


def build_encyclopedia_tree():
    """
    Fetch all encyclopedia entries in a single query and build the full tree in memory.

    Sets on each entry:
      - depth          (int, 0-indexed from root)
      - has_children   (bool)
      - children_count (int)
      - tree_children (list of child entries, ordered by name)

    Returns (roots, max_depth) where roots is the ordered list of root entries.
    """
    all_entries = list(Encyclopedia.objects.order_by('name'))

    entry_map = {e.id: e for e in all_entries}
    roots = []

    for e in all_entries:
        e.tree_children = []
        e.has_children = False
        e.children_count = 0

    for e in all_entries:
        if e.parent_id is None:
            roots.append(e)
        else:
            parent = entry_map.get(e.parent_id)
            if parent is not None:
                parent.tree_children.append(e)

    for e in all_entries:
        e.has_children = bool(e.tree_children)
        e.children_count = len(e.tree_children)

    max_depth = 0

    def annotate_depth(entry, depth):
        nonlocal max_depth
        entry.depth = depth
        if depth > max_depth:
            max_depth = depth
        for child in entry.tree_children:
            annotate_depth(child, depth + 1)

    for root in roots:
        annotate_depth(root, 0)

    return roots, max_depth
