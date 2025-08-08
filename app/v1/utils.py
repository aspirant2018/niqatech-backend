'''
This file contains utility functions and classes for the Niqatech backend application.
'''

import re


def parse_xls(workbook):
    data = {"classrooms": []}  # Start with a dictionary containing a list of classrooms

    for i in range(len(workbook.sheets()) - 1):
        # Access the current sheet
        sheet = workbook.sheet_by_index(i)
        sheet_name = sheet.name
        #print(f"Processing sheet: {sheet_name}")
        
        text   = sheet.row_values(4)[0]
        term = re.search(r"الفصل\s+(\S+)", text).group(1)
        year = re.search(r"السنة الدراسية\s*:\s*(\d{4}-\d{4})", text).group(1)
        level = re.search(r"الفوج التربوي\s*:\s*([^\d\n\r]+?\d)", text).group(1).strip()
        subject = re.search(r"مادة\s*:\s*(.+)", text).group(1).strip()

        classroom = {
            #"school_name": sheet.row_values(3)[0],
            #"term": term,
            #"year": year,
            "level": level,
            #"subject": subject,
            #"classroom_id": f"Sheet-{i}",
            "sheet_name": sheet_name,
            "number_of_students": sheet.nrows - 8,
            "students": []  # Store students in a list
        }

        for row in range(8, sheet.nrows):
            student = {
                "id": int(sheet.row_values(row)[0]),
                "row": row,
                "last_name": sheet.row_values(row)[1],
                "first_name": sheet.row_values(row)[2],
                "date_of_birth": sheet.row_values(row)[3],
                "evaluation": sheet.row_values(row)[4],
                "first_assignment": sheet.row_values(row)[5],
                "final_exam": sheet.row_values(row)[6],
                "observation": sheet.row_values(row)[7]
            }
            classroom["students"].append(student)

        data["classrooms"].append(classroom)  # Add classroom to the list

    return data  # Return the dictionary


def to_float_or_none(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None