from services.api.app.core import generate_and_save_today, today_iso

if __name__ == "__main__":
    lesson_asset_id = generate_and_save_today("user_mom", today_iso())
    print(lesson_asset_id)
