import config
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, Job
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
import logging
import sqlite3
import datetime
from random import randint
import collections
import re

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

ADMINWAIT, USERWAIT, PUBLISHNOW, PUBLISHLATER, SEND, FEEDBACK = range(6)

order = 0

cache = collections.OrderedDict()

def sendAnswer(bot, update):
	global cache
	query = update.callback_query
	number = query.data

	answer = cache.get(number)
	if answer == None:
		conn = sqlite3.connect('questions')
		cursor = conn.cursor()
		answer = str(cursor.execute("SELECT answer FROM questions WHERE id = ?", (number,)).fetchone()[0])
		conn.close()

	if len(answer) < 28:
		bot.answerCallbackQuery(callback_query_id=query.id, text=answer, show_alert=False, cache_time=300)
	else:
		bot.answerCallbackQuery(callback_query_id=query.id, text=answer, show_alert=True, cache_time=300)


def start(bot, update):
	if update.message.from_user.id in config.admins:
		bot.sendMessage(chat_id=update.message.chat_id, text=config.adminInstructions)
		return ADMINWAIT
	else:
		bot.sendMessage(chat_id=update.message.chat_id, text=config.userInstructions)
		return USERWAIT


def publishNowCommand(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=config.publishNowInstruction)
	return PUBLISHNOW


def publishLaterCommand(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=config.publishLaterInstruction)
	return PUBLISHLATER


def reserveCommand(bot, update):
	conn = sqlite3.connect('later')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM questions")
	queue = cursor.fetchall()
	number = len(queue)
	conn.commit()
	conn.close()
	bot.sendMessage(chat_id=update.message.chat_id, text="Вопросов в очереди: " + str(number))
	return ADMINWAIT


def voteCommand(bot, update):

	return VOTE


def sendCommand(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=config.sendInstruction)
	return SEND


def feedbackCommand(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=config.feedbackInstruction)
	return FEEDBACK


def insertIntoDb(name, question, answer, admin, user, file_id, kind):
	conn = sqlite3.connect(name)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO questions VALUES (?,?,?,?,?,?,?)", (None, question, answer, admin, user, file_id, kind))
	number = str(cursor.lastrowid)
	conn.commit()
	conn.close()
	return number


def publish(bot, chat_id, question, answer, admin, user, file_id, kind):
	global cache
	number = insertIntoDb('questions', question, answer, admin, user, file_id, kind)

	cache[number] = answer
	if len(cache) > config.cacheSize:
		cache.popitem(last=False)
			
	buttonList = [[InlineKeyboardButton("Ответ", callback_data=number)]]
	kb_markup = InlineKeyboardMarkup(buttonList)
	if kind == 1:
		urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', question)
		if len(urls) == 0:
			bot.sendMessage(chat_id=config.channelName, text=question, reply_markup=kb_markup)
		else:
			for url in urls:
				question = question.replace(url,'')
			bot.sendMessage(chat_id=config.channelName, text='<a href="'+ urls[0] + '">&#8203;</a>' + question.strip(), parse_mode=ParseMode.HTML, reply_markup=kb_markup)
	elif kind == 2:
		bot.sendPhoto(chat_id=config.channelName, photo=file_id, caption=question, reply_markup=kb_markup)
	elif kind == 3:
		bot.sendVideo(chat_id=config.channelName, video=file_id, caption=question, reply_markup=kb_markup)
	if chat_id is not None:
		bot.sendMessage(chat_id=chat_id, text=config.thanksPublishNow + " " + config.adminInstructions)


