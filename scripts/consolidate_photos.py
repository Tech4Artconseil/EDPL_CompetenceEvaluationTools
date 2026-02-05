"""
Script to consolidate/fill `Photo_Url` for students in the database.
Usage: run from repo root (or where App can be imported):
    python -m scripts.consolidate_photos
"""
from App_Main import App
from Data_Models import Db, Studnt
from image_fetcher import name_parts, fetch_photo_url


def main():
    with App.app_context():
        students = Studnt.query.order_by(Studnt.Name).all()
        updated = 0
        for st in students:
            if st.Photo_Url:
                continue
            first, last = name_parts(st.Name)
            url = fetch_photo_url(first, last)
            if url:
                st.Photo_Url = url
                try:
                    Db.session.commit()
                    updated += 1
                    print(f"Updated {st.Id} -> {url}")
                except Exception as e:
                    Db.session.rollback()
                    print(f"Failed to update {st.Id}: {e}")
        print(f"Done. Updated {updated} students.")


if __name__ == '__main__':
    main()
