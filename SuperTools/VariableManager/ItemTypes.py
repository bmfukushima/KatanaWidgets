# item types


class MASTER_ITEM(object):
    COLUMN = 0
    COLOR = (200, 160, 0, 255)

    def __repr__(self):
        return 'master'


class PATTERN_ITEM(object):
    COLUMN = 1
    COLOR = (100, 200, 100, 255)
    BACKGROUND_COLOR = 0

    def __repr__(self):
        print('TREPPRRPRPRPPRPRPREEE??')
        return 'pattern'


class BLOCK_ITEM(object):
    COLUMN = 2
    COLOR = (128, 128, 255, 255)
    BACKGROUND_COLOR = 0

    def __repr__(self):
        return 'block'


# item groups

BLOCK_PUBLISH_GROUP = [
    MASTER_ITEM,
    BLOCK_ITEM,
    MASTER_ITEM.COLUMN,
    BLOCK_ITEM.COLUMN
]
