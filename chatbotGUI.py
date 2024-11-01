import openai
from speech_to_text import speech_to_text
from text_to_speech import text_to_speech

"""本コードは、GUIを使用してチャットボットと対話するためのもの
    Github copilotの助けを借りたりするため、コメントが英語であったり日本語であったりするが、一番重要なことは日本語でコメントアウトしてある
    PyQt5を使用しているため、pip install PyQt5を行う必要がある"""

# OpenAIのAPIキーを設定
openai.api_key = ""

# プロンプトの準備
template = """あなたはどんな文章も指定された方言や敬語に正すAIです、入力された文章を関西弁、もしくは敬語に変換したものを返してください
制約:
- 入出力は日本語を用います
- 入力された文章を適切な形に変換した状態でオウム返しをしてください
- 最初に関西弁に変換するか、敬語に変換するかの選択肢を提供してください
- 敬語に変換できない語句が入力された場合は、その語句をそのまま返してください
- 会話をするのではなく入力された文章を変換するのみが目的です
- 「リセット」と入力されたら、再度どのような文章に変換するかの選択を提供してください"""

# メッセージの初期化
messages = [{"role": "system", "content": template}]

# Import necessary modules
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLineEdit,
    QListView,
    QMessageBox,
    QVBoxLayout,
    QStyledItemDelegate,
)
from PyQt5.QtCore import (
    Qt,
    QAbstractListModel,
    QMargins,
    QSize,
    QRect,
    QPoint,
    QThread,
    pyqtSignal,
)
from PyQt5.QtGui import QIcon, QColor, QImage, QPolygon


style_sheet = """ 
    QPushButton {
        background: #83E56C /* Green */
    }

    QListView {
        background: #FDF3DD
    }"""


class ChatLogModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self.chat_messages = []

    def rowCount(self, index):
        """chat_messagesの長さに基づいて、モデル内のアイテムの数を返す"""
        return len(self.chat_messages)

    def data(self, index, role=Qt.DisplayRole):
        """QAbstractListModel をサブクラス化するときに data() を含める必要がある。
        リストから項目を取得し、ロールで指定されたデータを返す。
        この場合、データはテキストとして表示される。"""
        if role == Qt.DisplayRole:
            return self.chat_messages[index.row()]

    def appendMessage(self, user_input, user_or_chatbot):
        """まず、新しいメッセージを chat_messages に追加する。
        これにより、モデル内の行とインデックスの数が更新され (rowCount())、さらに data() が更新される。"""
        self.chat_messages.append([user_input, user_or_chatbot])
        # Emit signal to indicate that the layout of items in the model has changed
        self.layoutChanged.emit()


