import webview
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.api import Api


def main():
    api = Api()

    html_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'frontend',
        'index.html'
    )

    window = webview.create_window(
        title='PC Optimizer',
        url=html_path,
        js_api=api,
        width=960,
        height=640,
        min_size=(800, 560),
        resizable=True,
        background_color='#ffffff',
    )

    webview.start(debug=False)


if __name__ == '__main__':
    main()
