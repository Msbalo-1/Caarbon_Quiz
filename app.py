from flask import (
    Flask, render_template, request, g, redirect, url_for, session, jsonify, flash, send_from_directory,
)
from flask_babel import Babel, gettext
import os
import json
import sqlite3
sqlite3.threadsafety = 3

# Initialize Flask app and Babel
app = Flask(__name__)
app.secret_key = "your_secret_key"
babel = Babel(app)

# Supported languages
LANGUAGES = ["en", "yo", "ig", "ha"]
app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_TRANSLATION_DIRECTORIES"] = "./translations"

# Define the locale selector function
def get_locale():
    return session.get("language", "en")

@app.before_request
def load_ui_text():
    lang = session.get("language", "en")
    g.ui_text = load_ui_translations(lang)
    g.category_text = load_category_translations(lang)


# Configure Babel to use the locale selector function
babel.init_app(app, locale_selector=get_locale)

# Context processor to expose the locale to Jinja templates
@app.context_processor
def inject_globals():
    return {
"current_locale": get_locale(),
"ui_text": getattr(g, "ui_text", {}),
"category_text": getattr(g, "category_text", {}),
}

# Load UI translations from JSON file
# Load UI translations
def load_ui_translations(lang):
    file_path = os.path.join(os.path.dirname(__file__), "translations", "ui_translations.json")

    if not os.path.exists(file_path):
        print(f"[ERROR] Translation file not found at: {file_path}")
        return {}

    with open(file_path, "r", encoding="utf-8") as file:
        try:
            translations = json.load(file)
            return translations.get(lang, translations.get("en", {}))
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse translation JSON: {e}")
            return {}
        
        
def load_category_translations(lang):
    with open("translations/category_translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    return translations.get(lang, translations["en"])  # fallback to English

# Database setup
DATABASE = "carbon_game.db"

# Helper function: Database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Route: Change language
@app.route("/change_language/<language>")
def change_language(language):
    if language in LANGUAGES:
        session["language"] = language
    return redirect(request.referrer or url_for("main"))

print("LOADED UI TRANSLATIONS:", load_ui_translations("en"))


# Landing Page (Dashboard)
@app.route("/")
def index():
    lang = get_locale()
    ui_translations = load_ui_translations(lang)  # Load UI translations based on language
    return render_template("dashboard.html", translations=ui_translations)

# Route: Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password),
        )
        conn.commit()
        conn.close()

        flash(gettext("Registration successful! Please log in."), "success")
        return redirect(url_for("login"))
    return render_template("register.html")

# Route: Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["language"] = session.get("language", "en")  # Default to English
            flash(gettext("Login successful!"))
            return redirect(url_for("main"))
        else:
            flash(gettext("Invalid email or password. Please try again."), "danger")
    return render_template("login.html")

# Route: Logout
@app.route("/logout")
def logout():
    session.clear()
    flash(gettext("Logged out successfully."))
    return redirect(url_for("login"))

# Route: Main page (Categories and Levels)
@app.route("/home")
def main():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Define categories and their respective levels
    categories = {
        "carbon_emissions": ["level_1", "level_2", "level_3"],
        "transportation": ["level_1", "level_2", "level_3"],
        "waste_management": ["level_1", "level_2", "level_3"],
        "energy_consumption": ["level_1", "level_2", "level_3"],
        "food_intake": ["level_1", "level_2", "level_3"],
    }

    # Load translations for UI elements
    lang = get_locale()
    ui_translations = load_ui_translations(lang)

    return render_template("main.html", categories=categories, ui_translations=ui_translations)

# Helper function to get the next level
def get_next_level(current_level):
    levels = ["level_1", "level_2", "level_3"]
    index = levels.index(current_level)
    return levels[index + 1] if index < len(levels) - 1 else None

# Helper function to get the previous level
def get_previous_level(current_level):
    levels = ["level_1", "level_2", "level_3"]
    index = levels.index(current_level)
    return levels[index - 1] if index > 0 else None



