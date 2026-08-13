class ZotlocalError(RuntimeError):
    pass


class ZoteroDown(ZotlocalError):
    pass


class ZoteroHttpError(ZotlocalError):
    def __init__(self, status: int, path: str, body: str = "") -> None:
        self.status = status
        self.path = path
        self.body = body
        super().__init__(f"Zotero HTTP {status} on {path}")
