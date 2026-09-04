def build_password_service(session: Session) -> PasswordService:
    return PasswordService(
        session=session,
        user_repository=UserRepository(session),
        email_sender=EmailSender(),
        user_session_service=build_user_session_service(session,
    )
