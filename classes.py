class Examiner:
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender
        self.current_student = None
        self.total_students = 0
        self.failed_students = 0
        self.working_time = 0
        self.is_busy = False
        self.is_on_lunch = False
        self.lunch_taken = False
        self.mood = None

class Student:
    def __init__(self, name, gender):
        self.name = name
        self.gender = gender
        self.status = "Очередь"
        self.start_time = None
        self.end_time = None
        self.exam_duration = None


class Question:
    def __init__(self, question):
        self.question = question
        self.words = question.split()
        self.correct_answ_count = 0
    

def create_obj_from_file(filename, object_class):
    objects = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                if ' ' in line:
                    name, gender = line.split()
                    object = object_class(name.strip(), gender.strip())
                    objects.append(object)

    except FileNotFoundError:
        print(f"Файл '{filename}' не найден")
        raise
    return objects


def read_questions(filename):
    questions = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            questions = [Question(line.strip()) for line in f if line.strip()]
            
    except FileNotFoundError:
        print(f"Файл '{filename}' не найден")
        exit(1)
    
    return questions 