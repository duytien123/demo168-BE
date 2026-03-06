def retrieve_sort_columns_orm(order_by: str, model) -> list:
    """
    Parses the order_by string and constructs a list of sorting columns for SQLAlchemy ORM queries.

    Args:
        order_by (str): A comma-separated string of column names to sort by. Prefix a column name with '-' for descending order.
        model: The SQLAlchemy ORM model to retrieve columns from.

    Returns:
        list: A list of SQLAlchemy column objects with the appropriate sorting order applied.

    Example:
        order_by = "id,-name"
        model = UserGroup
        retrieve_sort_columns_orm(order_by, model)
        # Returns [UserGroup.id.asc(), UserGroup.name.desc()]
    """
    if not order_by:
        return []
    sort_columns = []
    for field in order_by.split(","):
        if field.startswith("-"):
            sort_columns.append(getattr(model, field[1:]).desc())
        else:
            sort_columns.append(getattr(model, field).asc())
    return sort_columns