# コードに直接関係ない装飾関係の関数
class DrawSpeechBubbleDelegate(QStyledItemDelegate):
    def __init__(self):
        super().__init__()
        self.image_offset = 5  # 画像の位置調整
        # 吹き出しの位置調整
        self.side_offset, self.top_offset = 40, 5
        self.tail_offset_x, self.tail_offset_y = 30, 0
        self.text_side_offset, self.text_top_offset = 50, 15

    def paint(self, painter, option, index):
        """paint()関数を再実装する。
        指定されたインデックス (行値) で描画される項目に対して、指定された QPainter (ペインター) と QStyleOptionViewItem (オプション) を使用してデリゲートをレンダリングする。
        """
        text, user_or_chatbot = index.model().data(index, Qt.DisplayRole)
        image, image_rect = (
            QImage(),
            QRect(),
        )  # Initialize objects for the user and chatbot icons
        color, bubble_margins = (
            QColor(),
            QMargins(),
        )  # Initialize objects for drawing speech bubbles
        tail_points = (
            QPolygon()
        )  # Initialize QPolygon object for drawing the tail on the speech bubbles

        # user_or_chatbot の値を使用して、表示する画像、ペンの色、ブラシを選択する。
        # スピーチバブルの余白と尻尾のポイントを設定。
        if user_or_chatbot == "chatbot":
            image.load("images/bot.png")
            image_rect = QRect(
                QPoint(
                    option.rect.left() + self.image_offset,
                    option.rect.center().y() - 12,
                ),
                QSize(24, 24),
            )
            color = QColor("#83E56C")
            bubble_margins = QMargins(
                self.side_offset, self.top_offset, self.side_offset, self.top_offset
            )
            tail_points = QPolygon(
                [
                    QPoint(
                        option.rect.x() + self.tail_offset_x, option.rect.center().y()
                    ),
                    QPoint(
                        option.rect.x() + self.side_offset, option.rect.center().y() - 5
                    ),
                    QPoint(
                        option.rect.x() + self.side_offset, option.rect.center().y() + 5
                    ),
                ]
            )
        elif user_or_chatbot == "user":
            image.load("images/user.png")
            image_rect = QRect(
                QPoint(
                    option.rect.right() - self.image_offset - 24,
                    option.rect.center().y() - 12,
                ),
                QSize(24, 24),
            )
            color = QColor("#38E0F9")
            bubble_margins = QMargins(
                self.side_offset, self.top_offset, self.side_offset, self.top_offset
            )
            tail_points = QPolygon(
                [
                    QPoint(
                        option.rect.right() - self.tail_offset_x,
                        option.rect.center().y(),
                    ),
                    QPoint(
                        option.rect.right() - self.side_offset,
                        option.rect.center().y() - 5,
                    ),
                    QPoint(
                        option.rect.right() - self.side_offset,
                        option.rect.center().y() + 5,
                    ),
                ]
            )

        # 吹き出しの隣に画像を描画
        painter.drawImage(image_rect, image)

        # draw the speech bubble and tail
        painter.setPen(color)
        painter.setBrush(color)
        # Remove the margins from the rectangle to shrink its size
        painter.drawRoundedRect(option.rect.marginsRemoved(bubble_margins), 5, 5)
        painter.drawPolygon(tail_points)

        # Draw the text in the speech bubble
        painter.setPen(QColor("#4A4C4B"))  # Reset pen color for the text
        text_margins = QMargins(
            self.text_side_offset,
            self.text_top_offset,
            self.text_side_offset,
            self.text_top_offset,
        )
        painter.drawText(
            option.rect.marginsRemoved(text_margins),
            Qt.AlignVCenter | Qt.TextWordWrap,
            text,
        )

    def sizeHint(self, option, index):
        """指定されたインデックスに表示される項目のサイズを把握するために再実装する。オプションを使用して、スタイル情報 (この場合は吹き出しの余白) を把握する。"""
        text, user_or_chatbot = index.model().data(index, Qt.DisplayRole)
        font_size = QApplication.fontMetrics()  # Calculate the size of the text
        text_margins = QMargins(
            self.text_side_offset,
            self.text_top_offset,
            self.text_side_offset,
            self.text_top_offset,
        )

        # Remove the margins, get the rectangle for the font, and add the margins back in
        rect = option.rect.marginsRemoved(text_margins)
        rect = font_size.boundingRect(rect, Qt.TextWordWrap, text)
        rect = rect.marginsAdded(text_margins)
        return rect.size()

    """このコードの一番重要な部分、APIにテキストを送信したり、受け取ったりする部分"""


