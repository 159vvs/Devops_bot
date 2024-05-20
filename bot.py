import logging
import re
import psycopg2
import paramiko
import os

from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Подключаем логирование
logging.basicConfig(filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_ssh_command(host, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read() + stderr.read()
        data = str(output).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        return data
    finally:
        ssh.close()


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_number'


def find_phone_number(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий(или нет) номера телефонов
    PhoneRegex = re.compile(r'(\+7|8)( \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})') # формат 8 (000) 000-00-00
    PhoneList = [match.group() for match in PhoneRegex.finditer(user_input)]  # Ищем номера телефонов
    if not PhoneList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Номера телефонов не найдены')
        return ConversationHandler.END  # Завершаем выполнение функции
    phone_numbers = '\n'.join(PhoneList)  # Записываем найденные номера телефонов
    context.user_data['phone_numbers_to_save'] = PhoneList
    update.message.reply_text(f'Найдены следующие номера телефонов:\n\n{phone_numbers}\n\nХотите сохранить их в базу данных? (да/нет)')
    return 'confirmPhoneSave'


def confirmEmailSave(update: Update, context):
    user_response = update.message.text.lower()
    if user_response.startswith('да'):
        # Получаем сохраненные в контексте email-адреса и сохраняем их в базе данных
        emails_to_save = context.user_data['emails_to_save']
        success, message = saveEmailsToDB(emails_to_save)
        if success:
            update.message.reply_text(message)
        else:
            update.message.reply_text(message)
    return ConversationHandler.END


def confirmPhoneSave(update: Update, context):
    user_response = update.message.text.lower()
    if user_response.startswith('да'):
        # Получаем сохраненные в контексте номера телефонов и сохраняем их в базе данных
        phone_numbers_to_save = context.user_data['phone_numbers_to_save']
        success, message = savePhoneNumbersToDB(phone_numbers_to_save)
        if success:
            update.message.reply_text(message)
        else:
            update.message.reply_text(message)
    return ConversationHandler.END


def savePhoneNumbersToDB(phone_numbers):
    try:
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_DATABASE")

        # Формируем строку с номерами телефонов для вставки в запрос
        phone_numbers_str = ', '.join([f"('{phone_number}')" for phone_number in phone_numbers])
        # Формируем SQL-запрос для вставки номеров телефонов
        query = f"INSERT INTO phones (phone_number) VALUES {phone_numbers_str}"
        # Добавим отладочный вывод для проверки SQL-запроса
        print("DEBUG: SQL query:", query)
        # Выполняем запрос
        psql_insert_command(database, username, password, host, port, query)
        return True, "Номера телефонов успешно сохранены в базу данных"
    except Exception as e:
        return False, f"Ошибка при сохранении номеров телефонов в базу данных: {e}"


def findEmailsCommand(update: Update, context):
    update.message.reply_text('Введите текст для Email адресов: ')
    return 'find_email'


def find_email(update: Update, context):
    user_input = update.message.text  # Получаем текст, содержащий(или нет) email-адреса

    EmailRegex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    EmailList = [match.group() for match in EmailRegex.finditer(user_input)]  # Ищем email-адреса

    if not EmailList:  # Обрабатываем случай, когда email-адресов нет
        update.message.reply_text('Email адреса не найдены')
        return ConversationHandler.END  # Завершаем выполнение функции

    emails = '\n'.join(EmailList)  # Записываем найденные email-адреса
    context.user_data['emails_to_save'] = EmailList

    update.message.reply_text(f'Найдены следующие email адреса:\n\n{emails}\n\nХотите сохранить их в базу данных? (да/нет)')
    return 'confirmEmailSave'

def saveEmailsToDB(emails):
    try:
        username = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_DATABASE")

        # Формируем строку с email-адресами для вставки в запрос
        emails_str = ', '.join([f"('{email}')" for email in emails])

        # Формируем SQL-запрос для вставки email-адресов
        query = f"INSERT INTO emails (email) VALUES {emails_str}"

        # Выполняем запрос
        psql_insert_command(database, username, password, host, port, query)

        return True, "Emails успешно сохранены в базу данных"
    except Exception as e:
        return False, f"Ошибка при сохранении email-адресов в базу данных: {e}"

def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль: ')
    return 'verify_password'


def verify_password(update: Update, context):
    user_input = update.message.text

    PasswordRegex = re.compile(r'(?=.*[0-9]){1,}(?=.*[!@#$%^&*()]){1,}(?=.*[a-zа-я]){1,}(?=.*[A-ZА-Я]){1,}[0-9a-zA-Zа-яА-Я!@#$%^&*()]{8,}')

    PasswordList = [match.group() for match in PasswordRegex.finditer(user_input)]

    if not PasswordList:
        update.message.reply_text('Пароль простой')
        return ConversationHandler.END
    else:
        update.message.reply_text('Пароль сложный')
        return ConversationHandler.END

def execute_psql_command(dbname, user, password, host, port, command):
    connection = None
    print(dbname)
    print(user)
    print(password)
    print(host)
    print(port)
    try:
        connection = psycopg2.connect(user=user,
                                      password=password,
                                      host=host,
                                      port=port,
                                      database=dbname)
        cursor = connection.cursor()
        cursor.execute(command)
        data = cursor.fetchall()
        text = '\n\n'.join(['. '.join(map(str, x)) for x in data])
        return str(text)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def psql_insert_command(dbname, user, password, host, port, command):
    try:
        # Выполнение команды
        connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
        cursor.close()
        connection.close()
        return True, "Команда успешно выполнена"
    except Exception as e:
        return False, f"Ошибка выполнения команды: {e}"

def handle_ssh_command(update: Update, context, command_name: str, ssh_command: str, char_limit: int = 3900):
    # Параметры для SSH подключения
    host = os.getenv("RM_HOST")
    username = os.getenv("RM_USER")
    password = os.getenv("RM_PASSWORD")

    # Выполнение команды через SSH
    output = execute_ssh_command(host, username, password, ssh_command)

    if len(output) > char_limit:
        output = output[:char_limit] + '...'

    # Отправка результата обратно пользователю в Telegram
    update.message.reply_text(f"Результат выполнения команды:\n{output}")

def handle_psql_command(update: Update, context, command_name: str, psql_command: str):
    # Параметры для SSH подключения
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_DATABASE")

    # Выполнение команды через SSH
    output = execute_psql_command(database, username, password, host, port, psql_command)

    # Отправка результата обратно пользователю в Telegram
    update.message.reply_text(f"Результат выполнения команды {command_name}:\n{output}")

def get_release(update: Update, context):
    handle_ssh_command(update, context, "/get_release", "lsb_release -a")


def get_uname(update: Update, context):
    handle_ssh_command(update, context, "/get_uname", "uname -a")


def get_uptime(update: Update, context):
    handle_ssh_command(update, context, "/get_uptime", "uptime")


def get_df(update: Update, context):
    handle_ssh_command(update, context, "/get_df", "df")


def get_free(update: Update, context):
    handle_ssh_command(update, context, "/get_free", "free")


def get_mpstat(update: Update, context):
    handle_ssh_command(update, context, "/get_mpstat", "mpstat")


def get_w(update: Update, context):
    handle_ssh_command(update, context, "/get_w", "w")


def get_auths(update: Update, context):
    handle_ssh_command(update, context, "/get_auths", "last -n 10")


def get_critical(update: Update, context):
    handle_ssh_command(update, context, "/get_critical", "journalctl -p crit -n 5")


def get_ps(update: Update, context):
    handle_ssh_command(update, context, "/get_ps", "ps")


def get_ss(update: Update, context):
    handle_ssh_command(update, context, "/get_ss", "ss -n | head -10")


def get_apt_list(update: Update, context):
    # Проверяем, было ли предоставлено имя пакета в аргументах команды
    if context.args:
        package_name = context.args[0]
        handle_ssh_command(update, context, f"/get_apt_list {package_name}", f"apt show {package_name}")
    else:
        handle_ssh_command(update, context, "/get_apt_list", "apt list | head -10")


def get_services(update: Update, context):
    handle_ssh_command(update, context, "/get_services", "systemctl list-units --type=service | head -10")


def get_repl_logs(update: Update, context):
    password = os.getenv("RM_PASSWORD")
    handle_ssh_command(update, context, "/get_repl_logs", f"echo {password} | sudo -S docker exec bot sh -c \"cat /var/log/postgresql/postgres.log | grep replication\"")

def get_emails(update: Update, context):
    handle_psql_command(update, context, "/get_emails", "SELECT * FROM emails;")


def get_phone_numbers(update: Update, context):
    handle_psql_command(update, context, "/get_phone_numbers", "SELECT * FROM phones;")


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            'confirmPhoneSave': [MessageHandler(Filters.text & ~Filters.command, confirmPhoneSave)],
        },
        fallbacks=[]
    )

    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailsCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'confirmEmailSave': [MessageHandler(Filters.text & ~Filters.command, confirmEmailSave)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))


    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
