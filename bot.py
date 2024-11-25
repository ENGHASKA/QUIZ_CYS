import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Poll

# أدخل توكن البوت الخاص بك
BOT_TOKEN = "8141816032:AAGD3HKckToyPEP0kLIv62WHDecLggwHhRA"
bot = telebot.TeleBot(BOT_TOKEN)

# معرف القناة
CHANNEL_ID = "@HASKA_CYS"  # استبدل هذا بمعرف قناتك

# قائمة تخزين الأسئلة
questions = []

# البداية
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("📋 الطريقة العادية", callback_data="normal_mode"),
               InlineKeyboardButton("🌀 الطريقة الثانية", callback_data="second_mode"))
    bot.send_message(message.chat.id, "مرحبًا! 👋\nاختر الطريقة التي تريد استخدامها لإنشاء الاختبار:", reply_markup=markup)

# معالجة اختيار المستخدم من القائمة
@bot.callback_query_handler(func=lambda call: True)
def handle_menu(call):
    if call.data == "normal_mode":
        bot.send_message(call.message.chat.id, "🎯 اختر نوع السؤال:\n- 'صح أو خطأ' أو 'اختيارات متعددة'.")
        normal_mode(call.message)
    elif call.data == "second_mode":
        second_mode(call.message)
    elif call.data == "add_question":
        start_message(call.message)
    elif call.data == "finish_and_send":
        send_polls_to_channel(call.message)

# الطريقة العادية
def normal_mode(message):
    bot.send_message(message.chat.id, "⚡️ أدخل نوع السؤال (1️⃣: صح أو خطأ / 2️⃣: اختيارات متعددة):")
    bot.register_next_step_handler(message, process_question_type)

def process_question_type(message):
    question_type = message.text
    if question_type in ["1", "2"]:
        bot.send_message(message.chat.id, "💬 أدخل السؤال:")
        bot.register_next_step_handler(message, lambda msg: process_question(msg, question_type))
    else:
        bot.send_message(message.chat.id, "❌ نوع السؤال غير صحيح. أعد المحاولة.")
        normal_mode(message)

def process_question(message, question_type):
    question = message.text
    bot.send_message(message.chat.id, "🔢 أدخل الإجابات، كل إجابة في رسالة منفصلة. أرسل 'تم' عند الانتهاء:")
    options = []
    bot.register_next_step_handler(message, lambda msg: collect_options(msg, question_type, question, options))

def collect_options(message, question_type, question, options):
    if message.text.lower() == "تم":
        if len(options) >= 2:  # لا يقل عن إجابتين
            bot.send_message(message.chat.id, "✅ أدخل رقم الإجابة الصحيحة (1-{}):".format(len(options)))
            bot.register_next_step_handler(message, lambda msg: save_question(msg, question_type, question, options))
        else:
            bot.send_message(message.chat.id, "❌ يجب إدخال إجابتين على الأقل. أعد المحاولة.")
            process_question(message, question_type)
    else:
        options.append(message.text.strip())
        bot.register_next_step_handler(message, lambda msg: collect_options(msg, question_type, question, options))

def save_question(message, question_type, question, options):
    try:
        correct_answer = int(message.text.strip())
        if correct_answer < 1 or correct_answer > len(options):
            raise ValueError("رقم الإجابة خارج النطاق.")
        questions.append({
            "type": "multiple_choice" if question_type == "2" else "true_false",
            "question": question,
            "options": options,
            "correct_answer": correct_answer - 1  # لتحويل إلى الفهرس
        })
        bot.send_message(message.chat.id, "✅ تم إضافة السؤال بنجاح!")
        next_action(message)
    except ValueError as e:
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)}. أعد المحاولة.")
        bot.register_next_step_handler(message, lambda msg: save_question(msg, question_type, question, options))

# تأكيد أو إضافة أسئلة أخرى
def next_action(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("➕ إضافة سؤال", callback_data="add_question"),
               InlineKeyboardButton("📤 إنهاء وإرسال", callback_data="finish_and_send"))
    bot.send_message(message.chat.id, "ماذا تريد أن تفعل الآن؟", reply_markup=markup)

# الطريقة الثانية
def second_mode(message):
    bot.send_message(message.chat.id, 
                     "🌀 أدخل الأسئلة بالطريقة التالية:\n"
                     "🔹 ضع * قبل كل سؤال.\n"
                     "🔹 ضع + قبل كل خيار.\n"
                     "🔹 ضع = بجانب الإجابة الصحيحة.\n\n"
                     "📋 مثال:\n"
                     "*ما عاصمة السعودية؟\n"
                     "+الدمام\n"
                     "+الطائف\n"
                     "+الرياض=\n"
                     "+تبوك\n\n"
                     "📌 بعد إدخال الأسئلة، أرسل 'تم' للإنهاء.")
    bot.register_next_step_handler(message, process_custom_questions)

def process_custom_questions(message):
    user_input = message.text
    if user_input.lower() == "تم":
        if questions:
            bot.send_message(message.chat.id, "✅ تم إضافة الأسئلة بنجاح!")
            send_polls_to_channel(message)
        else:
            bot.send_message(message.chat.id, "⚠️ لم تقم بإضافة أي أسئلة. أعد المحاولة.")
            second_mode(message)
    else:
        try:
            parsed_questions = parse_custom_format(user_input)
            questions.extend(parsed_questions)
            bot.send_message(message.chat.id, "✅ الأسئلة تم تحليلها وإضافتها بنجاح! أرسل 'تم' لإنهاء.")
            bot.register_next_step_handler(message, process_custom_questions)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ خطأ في التنسيق: {str(e)}\nأعد المحاولة.")
            second_mode(message)

def parse_custom_format(input_text):
    lines = input_text.strip().split("\n")
    parsed_questions = []
    current_question = None
    options = []
    correct_option = None

    for line in lines:
        if line.startswith("*"):  # السؤال
            if current_question:  # حفظ السؤال السابق
                if correct_option is None:
                    raise ValueError("لم يتم تحديد الإجابة الصحيحة للسؤال السابق.")
                parsed_questions.append({
                    "type": "multiple_choice",
                    "question": current_question,
                    "options": options,
                    "correct_answer": correct_option
                })
            current_question = line[1:].strip()
            options = []
            correct_option = None
        elif line.startswith("+"):  # خيار
            option_text = line[1:].strip()
            if option_text.endswith("="):  # الإجابة الصحيحة
                option_text = option_text[:-1].strip()
                correct_option = len(options)
            options.append(option_text)
        else:
            raise ValueError("خطأ في التنسيق: يجب أن يبدأ السطر بـ * أو +.")

    if current_question:
        if correct_option is None:
            raise ValueError("لم يتم تحديد الإجابة الصحيحة للسؤال الأخير.")
        parsed_questions.append({
            "type": "multiple_choice",
            "question": current_question,
            "options": options,
            "correct_answer": correct_option
        })

    return parsed_questions

# إرسال الأسئلة كاختبار إلى القناة
def send_polls_to_channel(message):
    if questions:
        for q in questions:
            is_anonymous = True  # لضمان أن التصويت سري
            bot.send_poll(
                chat_id=CHANNEL_ID,
                question=q['question'],
                options=q['options'],
                correct_option_id=q['correct_answer'],
                is_anonymous=is_anonymous,
                type="quiz"  # نوع الاختبار
            )
        bot.send_message(message.chat.id, "✅ تم إرسال الأسئلة كاختبارات سرية إلى القناة!")
        questions.clear()
    else:
        bot.send_message(message.chat.id, "⚠️ لا توجد أسئلة لإرسالها.")

# تشغيل البوت
bot.polling()