def publishNow(bot, update):
	chat_id = update.message.chat_id

	if update.message.text is not None: #ЧИСТЫЙ ТЕКСТ
		record = update.message.text.split("|")

		if len(record) != 2 and len(record) != 3: 
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongText)
			return PUBLISHNOW

		else:
			question = record[0].strip()
			answer = record[1].strip()
			admin_from = str(update.message.from_user)

			if len(answer) > 200:
				bot.sendMessage(chat_id=update.message.chat_id, text=config.tooLongAnswer)
				return PUBLISHNOW

			else:
				if len(record) == 2:
					publish(bot, chat_id, question, answer, admin_from, admin_from, None, 1)
					return ADMINWAIT

				elif len(record) == 3:
					user_from = record[2].strip()
					publish(bot, chat_id, question, answer, admin_from, user_from, None, 1)
					return ADMINWAIT


	elif update.message.photo is not None and update.message.video is None and update.message.caption is not None: #С КАРТИНКОЙ
		record = update.message.caption.split("|")

		if len(record) != 2 and len(record) != 3: 
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongCaption)
			return PUBLISHNOW

		else:
			question = record[0].strip()
			answer = record[1].strip()
			admin_from = str(update.message.from_user)
			file_id = update.message.photo[0].file_id

			if len(record) == 2:
				publish(bot, chat_id, question, answer, admin_from, admin_from, file_id, 2)
				return ADMINWAIT

			elif len(record) == 3:
				user_from = record[2].strip()
				publish(bot, chat_id, question, answer, admin_from, user_from, file_id, 2)
				return ADMINWAIT


	elif update.message.video is not None and update.message.caption is not None: #С ВИДЕО
		record = update.message.caption.split("|")

		if len(record) != 2 and len(record) != 3: 
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongCaption)
			return PUBLISHNOW

		else:
			question = record[0].strip()
			answer = record[1].strip()
			admin_from = str(update.message.from_user)
			file_id = update.message.video.file_id

			if len(record) == 2:
				publish(bot, chat_id, question, answer, admin_from, admin_from, file_id, 3)
				return ADMINWAIT

			elif len(record) == 3:
				user_from = record[2].strip()
				publish(bot, chat_id, question, answer, admin_from, user_from, file_id, 3)
				return ADMINWAIT

	else:
		bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongType)
		return PUBLISHNOW


def publishLater(bot, update):
	chat_id = update.message.chat_id

	if update.message.text is not None: #ЧИСТЫЙ ТЕКСТ
		record = update.message.text.split("|")

		if len(record) != 2 and len(record) != 3: 
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongText)
			return PUBLISHLATER

		else:
			question = record[0].strip()
			answer = record[1].strip()
			admin_from = str(update.message.from_user)

			if len(answer) > 200:
				bot.sendMessage(chat_id=update.message.chat_id, text=config.tooLongAnswer)
				return PUBLISHLATER

			else:
				if len(record) == 2:
					number = insertIntoDb('later', question, answer, admin_from, admin_from, None, 1)
					bot.sendMessage(chat_id=update.message.chat_id, text=config.thanksPublishLater + " " + config.adminInstructions)
					return ADMINWAIT

				elif len(record) == 3:
					user_from = record[2].strip()
					number = insertIntoDb('later', question, answer, admin_from, user_from, None, 1)				
					bot.sendMessage(chat_id=chat_id, text=config.thanksPublishLater + " " + config.adminInstructions)
					return ADMINWAIT


	elif update.message.photo is not None and update.message.video is None and update.message.caption is not None: #С КАРТИНКОЙ
		record = update.message.caption.split("|")

		if len(record) != 2 and len(record) != 3: 
			bot.sendMessage(chat_id=chat_id, text=config.wrongCaption)
			return PUBLISHLATER

		else:
			question = record[0].strip()
			answer = record[1].strip()
			admin_from = str(update.message.from_user)
			file_id = update.message.photo[0].file_id

			if len(record) == 2:
				number = insertIntoDb('later', question, answer, admin_from, admin_from, file_id, 2)
				bot.sendMessage(chat_id=chat_id, text=config.thanksPublishLater + " " + config.adminInstructions)
				return ADMINWAIT

			elif len(record) == 3:
				user_from = record[2].strip()
				number = insertIntoDb('later', question, answer, admin_from, user_from, file_id, 2)
				bot.sendMessage(chat_id=chat_id, text=config.thanksPublishLater + " " + config.adminInstructions)
				return ADMINWAIT


	elif update.message.video is not None and update.message.caption is not None: #С ВИДЕО
		record = update.message.caption.split("|")

		if len(record) != 2 and len(record) != 3: 
			bot.sendMessage(chat_id=chat_id, text=config.wrongCaption)
			return PUBLISHLATER

		else:
			question = record[0].strip()
			answer = record[1].strip()
			admin_from = str(update.message.from_user)
			file_id = update.message.video.file_id

			if len(record) == 2:
				number = insertIntoDb('later', question, answer, admin_from, admin_from, file_id, 3)
				bot.sendMessage(chat_id=chat_id, text=config.thanksPublishLater + " " + config.adminInstructions)
				return ADMINWAIT

			elif len(record) == 3:
				user_from = record[2].strip()
				number = insertIntoDb('later', question, answer, admin_from, user_from, file_id, 3)
				bot.sendMessage(chat_id=chat_id, text=config.thanksPublishLater + " " + config.adminInstructions)
				return ADMINWAIT

	else:
		bot.sendMessage(chat_id=chat_id, text=config.wrongType)
		return PUBLISHLATER


