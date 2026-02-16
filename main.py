import classes
import logic
import time
import multiprocessing
import os
import prettytable

class ExamState:
    """Хранит текущее состояние всей симуляции экзамена"""
    def __init__(self):
        self.start_time = time.time()
        self.students = []
        self.examiners = []
        self.questions = []

    def elapsed_time(self):
        return time.time() - self.start_time

    def get_queue_count(self):
        """Количество студентов в очереди"""
        return sum(1 for s in self.students if s.status == "Очередь")

    def get_passed_count(self):
        return sum(1 for s in self.students if s.status == "Сдал") 


def examiner_works(examiner, student_queue, result_queue, questions, exam_start_time):
    while True:
        try:
            student = student_queue.get(timeout=0.6) #чуть ждет и выбрасывает empty если не берется. CPU не грузится при таком ожидании
            
            result_queue.put({
                'type': 'status_update',
                'examiner_name': examiner.name,
                'current_student': student.name,
                'is_busy': True
            })
            
            student.start_time = time.time()
            examiner.current_student = student.name
            examiner.is_busy = True

            exam_duration = logic.calculate_exam_duration(examiner.name)
            time.sleep(exam_duration)
            is_passed = logic.examine_student(student, examiner, questions, result_queue)
            
            student.end_time = time.time()
            student.status = 'Сдал' if is_passed else 'Провалил'
            examiner.total_students += 1
            if not is_passed:
                examiner.failed_students += 1
            examiner.working_time += exam_duration

            # Отправка результатов в главный процесс, т.к. дочерние процессы работают с копиями объектов
            result_queue.put({
                'type': 'exam_result',
                'student_name': student.name,
                'student_status': student.status,
                'is_passed': is_passed,
                'student_start_time': student.start_time,
                'student_end_time': student.end_time,
                'examiner_name': examiner.name,
                'examiner_current_student': None,  # освободили
                'total_students': examiner.total_students,
                'failed_students': examiner.failed_students,
                'examiner_work_time': examiner.working_time,
                'exam_duration': exam_duration
            })

            examiner.current_student = None
            examiner.is_busy = False

            if logic.should_lunch(examiner, exam_start_time):
                lunch_duration = logic.on_lunch(examiner)

                # Отправка информации об обеде
                result_queue.put({
                    'type': 'lunch',
                    'examiner_name': examiner.name,
                    'lunch_duration': lunch_duration,
                    'examiner_work_time': examiner.working_time,
                    'lunch_taken': True
                })
        
        except multiprocessing.queues.Empty: break

def create_st_table(students):
    student_table = prettytable.PrettyTable()
    student_table.field_names = ["Студент", "Статус"]
    student_table.align["Студент"] = "l"
    student_table.align["Статус"] = "c"

    status_order = {"Очередь": 0, "Сдал": 1, "Провалил": 2}
    sorted_students = sorted(students, key=lambda s: status_order[s.status])
    
    for s in sorted_students:
        student_table.add_row([s.name, s.status])
    return student_table

def display_simulation(exam_state):
    os.system('cls' if os.name == 'nt' else 'clear')
    output_lines = []

    student_table = create_st_table(exam_state.students)
    output_lines.extend(str(student_table).split('\n'))
    output_lines.append("")

    examiner_table = prettytable.PrettyTable()
    examiner_table.field_names = ["Экзаменатор", "Текущий студент", "Всего студентов", "Завалил", "Время работы"]
    examiner_table.align["Экзаменатор"] = "l"
    examiner_table.align["Текущий студент"] = "l"
    examiner_table.align["Всего студентов"] = "c"
    examiner_table.align["Завалил"] = "c"
    examiner_table.align["Время работы"] = "c"

    for ex in exam_state.examiners:
        current_st = ex.current_student if ex.current_student else "-"
        total_st = ex.total_students
        failed_st = ex.failed_students
        working_time = f"{ex.working_time:5.2f}"

        examiner_table.add_row([ex.name, current_st, total_st, failed_st, working_time])

    output_lines.extend(str(examiner_table).split('\n'))
    output_lines.append("")

    queue_count = exam_state.get_queue_count()

    output_lines.append(f"Осталось в очереди: {queue_count} из {len(exam_state.students)}")
    output_lines.append(f"Время с момента начала экзамена: {exam_state.elapsed_time():.2f}")

    final_output = '\n'.join(output_lines)
    print(final_output)