class Chatbot(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()

    def initializeUI(self):
        """ウィンドウとその内容を初期化"""
        self.setMinimumSize(450, 600)
        self.setWindowTitle("Voice_chat_bot GUI")
        self.setWindowFlag(Qt.Window)

        self.chat_started = False

        self.setupWindow()
        self.show()

    def setupWindow(self):
        """メイン ウィンドウのウィジェットとモデル/ビュー インスタンスを設定"""
        self.chat_button = QPushButton(QIcon("images/chat.png"), "Start Chat")
        self.chat_button.setLayoutDirection(Qt.RightToLeft)
        self.chat_button.pressed.connect(self.chatButtonPressed)

        # Create the model for keeping track of new messages (data), the list view
        # for displaying the chat log, and the delegate for drawing the items in the list view
        self.model = ChatLogModel()
        self.chat_log_view = QListView()
        self.chat_log_view.setModel(self.model)

        message_delegate = DrawSpeechBubbleDelegate()
        self.chat_log_view.setItemDelegate(message_delegate)

        # Create the QLineEdit widget for entering text
        self.user_input_line = QLineEdit()
        self.user_input_line.setMinimumHeight(24)
        self.user_input_line.setPlaceholderText(
            "'Start Chat'を押して対話を開始してください..."
        )
        self.user_input_line.returnPressed.connect(self.enterTextMessage)

        # 上記の代わりに音声認識を行う
        # 音声認識ボタンを作成
        self.speech_button = QPushButton("音声認識")

        # 音声認識ボタンが押されたらspeechButtonPressedとenterUserMessageを呼び出す
        # self.speech_button.pressed.connect(self.speechButtonPressed)
        self.speech_button.pressed.connect(self.enterUserMessage)
        # 音声認識ボタンを配置

        main_v_box = QVBoxLayout()
        main_v_box.setContentsMargins(0, 2, 0, 10)
        main_v_box.addWidget(self.chat_button, Qt.AlignRight)
        main_v_box.setSpacing(10)
        main_v_box.addWidget(self.chat_log_view)
        main_v_box.addWidget(self.speech_button)
        main_v_box.addWidget(self.user_input_line)
        self.setLayout(main_v_box)

    def chatButtonPressed(self):
        """ユーザーがチャットを開始すると、chat_button の外観と状態が設定され、ユーザーはチャットを終了することもできる。"""
        button = self.sender()
        if button.text() == "Start Chat":
            self.chat_button.setText("End Chat")
            self.chat_button.setIcon(QIcon("images/end.png"))
            self.chat_button.setStyleSheet("background: #EC7161")  # Red
            self.chat_button.setDisabled(True)
            self.chat_started = True
        elif button.text() == "End Chat":
            self.endCurrentChat()

    # 音声認識ボタンを押したときのUIの変化
    def speechButtonPressed(self):
        """うまくいかなかったため、音声認識ボタンを押したときのUIの変化のみを行う"""
        button = self.sender()
        if button.text() == "音声認識":
            self.speech_button.setText("音声認識中")
            self.speech_button.setIcon(QIcon("images/end.png"))
            self.speech_button.setStyleSheet("background: #EC7161")  # Red
            self.speech_button.setDisabled(True)
            self.chat_started = True
        elif button.text() == "音声認識中":
            self.speech_button.setText("音声認識")
            self.chat_button.setIcon(QIcon("images/chat.png"))
            selif.chat_button.setStyleSheet("background: #83E56C")  # Green
            self.chat_button.setDisabled(False)

    # テキストを手動で入力する場合の関数
    def enterTextMessage(self):
        user_input = self.user_input_line.text()
        if user_input != "" and self.chat_started == True:
            self.model.appendMessage(user_input, "user")
            self.displayChatbotResponse(user_input)
            self.user_input_line.clear()

    def enterUserMessage(self):
        """音声認識を行い、入力された文章をチャットボットに送信する関数"""
        # 音声をテキストに変換
        user_message = speech_to_text()

        # テキストが空の場合は処理をスキップ
        if user_message == "":
            return

        # ターミナルに表示
        print("あなたのメッセージ: \n{}".format(user_message))

        user_input = user_message
        if user_input != "" and self.chat_started == True:
            self.model.appendMessage(user_input, "user")
            self.displayChatbotResponse(user_input)

    def displayChatbotResponse(self, user_input):
        """チャットボットからの応答を表示する関数、最後に音声に変換して再生する"""
        messages.append({"role": "user", "content": user_input})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
        bot_message = response["choices"][0]["message"]["content"]
        self.model.appendMessage(str(bot_message), "chatbot")
        # Uncomment to get the time it takes for the chatbot to respond
        # print(utils.get_response_time(self.chatbot))
        text_to_speech(bot_message)

    def endCurrentChat(self):
        """チャットを終了する関数、チャット履歴を削除する"""
        choice = QMessageBox.question(
            self,
            "End Chat",
            "The chat history will be deleted. 対話を終了しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if choice == QMessageBox.Yes:
            # Clearing the list will set the number of rows to 0 and clear the chat area
            self.model.chat_messages = []
            self.user_input_line.setPlaceholderText(
                "Press 'Start Chat' to begin chatting..."
            )
            self.chat_button.setText("Start Chat")
            self.chat_button.setIcon(QIcon("images/chat.png"))
            self.chat_button.setStyleSheet("background: #83E56C")  # Green
            self.chat_started = False
        else:
            self.model.appendMessage("I thought you were going to leave me.", "chatbot")

    def closeEvent(self, event):
        """チャットを終了する際、確認画面を表示する"""
        if self.chat_started:
            choice = QMessageBox.question(
                self,
                "Leave Chat?",
                "対話を終了しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if choice == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style_sheet)
    window = Chatbot()
    sys.exit(app.exec_())
