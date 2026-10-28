from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["Profile"])


def _get_or_create_profile(db: Session) -> Profile:
    """This app has one user, so there is only one profile row."""
    profile = db.execute(select(Profile).limit(1)).scalar_one_or_none()
    if profile is None:
        profile = Profile(
            full_name="", bio="", interests=[], skills=[],
            learning_preferences="", personal_goals="",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    return _get_or_create_profile(db)


@router.put("", response_model=ProfileOut)
def update_profile(data: ProfileIn, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    profile.full_name = data.full_name
    profile.bio = data.bio
    profile.interests = data.interests
    profile.skills = data.skills
    profile.learning_preferences = data.learning_preferences
    profile.personal_goals = data.personal_goals
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("", status_code=204)
def reset_profile(db: Session = Depends(get_db)):
    """Clear all saved profile information."""
    profile = _get_or_create_profile(db)
    profile.full_name = ""
    profile.bio = ""
    profile.interests = []
    profile.skills = []
    profile.learning_preferences = ""
    profile.personal_goals = ""
    db.commit()