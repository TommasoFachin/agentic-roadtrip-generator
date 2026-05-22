from tinydb import TinyDB
from app.models import UserProfile

db = TinyDB("user_profile.json")

def get_user_profile() -> UserProfile:
    data = db.get(doc_id=1)
    if data is None:
        profile = UserProfile()
        db.insert(profile.dict())
        return profile
    return UserProfile(**data)

def update_user_profile(new_data: dict) -> UserProfile:
    profile = get_user_profile()
    updated = profile.model_copy(update=new_data)
    db.update(updated.dict(), doc_ids=[1])
    return updated
