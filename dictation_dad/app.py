import argparse
import logging
import os

import webview

from dictation_dad.api import API

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Dictation Dad")
    parser.add_argument("--debug", action="store_true", help="启用 debug 级别日志")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

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
