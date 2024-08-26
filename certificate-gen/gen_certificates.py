import os
import csv
from pathlib import Path


participants = []
with open("2023_participants_test.csv") as f:
    reader = csv.reader(f, delimiter=',', quotechar='"')
    for idx, row in enumerate(reader):
        if not idx:
            continue
        participants.append((f"{row[0]} {row[1]}", row[2]))

print("Total participants:", len(participants))

base_certificate = None
with open("base.svg") as f:
    base_certificate = f.read()

register = {}
for idx, participant in enumerate(participants):
    name, email = participant
    content = base_certificate.replace("PERSON_NAME", name)

    fname = f'out/{name.lower().replace(" ", "_")}'
    fname_svg = Path(f"{fname}.svg")
    fname_pdf = Path(f"{fname}.pdf")

    if name in register:
        print(f"Repeated name: {name} - {email}")
        print(f"  already had: {name} {register[name]}")
    else:
        register[name] = email

    if fname_pdf.exists() and fname_svg.exists():
        #print(f"Skipping: {fname}")
        continue

    with open(str(fname_svg), "w") as svg:
        svg.write(content)

    os.system(f"inkscape {fname_svg} --export-area-drawing --batch-process --export-type=pdf --export-filename={fname_pdf}")
