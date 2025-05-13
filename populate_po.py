import polib
import json
import os


def load_category_translations(category_file):
    """Load category translations from a JSON file located in the questions directory."""
    try:
        with open(category_file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {category_file}: {e}")
        return None
    except FileNotFoundError:
        print(f"File {category_file} not found.")
        return None


def populate_po_with_translations(lang_code, category_files):
    po = polib.POFile()

    # Iterate through all the category files
    for category_file in category_files:
        category_data = load_category_translations(category_file)
        if not category_data:
            continue

        # Iterate through categories in the JSON data
        for category_name, category in category_data["categories"].items():
            # Iterate through each level and questions
            for level, questions in category.items():
                for question_data in questions:
                    question = question_data["question"]
                    options = question_data["options"]
                    answer = question_data["answer"]
                    explanation = question_data["explanation"]

                    # Process question translations
                    if lang_code in question:
                        msgid = question[lang_code]  # The question itself
                        msgstr = answer[
                            lang_code
                        ]  # The correct answer in the selected language
                        entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
                        po.append(entry)

                    # Process options translations
                    if lang_code in options:
                        for option in options[lang_code]:
                            msgid = option  # Each option
                            entry = polib.POEntry(msgid=msgid, msgstr=option)
                            po.append(entry)
                        # Process explanation translations
                    if lang_code in explanation:
                        msgid = explanation[lang_code]  # The explanation itself
                        entry = polib.POEntry(msgid=msgid, msgstr=msgid)
                        po.append(entry)

    # Ensure the directory exists before saving the PO file
    po_directory = f"translations/{lang_code}/LC_MESSAGES/"
    os.makedirs(po_directory, exist_ok=True)

    # Save the populated PO file for the specific language
    po.save(f"{po_directory}messages.po")
    #                 # Process explanation translations
    #                 if lang_code in explanation:
    #                     msgid = explanation[lang_code]  # The explanation itself
    #                     entry = polib.POEntry(msgid=msgid, msgstr=msgid)
    #                     po.append(entry)
    #
    # # Save the populated PO file for the specific language
    # po.save(f"translations/{lang_code}/LC_MESSAGES/messages.po")


def main():
    # Path to the questions directory where category JSON files are stored
    questions_dir = "questions"

    # List all the category JSON files inside the 'questions' directory
    category_files = [
        os.path.join(questions_dir, "carbon_emissions.json"),
        os.path.join(questions_dir, "transportation.json"),
        os.path.join(questions_dir, "waste_management.json"),
        os.path.join(questions_dir, "energy_consumption.json"),
        os.path.join(questions_dir, "food_intake.json"),
    ]

    # Populate PO files for each language
    for lang_code in ["en", "yo", "ig", "ha"]:
        populate_po_with_translations(lang_code, category_files)


if __name__ == "__main__":
    main()
