from Background_work import update_pet_status
from database import get_connection
from flask import Flask, render_template, request, jsonify
from game_logic import VirtualPetML
import database
from behaviour import Pet
from datetime import datetime
import random

# -------------------------
# Flask Setup
# -------------------------
app = Flask(__name__)

# -------------------------
# Initialize DB + Pet
# -------------------------
database.init_db()
pet_id = database.add_pet("Buddy")   # stored in DB
pet = VirtualPetML(name="Buddy")     # game logic + ML mood
behaviour_pet = Pet()                # behaviour system

# Add required attributes for behaviour.py
behaviour_pet.day = 1
behaviour_pet.difficulty = 1
behaviour_pet.interaction_history = []

# -------------------------
# Routes
# -------------------------
@app.route("/")
@app.route("/status/<int:pet_id>")
def pet_status(pet_id):
    # Update the pet's status first
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pets WHERE id=?", (pet_id,))
    pet_row = cursor.fetchone()

    if pet_row:
        # Convert DB row into a dict
        pet = {
            "id": pet_row[0],
            "name": pet_row[1],
            "species": pet_row[2],
            "hunger": pet_row[3],
            "happiness": pet_row[4],
            "energy": pet_row[5],
            "last_updated": pet_row[6]
        }

        # Apply background logic
        updated_pet = update_pet_status(pet)

        return jsonify(updated_pet)

    return jsonify({"error": "Pet not found"}), 404

def home():
    status = pet.get_status()
    return render_template("index.html", pet=status)

@app.route("/interact", methods=["POST"])
def interact():
    action = request.json.get("action")

    # Perform action
    if action == "feed":
        message = pet.feed_pet()
    elif action == "play":
        message = pet.play_pet()
    elif action == "sleep":
        message = pet.sleep_pet()
    else:
        message = "Unknown action."

    # Update behaviour interaction history
    behaviour_pet.interaction_history.append(datetime.now().hour)

    # Update difficulty daily (example: each interaction = 1 "day")
    behaviour_pet.update_difficulty()
    behaviour_pet.day += 1

    # Get latest state
    state = pet.get_status()

    # Update DB
    database.update_pet(pet_id, state)
    database.save_pet_action(pet_id, action, message)

    return jsonify({
        "message": message,
        "state": state,
        "difficulty": behaviour_pet.difficulty
    })

@app.route("/attention", methods=["GET"])
def attention():
    """Simulate the pet demanding attention."""
    demand_hour = random.choice(range(24))
    current_hour = datetime.now().hour
    if current_hour == demand_hour or behaviour_pet.difficulty > 5:
        response = "Pet is demanding attention now! 🐾"
    else:
        response = "Pet is calm."
    return jsonify({"attention": response})

@app.route("/train", methods=["GET"])
def train_model():
    """Trigger behaviour ML training."""
    unavailable = behaviour_pet.train_ml_model()
    if unavailable:
        return jsonify({"unavailable_hours": unavailable})
    return jsonify({"message": "Not enough interaction history to train model."})

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)
