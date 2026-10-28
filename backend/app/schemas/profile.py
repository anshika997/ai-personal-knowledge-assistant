from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileIn(BaseModel):
    full_name: str = Field(default="", max_length=120)
    bio: str = Field(default="", max_length=2000)
    interests: list[str] = Field(default_factory=list, max_length=30)
    skills: list[str] = Field(default_factory=list, max_length=50)
    learning_preferences: str = Field(default="", max_length=1000)
    personal_goals: str = Field(default="", max_length=2000)

    @field_validator("interests", "skills")
    @classmethod
    def clean_list(cls, items: list[str]) -> list[str]:
        # Remove empty items and extra spaces
        return [item.strip() for item in items if item and item.strip()]


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)
    updated_at: datetime