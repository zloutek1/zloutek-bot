class WelcomeService:
    def __init__(self) -> None:
        pass

    def generate_welcome_text(self, guild_id: int, user_name: str) -> str:
        return f"Welcome, {user_name}!"
