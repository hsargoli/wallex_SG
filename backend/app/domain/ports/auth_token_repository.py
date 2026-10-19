import uuid
from abc import ABC, abstractmethod
from app.domain.entities.auth_token import AuthToken

class AuthTokenRepositoryPort(ABC):
    @abstractmethod
    async def create(self, token: AuthToken) -> AuthToken:
        ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> AuthToken | None:
        ...

    @abstractmethod
    async def delete_by_user_and_type(self, user_id: uuid.UUID, token_type: str) -> None:
        ...