def display_after_exam(exam_state):
    os.system('cls' if os.name == 'nt' else 'clear')
    output_lines = []

    student_table = create_st_table(exam_state.students)
    output_lines.extend(str(student_table).split('\n'))
    output_lines.append("")

    examiner_table = prettytable.PrettyTable()
    examiner_table.field_names = ["Экзаменатор", "Всего студентов", "Завалил", "Время работы"]
    examiner_table.align["Экзаменатор"] = "l"
    examiner_table.align["Всего студентов"] = "c"
    examiner_table.align["Завалил"] = "c"
    examiner_table.align["Время работы"] = "c"

    for ex in exam_state.examiners:
        total_st = ex.total_students
        failed_st = ex.failed_students
        working_time = f"{ex.working_time:5.2f}"
        examiner_table.add_row([ex.name, total_st, failed_st, working_time])

    output_lines.extend(str(examiner_table).split('\n'))
    output_lines.append("")

    output_lines.append(f"Время с момента начала экзамена и до момента его завершения: {exam_state.elapsed_time():.2f}")
    
    passed_st = [st for st in exam_state.students if st.status == "Сдал"]
    fastest_time = min(st.exam_duration for st in passed_st if st.exam_duration is not None)
    best_st = [st.name for st in passed_st if abs(st.exam_duration - fastest_time) < 0.01]
    output_lines.append(f"Имена лучших студентов: {', '.join(best_st)}")

    best_rate = min(ex.failed_students / ex.total_students for ex in exam_state.examiners)
    best_ex = [ex.name for ex in exam_state.examiners if abs(ex.failed_students / ex.total_students - best_rate < 0.01)]
    output_lines.append(f"Имена лучших экзаменаторов: {', '.join(best_ex)}")

    failed_st = [st for st in exam_state.students if st.status == "Провалил"]
    fastest_time2 = min(st.exam_duration for st in failed_st if st.exam_duration is not None)
    expelled_st = [st.name for st in failed_st if abs(st.exam_duration - fastest_time2) < 0.01]
    output_lines.append(f"Имена студентов, которых после экзамена отчислят: {', '.join(expelled_st)}")

    best_q = max(q.correct_answ_count for q in exam_state.questions if q.correct_answ_count is not None)
    best_questions = [q.question for q in exam_state.questions if abs(q.correct_answ_count - best_q) < 0.01]
    output_lines.append(f"Лучшие вопросы: {', '.join(best_questions)}")

    verdict = "экзамен удался" if len(passed_st) / len(exam_state.students) > 0.85 else "экзамен не удался"
    output_lines.append(f"Вывод: {verdict}")

    final_output = '\n'.join(output_lines)
    print(final_output)

def simulate_exam():
    
    exam_state = ExamState()
    exam_state.students = classes.create_obj_from_file('students.txt', classes.Student)
    exam_state.examiners = classes.create_obj_from_file('examiners.txt', classes.Examiner)
    exam_state.questions = classes.read_questions('questions.txt')

    student_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    for st in exam_state.students:
        student_queue.put(st)

    processes = []
    for ex in exam_state.examiners:
        p = multiprocessing.Process(target=examiner_works, args=(ex, student_queue, result_queue, exam_state.questions, exam_state.start_time))
        processes.append(p)
        p.start()

    try:
        # Главный цикл обработки результатов 
        while True:
            if exam_state.get_queue_count() == 0: break
            try:
                result = result_queue.get_nowait()

                if result.get('type') == 'lunch':
                    for ex in exam_state.examiners:
                        if ex.name == result['examiner_name']:
                            ex.working_time = result['examiner_work_time']
                            ex.lunch_taken = result.get('lunch_taken', True)
                            break
                elif result.get('type') == 'status_update':
                    for ex in exam_state.examiners:
                        if ex.name == result['examiner_name']:
                            ex.current_student = result['current_student']
                            ex.is_busy = result['is_busy']
                            break
                elif result.get('type') == 'question_correct':
                    for q in exam_state.questions:
                        if q.question == result['question_text']:
                            q.correct_answ_count += 1
                            break
                else:  # exam_result
                    # Обновляем студента
                    for st in exam_state.students:
                        if st.name == result['student_name']:
                            st.status = result['student_status']
                            st.start_time = result['student_start_time']
                            st.end_time = result['student_end_time']
                            st.exam_duration = st.end_time - st.start_time
                            break
                    
                    # Обновляем экзаменатора  
                    for ex in exam_state.examiners:
                        if ex.name == result['examiner_name']:
                            ex.total_students = result['total_students']
                            ex.failed_students = result['failed_students']
                            ex.working_time = result['examiner_work_time']
                            ex.current_student = result['examiner_current_student']
                            break
                
            except multiprocessing.queues.Empty:
                # Нет результатов в очереди 
                pass
            
            # Обновляем отображение
            display_simulation(exam_state)
            time.sleep(0.5)  # Частота обновлений
        
    except KeyboardInterrupt:
        print("\nЭкзамен прерван пользователем!")
    
    finally:
        print("\nЗавершение процессов экзаменаторов...")
        for p in processes:
            p.terminate()
            p.join()
                    
    display_after_exam(exam_state)


if __name__ == '__main__':
    simulate_exam()