def build_mfa_service(session: Session) -> MfaService:
    return MfaService(
        session=session,
        user_repository=UserRepository(session),
        token_service=_build_token_service(session),
    )