def sendGo(bot, chat_id, question, answer, admin, user, file_id, kind, user_id):
	insertIntoDb('proposed', question, answer, admin, user, file_id, kind)
	bot.sendMessage(chat_id=admin, text="Вопрос на рассмотрение:")
	if kind == 1:
		bot.sendMessage(chat_id=admin, text=question + "|" + answer + "|" + user)
	elif kind == 2:
		bot.sendPhoto(chat_id=admin, photo=file_id, caption=question + "|" + answer + "|" + user_id)
	elif kind == 3:
		bot.sendVideo(chat_id=admin, video=file_id, caption=question + "|" + answer + "|" + user_id)
	bot.sendMessage(chat_id=chat_id, text=config.thanksSend + " " + config.userInstructions)


def send(bot, update):
	global order
	chat_id = update.message.chat_id
	user_id = str(update.message.from_user.id)

	if update.message.text is not None: #ЧИСТЫЙ ТЕКСТ
		record = update.message.text.split("|")

		if len(record) == 2:
			question = record[0].strip()
			answer = record[1].strip()
			user_from = str(update.message.from_user)
			order = (order + 1) % len(config.admins)
			admin_to = config.admins[order]

			sendGo(bot, chat_id, question, answer, admin_to, user_from, None, 1, user_id)
			return USERWAIT

		else:
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongText)
			return SEND

	elif update.message.photo is not None and update.message.video is None and update.message.caption is not None: #С КАРТИНКОЙ
		record = update.message.caption.split("|")
		if len(record) == 2:
			question = record[0].strip()
			answer = record[1].strip()
			user_from = str(update.message.from_user)
			order = (order + 1) % len(config.admins)
			admin_to = config.admins[order]
			file_id = update.message.photo[0].file_id

			sendGo(bot, chat_id, question, answer, admin_to, user_from, file_id, 2, user_id)
			return USERWAIT

		else:
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongCaption)
			return SEND

	elif update.message.video is not None and update.message.caption is not None: #С ВИДЕО
		record = update.message.caption.split("|")
		if len(record) == 2:
			question = record[0].strip()
			answer = record[1].strip()
			user_from = str(update.message.from_user)
			order = (order + 1) % len(config.admins)
			admin_to = config.admins[order]
			file_id = update.message.video.file_id

			sendGo(bot, chat_id, question, answer, admin_to, user_from, file_id, 3, user_id)
			return USERWAIT

		else:
			bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongCaption)		
			return SEND	

	else:
		bot.sendMessage(chat_id=update.message.chat_id, text=config.wrongType)
	return SEND


