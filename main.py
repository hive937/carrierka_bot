import os
from dotenv import load_dotenv
import threading

import openai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters

AGE_QUESTION, UNIVERSITY_QUESTION, SPECIALTY_QUESTION, SKILLS_QUESTION, SPHERE_QUESTION, = range(5)

load_dotenv()

def start(update: Update, context):
    reply_keyboard = [['15-20 лет', '20-25 лет'], ['25 и больше']]
    update.message.reply_text(
        '👋 Привет! Я Карьерка - бот, который поможет тебе сгенерировать вспомогательные шаги для построения своей собственной карьерной стратегии.\n'
        '\n❓ Ответь на первый вопрос - сколько тебе лет?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return AGE_QUESTION


def age_question(update: Update, context):
    age = update.message.text
    update.message.reply_text('Отлично!\n\n❓ Ты обучаешься в университете?', reply_markup=ReplyKeyboardMarkup([['Да', 'Нет']], one_time_keyboard=True))
    context.user_data['age'] = age
    return UNIVERSITY_QUESTION


def university_question(update: Update, context):
    university = update.message.text
    if university == 'Да':
        update.message.reply_text('❓ Какая у тебя специальность?')
        return SPECIALTY_QUESTION
    else:
        update.message.reply_text('❓ Какими навыками ты владеешь?')
        return SKILLS_QUESTION


def specialty_question(update: Update, context):
    specialty = update.message.text
    update.message.reply_text('❓ Какими навыками ты владеешь?')
    context.user_data['specialty'] = specialty
    return SKILLS_QUESTION


def skills_question(update: Update, context):
    skills = update.message.text
    context.user_data['skills'] = skills
    update.message.reply_text('❓ В какой сфере ты хотел бы развиваться дальше?')
    return SPHERE_QUESTION


def sphere_question(update: Update, context):
    sphere = update.message.text
    context.user_data['sphere'] = sphere
    update.message.reply_text('🤍 Спасибо за ответы! \n Твоя стратегия генерируется...')

    threading.Thread(target=generate_strategy, args=(update, context)).start()
    return ConversationHandler.END


def generate_strategy(update: Update, context):
    openai.api_key = os.environ['API_TOKEN']
    model = 'gpt-3.5-turbo'
    prompt = f'Сгенерируй стратегию карьерного развития, если: мне {context.user_data["age"]} лет, я хочу развиваться в сфере {context.user_data["sphere"]} и у меня есть такие навыки, как {context.user_data["skills"]}'
    completion = openai.ChatCompletion.create(model=model,
                                              messages=[
                                                  {'role': 'user', 'content': prompt}
                                              ],
                                              temperature=0,
                                              max_tokens=2000)
    update.message.reply_text(f'Ниже представлены определенные шаги для выполнения / моменты, на которые тебе стоит обратить внимание:\n\n' + completion.choices[0]['message']['content'])
    update.message.reply_text('☑ Данные шаги помогут тебе понять, как развиваться в области, которая тебе интересна. '
                              'Надеюсь, я был полезен для тебя!')


def cancel(update: Update, context):
    update.message.reply_text('Ок, давай поговорим в другой раз.')
    return ConversationHandler.END


def main():
    updater = Updater(token=os.environ['BOT_TOKEN'])
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGE_QUESTION: [MessageHandler(Filters.regex('^(15-20 лет|20-25 лет|25 и больше)$'), age_question)],
            UNIVERSITY_QUESTION: [MessageHandler(Filters.regex('^(Да|Нет)$'), university_question)],
            SPECIALTY_QUESTION: [MessageHandler(Filters.text, specialty_question)],
            SKILLS_QUESTION: [MessageHandler(Filters.text, skills_question)],
            SPHERE_QUESTION: [MessageHandler(Filters.text, sphere_question)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()
