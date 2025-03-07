
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedwidget, Qwidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy 
from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer 
from dotenv import dotenv_values
import sys 
import os
env_vars= dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = TempDirPath = rf" {current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

def AnswerModifier(Answer):
	lines = Answer.split('\n')
	non_empty_lines = [line for line in lines if line.strip()]
	modified_answer = '\n'.join(non_empty_lines)
	return modified_answer

def QueryModifier(Query):
	new_query = Query.lower().strip()
	query_words = new_query.split()
	question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
	
	if any(word in new_query for word in question_words):
		pass
	else:
		if query_words[-1][-1] in ['.', '?', '!']:
			new_query = new_query[:-1]
		new_query += "?"
	
	return new_query.capitalize()
