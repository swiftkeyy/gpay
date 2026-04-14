def get_offset(page: int, page_size: int) -> int:
    return max(0, (page - 1) * page_size)


def total_pages(total: int, page_size: int) -> int:
    if total <= 0:
        return 1
    return ((total - 1) // page_size) + 1
