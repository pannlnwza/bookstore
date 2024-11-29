from django.core.management import call_command

def run():
    print("Dumping data...")
    with open("data/all_data.json", "w", encoding="utf-8") as f:
        call_command("dumpdata", indent=4, stdout=f)
    print("Data dumped successfully to data/all_data.json.")
