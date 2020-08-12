# item types


class MASTER_ITEM(object):
    COLUMN = 0

    def __repr__(self):
        return 'master'


class PATTERN_ITEM(object):
    COLUMN = 1

    def __repr__(self):
        return 'pattern'


class BLOCK_ITEM(object):
    COLUMN = 2

    def __repr__(self):
        return 'block'


# item groups

BLOCK_PUBLISH_GROUP = [
    MASTER_ITEM,
    BLOCK_ITEM,
    MASTER_ITEM.COLUMN,
    BLOCK_ITEM.COLUMN
]