# Load questions dynamically
@app.route("/play/<category>/<level>")
def play_game(category, level):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    conn = get_db_connection()
    user = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

  

    # Check if the user has completed the previous level
    conn = get_db_connection()
    previous_level = get_previous_level(level)
    if previous_level:
        progress = conn.execute(
            "SELECT completed FROM user_progress WHERE user_id = ? AND category = ? AND level = ?",
            (user_id, category, previous_level),
        ).fetchone()
        if not progress or not progress["completed"]:
            conn.close()
            return jsonify({"error": gettext("You must complete the previous level first.")})

    # Map the file path for the category JSON
    file_path = os.path.join("questions", f"{category}.json")
    if not os.path.exists(file_path):
        return "Category not found", 404

    # Load the JSON data
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Get the questions for the selected level
    category_data = data.get("categories", {}).get(category, {})
    questions = category_data.get(f"{level}", [])

    # If no questions are available, return an error message
    if not questions:
        return f"No questions available for {category} at level {level}", 404

    # Get the user's selected language or default to English
    user_language = session.get("language", "en")

    # Filter the data based on the user's language
    filtered_data = []
    for item in questions:
        filtered_item = {
            "id": item.get("id"),  # Ensure each question has a unique ID
            "question": item.get("question").get(user_language),
            "options": item.get("options").get(user_language),
            "answer": item.get("answer").get(user_language),
            "explanation": item.get("explanation").get(user_language),
        }
        filtered_data.append(filtered_item)

    # Pagination logic
    page = request.args.get("page", 1, type=int)  # Get the current page from the query string
    per_page = 1  # Show one question per page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_questions = filtered_data[start:end]


    # ✅ Get next level for progression
    next_level = get_next_level(level)

    current_level_number = int(level.split("_")[1])
    next_level = f"level_{current_level_number + 1}"

    # Pass questions, pagination info, and language to the template
    return render_template(
        "play.html",
        questions=paginated_questions,
        language=user_language,
        level=level,
        category=category,
        current_page=page,
        total_pages=len(filtered_data),
        next_level=next_level,
        user_points=user["points"]

    )




BADGES = {
    "carbon_emissions_level_1": ("Carbon Cadet", "Beginner understanding of emissions"),
    "carbon_emissions_level_2": ("Emission Analyst", "Intermediate knowledge"),
    "carbon_emissions_level_3": ("Carbon Crusader", "Mastery of carbon emissions"),

    "transportation_level_1": ("Eco Rider", "Knows greener transport choices"),
    "transportation_level_2": ("Transit Tactician", "Applies low-carbon travel methods"),
    "transportation_level_3": ("Green Mover", "Mastered sustainable transport behaviors"),

    "waste_management_level_1": ("Trash Tracker", "Understands basic waste sorting"),
    "waste_management_level_2": ("Waste Warrior", "Advocates proper waste handling"),
    "waste_management_level_3": ("Recycle Ranger", "Masters recycling and waste reduction"),

    "energy_consumption_level_1": ("Power Saver", "Learns energy-saving basics"),
    "energy_consumption_level_2": ("Energy Expert", "Applies smart energy habits"),
    "energy_consumption_level_3": ("Efficiency Engineer", "Masters energy efficiency practices"),

    "food_intake_level_1": ("Food Footprint Fighter", "Aware of food’s carbon impact"),
    "food_intake_level_2": ("Green Grocer", "Chooses low-emission diets"),
    "food_intake_level_3": ("Eco Chef", "Fully understands sustainable food choices"),
}




