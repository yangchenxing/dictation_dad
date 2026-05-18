import os

import webview

from dictation_dad.api import API


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vocabulary_dir = os.path.join(base_dir, "vocabulary")
    os.makedirs(vocabulary_dir, exist_ok=True)
    api = API(vocabulary_dir)
    html_path = os.path.join(base_dir, "static", "index.html")
    webview.create_window(
        "Dictation Dad",
        html_path,
        js_api=api,
        width=1024,
        height=768,
    )
    webview.start()


if __name__ == "__main__":
    main()