def feedback(bot, update):
	bot.sendMessage(chat_id=config.creator, text="Обратная связь:")
	bot.forwardMessage(chat_id=config.creator, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
	bot.sendMessage(chat_id=update.message.chat_id, text=config.thanksFeedback + " " + config.userInstructions)
	return USERWAIT


def cancel(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=config.cancelBanner)
    return ConversationHandler.END


def getInterval():
	interval = 0
	weekDay = datetime.datetime.now().weekday()
	hour = datetime.datetime.now().hour
	minute = datetime.datetime.now().minute

	if config.checkLater == 1:
		if weekDay < 5:
			if hour < 9:
				interval += (9 - hour)*3600 + randint(0, 30)*60
				interval -= minute*60
			elif hour > 18:
				interval += (24 - hour + 9)*3600 + randint(0, 30)*60
				if weekDay == 4:
					interval += 48*3600
				interval -= minute*60
			else:
				interval += randint(80, 150)*60
		elif weekDay == 5:
			interval += (57 - hour)*3600 + randint(0, 30)*60
			interval -= minute*60
		elif weekDay == 6:
			interval += (33 - hour)*3600 + randint(0, 30)*60
			interval -= minute*60

	elif config.checkLater == 2:
		if weekDay < 5:
			if hour < 9:
				interval += (9 - hour)*3600 + randint(0, 30)*60
				interval -= minute*60
			elif hour > 13:
				interval += (24 - hour + 9)*3600 + randint(0, 30)*60
				if weekDay == 4:
					interval += 48*3600
				interval -= minute*60
			else:
				interval += randint(210, 240)*60
		elif weekDay == 5:
			interval += (57 - hour)*3600 + randint(0, 30)*60
			interval -= minute*60
		elif weekDay == 6:
			interval += (33 - hour)*3600 + randint(0, 30)*60
			interval -= minute*60

	print(str(datetime.datetime.now()) + " interval: " + str(interval))
	return interval


def checkLater(bot, job):
	conn = sqlite3.connect('later')
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM questions")
	queue = cursor.fetchall()
	number = len(queue)
	if number > 0:
		publish(bot, None, queue[0][1], queue[0][2], queue[0][3], queue[0][4], queue[0][5], queue[0][6])
		cursor.execute("DELETE FROM questions WHERE id=?", (queue[0][0],))
	conn.commit()
	conn.close()
	job.interval = getInterval()


def cacheInitialize():
	global cache
	conn = sqlite3.connect('questions')
	cursor = conn.cursor()
	lastRows = cursor.execute("SELECT * FROM (SELECT id, answer FROM questions ORDER BY id DESC LIMIT ?) sub ORDER BY id ASC", (config.cacheSize,)).fetchall()
	conn.close()
	for t in lastRows:
		cache[str(t[0])] = t[1]

#def error(bot, update, error):
#    logger.warn('Update "%s" caused error "%s"' % (update, error))
#    if update.message.from_user.id in config.admins:
#    	return ADMINWAIT
#    else:
#    	return USERWAIT

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

def myServer():
	httpd = HTTPServer(('0.0.0.0', 80), SimpleHTTPRequestHandler)
	httpd.serve_forever()

def main():
	threading.Thread(target=myServer).start()

	updater = Updater(token=config.token)
	dispatcher = updater.dispatcher

	sendAnswer_handler = CallbackQueryHandler(sendAnswer)

	startCommand_handler = CommandHandler('start', start)
	start_handler = MessageHandler(Filters.all, start)

	publishNowCommand_handler = CommandHandler('publishnow', publishNowCommand)
	publishLaterCommand_handler = CommandHandler('publishlater', publishLaterCommand)
	reserveCommand_handler = CommandHandler('reserve', reserveCommand)
	publishNow_handler = MessageHandler(Filters.all, publishNow)
	publishLater_handler = MessageHandler(Filters.all, publishLater)

	sendCommand_handler = CommandHandler('send', sendCommand)
	feedbackCommand_handler = CommandHandler('feedback', feedbackCommand)
	send_handler = MessageHandler(Filters.all, send)
	feedback_handler = MessageHandler(Filters.all, feedback)

	cancelCommand_handler = CommandHandler('cancel', cancel)

	conv_handler = ConversationHandler(
        entry_points=[startCommand_handler, start_handler],
        states={
        	ADMINWAIT: [publishNowCommand_handler, publishLaterCommand_handler, reserveCommand_handler, start_handler],

        	PUBLISHNOW: [publishNow_handler],

        	PUBLISHLATER: [publishLater_handler],

        	USERWAIT: [sendCommand_handler, feedbackCommand_handler, start_handler], 

        	SEND: [send_handler, feedbackCommand_handler],

        	FEEDBACK: [feedback_handler]
        },
        fallbacks=[cancelCommand_handler]
	)
	
	dispatcher.add_handler(sendAnswer_handler)
	dispatcher.add_handler(conv_handler)
	#dispatcher.add_error_handler(error)

	cacheInitialize()

	if config.checkLater != 0:
		jobQueue = updater.job_queue
		jobCheckLater = Job(checkLater, getInterval())
		jobQueue.put(jobCheckLater)
	
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
    main()