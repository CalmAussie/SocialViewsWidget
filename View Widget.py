import sys
import subprocess
import importlib
import os
import webbrowser
import yt_dlp
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QProgressBar,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QFont

# Ensure yt-dlp is installed
try:
    importlib.import_module("yt_dlp")
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp


class VideoCard(QFrame):
    def __init__(self, platform, logo_path, url, parent_widget=None):
        super().__init__()
        self.platform = platform
        self.url = url
        self.prev_views = None
        self.prev_likes = None
        self.parent_widget = parent_widget

        # Card style
        self.setStyleSheet("""
            QFrame {
                background-color: #e6e6e6;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        self.setFrameShadow(QFrame.Raised)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Logo (left side)
        logo_container = QVBoxLayout()
        logo_container.setAlignment(Qt.AlignVCenter)
        self.logo_label = QLabel()
        if os.path.exists(logo_path):
            self.logo_label.setPixmap(QPixmap(logo_path).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_container.addWidget(self.logo_label)
        main_layout.addLayout(logo_container)

        # Stack on the right: title, views, likes, buttons
        self.info_layout = QVBoxLayout()
        self.info_layout.setAlignment(Qt.AlignVCenter)
        self.info_layout.setSpacing(2)
        self.info_layout.setContentsMargins(0, 0, 0, 0)

        # Title label
        self.title_label = QLabel(platform)
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.info_layout.addWidget(self.title_label)

        # Views label
        self.views_label = QLabel("👀 Views: 0")
        self.views_label.setFont(QFont("Segoe UI", 10))
        self.views_label.setAlignment(Qt.AlignLeft)
        self.info_layout.addWidget(self.views_label)

        # Likes label
        self.likes_label = QLabel("👍 Likes: 0")
        self.likes_label.setFont(QFont("Segoe UI", 10))
        self.likes_label.setAlignment(Qt.AlignLeft)
        self.info_layout.addWidget(self.likes_label)

        # Buttons container (horizontal: link + remove)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Link button
        self.link_button = QPushButton("Link")
        self.link_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border-radius: 5px;
                padding: 3px 7px;
                max-width: 60px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.link_button.clicked.connect(lambda: webbrowser.open(self.url))
        buttons_layout.addWidget(self.link_button)

        # Remove button
        self.remove_button = QPushButton("Remove")
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: #ffffff;
                border-radius: 5px;
                padding: 3px 7px;
                max-width: 70px;
            }
            QPushButton:hover {
                background-color: #c12e2a;
            }
        """)
        self.remove_button.clicked.connect(self.remove_self)
        buttons_layout.addWidget(self.remove_button)

        self.info_layout.addLayout(buttons_layout)
        main_layout.addLayout(self.info_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    # ----------------- Update stats with trend difference -----------------
    def update_stats(self, title, views, likes):
        # Views difference
        if self.prev_views is not None:
            diff_views = views - self.prev_views
            view_arrow = f" 📈(+{diff_views})" if diff_views > 0 else f" 📉({diff_views})" if diff_views < 0 else ""
        else:
            view_arrow = ""

        # Likes difference
        if self.prev_likes is not None:
            diff_likes = likes - self.prev_likes
            like_arrow = f" 📈(+{diff_likes})" if diff_likes > 0 else f" 📉({diff_likes})" if diff_likes < 0 else ""
        else:
            like_arrow = ""

        # Update previous values
        self.prev_views = views
        self.prev_likes = likes

        # Update labels
        self.title_label.setText(title)
        self.views_label.setText(f"👀 Views: {views:,}{view_arrow}")
        self.likes_label.setText(f"👍 Likes: {likes:,}{like_arrow}")

    # ----------------- Remove self from parent -----------------
    def remove_self(self):
        if self.parent_widget:
            self.parent_widget.cards_layout.removeWidget(self)
            self.parent_widget.video_cards.remove(self)
            self.setParent(None)


class SocialStatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.refresh_interval = 60
        self.timer_count = 0
        self.video_cards = []

        self.setStyleSheet("background-color: #ffffff;")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Single input box
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("Paste YouTube/TikTok links (comma-separated)")
        self.link_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border-radius: 10px;
                border: 1px solid #cccccc;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.link_input)

        # Add/Fetch button
        self.add_button = QPushButton("Add Videos")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.add_button.clicked.connect(self.add_videos)
        main_layout.addWidget(self.add_button)

        # Scrollable area for video cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.cards_container.setLayout(self.cards_layout)
        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area)

        # Bottom progress bar
        self.progress = QProgressBar()
        self.progress.setMaximum(self.refresh_interval * 10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #e0e0e0;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(self.progress)

        self.setLayout(main_layout)

        # Timer for auto-refresh & progress animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_refresh)
        self.timer.start(100)

    # ----------------- Add videos -----------------
    def add_videos(self):
        links = [link.strip() for link in self.link_input.text().split(",") if link.strip()]
        for link in links:
            if "youtube" in link or "youtu.be" in link:
                card = VideoCard("YouTube", "youtube_logo.png", link, parent_widget=self)
            elif "tiktok" in link:
                card = VideoCard("TikTok", "tiktok_logo.png", link, parent_widget=self)
            else:
                continue
            self.video_cards.insert(0, card)  # Add new videos at the top
            self.cards_layout.insertWidget(0, card)
        self.fetch_all_stats()
        self.link_input.clear()

    # ----------------- Fetch stats -----------------
    def fetch_all_stats(self):
        for card in self.video_cards:
            title, views, likes = self.fetch_stats(card.url, card.platform)
            card.update_stats(title, views, likes)

    def normalize_youtube(self, url):
        if "youtube.com/shorts/" in url:
            vid = url.split("/")[-1].split("?")[0]
            return f"https://www.youtube.com/watch?v={vid}"
        elif "youtu.be/" in url:
            vid = url.split("/")[-1].split("?")[0]
            return f"https://www.youtube.com/watch?v={vid}"
        elif "watch?v=" in url:
            vid = url.split("watch?v=")[-1].split("&")[0]
            return f"https://www.youtube.com/watch?v={vid}"
        return url

    def normalize_tiktok(self, url):
        return url.split("?")[0]

    def fetch_stats(self, url, platform=None):
        try:
            if platform.lower() == "youtube":
                url = self.normalize_youtube(url)
            else:
                url = self.normalize_tiktok(url)
            ydl_opts = {"quiet": True, "skip_download": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            views = info.get("view_count") or 0
            likes = info.get("like_count") or 0
            title = info.get("title", "Unknown Title")
            return title, views, likes
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return "Error", 0, 0

    # ----------------- Auto-refresh -----------------
    def update_refresh(self):
        self.timer_count += 1
        self.progress.setValue(self.timer_count)
        ratio = self.timer_count / (self.refresh_interval * 10)
        r = int(0 + ratio * 0)
        g = int(120 + ratio * 50)
        b = int(215 + ratio * 40)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #e0e0e0;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: rgb({r},{g},{b});
                border-radius: 5px;
            }}
        """)
        if self.timer_count >= self.refresh_interval * 10:
            self.timer_count = 0
            self.progress.reset()
            self.fetch_all_stats()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SocialStatsWidget()
    window.setWindowTitle("Social Media Stats")
    window.resize(700, 600)
    window.show()
    sys.exit(app.exec_())
