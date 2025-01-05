import openpyxl
from .models import Income
import jdatetime

def import_excel(file):
    """Import income data from an Excel file, handling Jalali dates and field validation."""
    try:
        # Load Excel file
        wb = openpyxl.load_workbook(file)
        sheet = wb.active

        for row in sheet.iter_rows(min_row=2, values_only=True):
            try:
                # Convert Jalali to Gregorian
                day, month, year = map(int, row[0].split("/"))
                jalali_date = jdatetime.date(year, month, day)
                exact_date = jalali_date.togregorian()

                # Clean the amount field
                amount = int(str(row[1]).replace("IRR", "").replace(",", "").strip())

                # Validate Type
                income_type = row[2].strip()
                if income_type not in ["Cash", "Non-Cash"]:
                    raise ValueError(f"Invalid type: {income_type}")

                # Handle Category
                category = row[3].strip() if row[3] else "Unknown"

                # Save to database
                Income.objects.create(
                    exact_date=exact_date,
                    amount=amount,
                    type=income_type,
                    category=category
                )

            except Exception as e:
                print(f"❌ Error importing row {row}: {e}")
                continue

        return True, None
    except Exception as e:
        return False, str(e)
