# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.core.paginator import Paginator, EmptyPage


def pager(objects, items_per_page, current_page_number):
    p = Paginator(objects, items_per_page)

    page = {}

    page["current"] = 1 if current_page_number is None else int(current_page_number)

    try:
        pager = p.page(page["current"])

    except EmptyPage:
        return False

    page["has_next"] = pager.has_next()
    page["next"] = page["current"] + 1
    page["has_previous"] = pager.has_previous()
    page["previous"] = page["current"] - 1
    page["has_other"] = pager.has_other_pages()

    page["end_index"] = pager.end_index()
    page["start_index"] = pager.start_index()
    page["total_items"] = len(objects)

    # if a Pyes resultset, won't need paginator to splice it
    if objects.__class__.__name__ == "ResultSet":
        page["objects"] = objects
    else:
        page["objects"] = pager.object_list

    page["num_pages"] = p.num_pages

    return page
