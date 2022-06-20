import bcrypt
from nameko.rpc import rpc
import werkzeug

class StorageService:
    name = "storage_service"

    @rpc
    def upload(self, file) -> str:
        file.save(f"/uploads/{file.filename}")
        return file.filename

    @rpc
    def download(self, filename: str) -> str:
        # f = open(f'/uploads/{filename}', 'r')
        pass
