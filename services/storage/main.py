import base64
import mimetypes
import pickle
from uuid import uuid4
from nameko.rpc import rpc

class StorageService:
    name = "storage_service"

    @rpc
    def upload(self, filedata: dict) -> str:
        ext = mimetypes.guess_extension(filedata['mimetype'])
        if ext == None:
            return None

        filename = str(uuid4()) + ext

        with open(f"/uploads/{filename}", "wb") as openfile:
            openfile.write(base64.b64decode(filedata['content_data']))
        return filename

    @rpc
    def download(self, filename: str) -> str:
        f = open(f'/uploads/{filename}', 'rb')
        content = f.readlines()
        content_bytes = b''.join(content)
        return base64.b64encode(content_bytes).decode()
