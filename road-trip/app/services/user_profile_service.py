from tinydb import TinyDB
from app.models import UserProfile
from tinydb.storages import JSONStorage
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer
from datetime import date



# --- CONFIGURAZIONE SERIALIZZAZIONE PER DATE ---
# Questo middleware "insegna" a TinyDB come salvare e caricare
# gli oggetti `date` di Python, che non sono JSON serializzabili di default.
serialization = SerializationMiddleware(JSONStorage)
serialization.register_serializer(DateTimeSerializer(), 'date')

db = TinyDB("user_profile.json", storage=serialization)

def get_user_profile() -> UserProfile:
    data = db.get(doc_id=1)
    if data:
        return UserProfile(**data)
    # Se non esiste, crea un profilo vuoto
    profilo_vuoto = UserProfile()
    db.insert(profilo_vuoto.model_dump(mode="json"))
    return profilo_vuoto

def update_user_profile(new_data: dict) -> UserProfile:
    profile = get_user_profile()
    updated = profile.model_copy(update=new_data)
    db.update(updated.model_dump(mode="json"), doc_ids=[1])
    return updated
