import os

token = os.environ['TOKEN']
channelName = "@chgkgame"
creator = 287002169
admins =[287002169]
checkLater = 1
cacheSize = 100
adminInstructions = "Введите команду:\n/publishnow - опубликовать сейчас\n/publishlater - добавить в очередь на публикацию\n/reserve - узнать сколько в очереди на публикацию"
userInstructions = "Введите команду:\n/send - отправить вопрос для публикации в канале\n/feedback - отправить вопрос, жалобу, предложение"
publishNowInstruction = "Отправьте вопрос в формате \"Вопрос | Ответ\" или \"Вопрос | Ответ | От кого\" и он будет опубликован сейчас"
publishLaterInstruction = "Отправьте вопрос в формате \"Вопрос | Ответ\" или \"Вопрос | Ответ | От кого\" и он будет добавлен в очередь на публикацию"
sendInstruction = "Отправьте текст в формате \"Вопрос | Ответ\", либо фото или видео с подписью в формате \"Вопрос | Ответ\""
feedbackInstruction = "Отправьте вопрос, предложение или замечание"
thanksPublishNow = "Вопрос отправлен в канал! Спасибо!"
thanksPublishLater = "Вопрос добавлен в очередь на публикацию! Спасибо!"
thanksSend = "Вопрос отправлен на модерацию, спасибо!"
thanksFeedback = "Спасибо за обратную связь! Ожидайте ответа от администраторов канала!"
tooLongAnswer = "Слишком длинный ответ, сократите его до 200 символов"
wrongText = "Неправильный формат. Отправьте повторно, используя формат \"Вопрос | Ответ\" или \"Вопрос | Ответ | От кого\""
wrongCaption = "Неправильный формат подписи. Отправьте повторно, используя формат \"Вопрос | Ответ\" или \"Вопрос | Ответ | От кого\""
wrongType = "Неправильный тип сообщения. Отправьте текстовое сообщение, либо фото или видео с подписью"
cancelBanner = "Пока! Чтобы начать, введите команду /start"