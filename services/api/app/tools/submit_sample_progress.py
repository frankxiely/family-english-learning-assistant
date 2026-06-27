from services.api.app.core import submit_sample_progress, today_iso

if __name__ == "__main__":
    review_asset_id = submit_sample_progress("user_mom", today_iso())
    print(review_asset_id)
