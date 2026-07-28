import os
from datetime import datetime
import fitz

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')


def sedot_metadata(file_path):
    """
    Mengambil metadata PDF atau gambar tanpa melakukan OCR.
    """

    size_str = "-"
    pages_str = "-"
    author_str = "-"
    date_str = "-"

    try:
        if not os.path.exists(file_path):
            return size_str, pages_str, author_str, date_str

        ukuran = os.path.getsize(file_path)

        if ukuran >= 1024 * 1024:
            size_str = f"{ukuran/(1024*1024):.2f} MB"
        else:
            size_str = f"{ukuran/1024:.2f} KB"

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            doc = fitz.open(file_path)

            pages_str = str(doc.page_count)

            metadata = doc.metadata

            if metadata:

                author_str = metadata.get("author") or "-"

                creation = metadata.get("creationDate")

                if creation:

                    if creation.startswith("D:"):

                        try:
                            date_str = (
                                f"{creation[8:10]}-"
                                f"{creation[6:8]}-"
                                f"{creation[2:6]}"
                            )

                        except Exception:
                            date_str = creation

                    else:
                        date_str = creation

            doc.close()

        elif ext in IMAGE_EXTENSIONS:
            pages_str = "1"
            date_str = datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).strftime("%d-%m-%Y")

    except Exception:
        pass

    return (
        size_str,
        pages_str,
        author_str,
        date_str
    )