from django.apps import apps
from django.core.management import call_command

def run():
    excluded_models = {}  # Models to exclude
    app_label = "bookstore"  # Replace with your app's name

    print("Dumping data for all models (excluding Genre and Book)...")

    # Get all models for the specified app
    models = apps.get_app_config(app_label).get_models()

    for model in models:
        model_name = model.__name__
        if model_name in excluded_models:
            print(f"Skipping {model_name}...")
            continue

        # Dump data for the model
        file_name = f"data/{model_name.lower()}.json"
        print(f"Dumping data for {model_name} into {file_name}...")

        with open(file_name, "w", encoding="utf-8") as f:
            call_command("dumpdata", f"{app_label}.{model_name}", indent=4, stdout=f)

    print("Data dump completed!")
