"""User service for managing default user in prototype."""

from sqlalchemy.orm import Session

from ..models.user import User


class UserService:
    """Service for managing users (prototype with default user)."""

    DEFAULT_USER_EMAIL = "prototype@fundflow.com"
    DEFAULT_COMPANY_NAME = "FundFlow Prototype"

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_default_user(self) -> User:
        """Get or create the default user for prototype."""
        # Try to find existing default user
        user = self.db.query(User).filter(User.email == self.DEFAULT_USER_EMAIL).first()

        if user:
            return user

        # Create default user
        user = User(
            email=self.DEFAULT_USER_EMAIL, company_name=self.DEFAULT_COMPANY_NAME
        )

        self.db.add(user)
        self.db.flush()
        return user
