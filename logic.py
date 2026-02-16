import random
import time

PHI = (1 + 5**0.5) / 2

def golden_ratio_probabilities(n):
    if n <= 0: return []
    probs = []
    remaining = 1.0
    
    for i in range(n):
        if i < n-1:
            prob = remaining / PHI
        else:
            prob = remaining

        probs.append(prob)
        remaining = remaining - prob
    
    return probs

def choose_word_by_golden_ratio(words, gender):
    if not words: return ""
    n = len(words)
    probs = golden_ratio_probabilities(n)
    
    if gender == "Ж":
        probs = probs[::-1]
    
    return random.choices(words, weights=probs)[0]

def examine_one_quest(question_words, st_gender, ex_gender):
    st_answer = choose_word_by_golden_ratio(question_words, st_gender)
    correct_answers = []
    remaining_words = question_words.copy() #чтобы не изменять question_words
    
    while remaining_words:
        if not correct_answers or random.random() < 1/3:
            ex_answer = choose_word_by_golden_ratio(remaining_words, ex_gender)
            correct_answers.append(ex_answer)
            remaining_words.remove(ex_answer)
        else:
            break

    return st_answer in correct_answers

def determine_ex_mood():
    m = random.random()
    if m < 1/8:
        return 'bad'
    elif m < 1/8 + 1/4:
        return 'good'
    else:
        return 'neutral'
    
def examine_student(student, examiner, questions, result_queue):
    selected_questions = random.sample(questions, min(3, len(questions)))
    correct_count = 0
    for q in selected_questions:
        if examine_one_quest(q.words, student.gender, examiner.gender):
            correct_count += 1
            result_queue.put({
                'type': 'question_correct',
                'question_text': q.question,
                'increment': 1
            })

    examiner.mood = determine_ex_mood()
    if examiner.mood == 'bad':
        return False
    elif examiner.mood == 'good':
        return True
    else:
        total = len(selected_questions)
        return correct_count > (total - correct_count)

def calculate_exam_duration(examiner_name):
    length = len(examiner_name)
    min = length - 1
    max = length + 1
    return random.uniform(min, max) #вернет число типа float в заданном интервале

def should_lunch(examiner, exam_start_time):
    current_time = time.time()
    elapsed_time = current_time - exam_start_time
    return(elapsed_time > 30 and not examiner.lunch_taken and
                                not examiner.is_on_lunch)

def on_lunch(examiner):
    lunch_duration = random.uniform(12, 18)
    examiner.is_on_lunch = True
    time.sleep(lunch_duration)
    examiner.is_on_lunch = False
    examiner.working_time += lunch_duration
    examiner.lunch_taken = True
    return lunch_duration