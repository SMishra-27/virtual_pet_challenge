from datetime import datetime
from database import db, Pet

def update_pet_status(pet: Pet):
    now = datetime.utcnow()
    elapsed_hours = (now - pet.last_updated).total_seconds() / 3600.0

    if elapsed_hours > 0:
        # Natural decay
        pet.hunger = min(100.0, pet.hunger + 5 * elapsed_hours)   # gets hungrier
        pet.happiness = max(0.0, pet.happiness - 3 * elapsed_hours)  # gets sadder

        # Neglect system (every 6 hours = neglect event)
        neglect_intervals = int(elapsed_hours // 6)
        if neglect_intervals > 0:
            pet.neglect_count += neglect_intervals
            pet.self_destructive_index = min(1e6, 2 ** pet.neglect_count)  # cap huge values
            pet.health = max(0.0, pet.health - pet.self_destructive_index)

    # Update last checked time
    pet.last_updated = now
    db.session.commit()
    return pet