@app.route("/submit_answer", methods=["POST"])
def submit_answer():
    if "user_id" not in session:
        return jsonify({"error": gettext("You must be logged in to play.")})

    user_id = session["user_id"]
    category = request.json.get("category")
    level = request.json.get("level")
    question_id = request.json.get("question_id")
    answer = request.json.get("answer")

    # Load questions from the selected category and level
    filepath = os.path.join("questions", f"{category}.json")
    if not os.path.exists(filepath):
        return jsonify({"error": gettext("Category not found.")})

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)
        category_data = data.get("categories", {}).get(category, {})
        questions = category_data.get(level, [])

    # Find the question based on ID
    question = next((q for q in questions if q["id"] == question_id), None)
    if not question:
        return jsonify({"error": gettext("Question not found.")})

    # Get the user's selected language or default to English
    user_language = session.get("language", "en")

    # Check if the answer is correct
    correct_answer = question["answer"].get(user_language)
    correct = answer == correct_answer

    # Track attempts for the question
    if "attempts" not in session:
        session["attempts"] = {}
    if question_id not in session["attempts"]:
        session["attempts"][question_id] = 0
    session["attempts"][question_id] += 1

    # Calculate points based on attempts
    if correct:
        points = 5 if session["attempts"][question_id] == 1 else 4  # Reduce points for second attempt
    else:
        points = 0

    # Update user points in the database
    conn = get_db_connection()
    user = conn.execute("SELECT points FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": gettext("User not found.")})

    # Check if the level has already been completed
    progress = conn.execute(
        "SELECT completed FROM user_progress WHERE user_id = ? AND category = ? AND level = ?",
        (user_id, category, level),
    ).fetchone()

    if progress and progress["completed"]:
        # If the level is already completed, do not allocate points
        points = 0
        level_completed = True
    else:
        level_completed = False

    new_points = user["points"] + points
    conn.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, user_id))

    # Check if this is the last question in the level (since we have exactly 3 questions)
    if correct and not level_completed:
        # Get all question IDs for this level
        question_ids = [q["id"] for q in questions]
        
        # Check if user has answered all questions correctly
        answered_questions = conn.execute(
            "SELECT question_id FROM user_answers WHERE user_id = ? AND category = ? AND level = ? AND correct = 1",
            (user_id, category, level)
        ).fetchall()
        
        answered_ids = [a["question_id"] for a in answered_questions]
        
        # Check if current question is already answered
        if question_id not in answered_ids:
            # Record this correct answer
            conn.execute(
                "INSERT INTO user_answers (user_id, category, level, question_id, correct) VALUES (?, ?, ?, ?, ?)",
                (user_id, category, level, question_id, 1)
            )
            answered_ids.append(question_id)
        
        # Check if all 3 questions are answered correctly
        if len(answered_ids) >= 3 and all(qid in answered_ids for qid in question_ids):
            level_completed = True
            conn.execute(
                "INSERT OR REPLACE INTO user_progress (user_id, category, level, completed) VALUES (?, ?, ?, ?)",
                (user_id, category, level, True),
            )
    
   # Determine the next level
    all_levels = list(category_data.keys())  # ["level_1", "level_2", "level_3"]
    all_levels.sort()  # Ensure they are ordered

    try:
        current_index = all_levels.index(level)
        next_level = all_levels[current_index + 1] if current_index + 1 < len(all_levels) else None
    except ValueError:
        next_level = None

    # Check if all levels in this category are completed
    completed_levels = conn.execute(
        "SELECT level FROM user_progress WHERE user_id = ? AND category = ? AND completed = 1",
        (user_id, category)
    ).fetchall()
    completed_level_names = [lvl["level"] for lvl in completed_levels]
    category_completed = all(lvl in completed_level_names for lvl in all_levels)



    conn.commit()
    conn.close()



    # If the answer is correct, award a badge
    badge_awarded = None
    if level_completed:
        badge_key = f"{category.lower().replace(' ', '_')}_level_{level[-1]}"
        award_badge(user_id, badge_key)
        badge_awarded = badge_key

    # Return response with updated points, result message, and explanation
    return jsonify(
        {
            "correct": correct,
            "points": new_points,
            "message": gettext("Correct!" if correct else "Incorrect."),
            "explanation": question["explanation"].get(user_language),
            "attempts": session["attempts"][question_id],
            "level_completed": level_completed,
            "badge": badge_awarded,
            "next_level": next_level,
            "category_completed": category_completed

        }
    )



# Serve static badge images
@app.route("/static/badges/<badge_key>")
def badge_image(badge_key):
    return send_from_directory(
        os.path.join(app.root_path, "static", "images", "badges"), badge_key
    )

# Award Badge Function
def award_badge(user_id, badge_key):
    if badge_key not in BADGES:
        print(f"Invalid badge: {badge_key}")
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM user_badges WHERE user_id = ? AND badge_name = ?",
            (user_id, badge_key),
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO user_badges (user_id, badge_name) VALUES (?, ?)",
                (user_id, badge_key),
            )
            conn.commit()
            flash(f"You've earned a new badge: {BADGES[badge_key][0]}!", "success")


# Profile Page
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    user = conn.execute(
        "SELECT username, email, points FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    badges_data = conn.execute(
        "SELECT badge_name FROM user_badges WHERE user_id = ?", (session["user_id"],)
    ).fetchall()
    conn.close()

   
    # Construct badge display info using shared image
    badges = []
    for row in badges_data:
        badge_key = row["badge_name"]
        name, description = BADGES.get(badge_key, ("Unknown Badge", "No description available"))
        badges.append({
            "icon_url": url_for("static", filename="images/badges/badge.png"),
            "name": name,
            "description": description
        })

    return render_template("profile.html", user=user, badges=badges)

# Newsletter subscription
@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    if not email:
        flash("Please provide a valid email address.")
        return redirect(url_for("index"))

    with open("subscribers.txt", "a") as f:
        f.write(email + "\n")

    flash("You have successfully subscribed to our newsletter!")
    return redirect(url_for("index"))

@app.route("/leaderboard")
def leaderboard():
    conn = get_db_connection()

    # Fetch live leaderboard data from users table
    leaderboard_data = conn.execute(
        """
        SELECT username, points 
        FROM users 
        ORDER BY points DESC 
        LIMIT 20
    """
    ).fetchall()

    # Optionally, record current leaderboard positions in leaderboard table
    for position, user in enumerate(leaderboard_data, start=1):
        conn.execute(
            """
            INSERT INTO leaderboard (user_id, position, points)
            VALUES ((SELECT id FROM users WHERE username = ?), ?, ?)
        """,
            (
                user["username"],
                position,
                user["points"],
            ),
        )

    conn.commit()
    conn.close()

    return render_template("leaderboard.html", leaderboard=leaderboard_data)

if __name__ == "__main__":
    app.run(debug=True)


