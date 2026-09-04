def build_token_service(session: Session) -> AuthTokenService:
    return AuthTokenService(
        session=session,
        session_repository=UserSessionRepository(session),
    )
