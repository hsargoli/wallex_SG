import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.auth_token import AuthToken
from app.domain.ports.auth_token_repository import AuthTokenRepositoryPort
from app.infrastructure.db.models.auth_token import AuthTokenModel

class AuthTokenRepository(AuthTokenRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: AuthToken) -> AuthToken:
        db_token = AuthTokenModel(
            id=token.id, user_id=token.user_id, token_hash=token.token_hash,
            token_type=token.token_type, expires_at=token.expires_at, created_at=token.created_at
        )
        self.session.add(db_token)
        await self.session.commit()
        return token

    async def get_by_hash(self, token_hash: str) -> AuthToken | None:
        result = await self.session.execute(select(AuthTokenModel).where(AuthTokenModel.token_hash == token_hash))
        db = result.scalar_one_or_none()
        if not db: return None
        return AuthToken(id=db.id, user_id=db.user_id, token_hash=db.token_hash, token_type=db.token_type, expires_at=db.expires_at, created_at=db.created_at)

    async def delete_by_user_and_type(self, user_id: uuid.UUID, token_type: str) -> None:
        await self.session.execute(delete(AuthTokenModel).where(AuthTokenModel.user_id == user_id, AuthTokenModel.token_type == token_type))
        await self.session.commit()
