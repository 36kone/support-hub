def build_auth_service(session: Session) -> AuthService:
    return AuthService(
        user_repository=UserRepository(session),
        token_service=_build_token_service(session),
        mfa_service=build_mfa_service(session),
    )
