def create_dict_with_questions():
    with open('quiz-questions/12koll07.txt', 'r', encoding='KOI8-R') as file:
        file_content = file.read()
    print(file_content)
    questions_and_answers = {}
    sections = file_content.split('\n\n')
    question = None
    answer = None
    for part in sections:
        if part.startswith('Вопрос'):
            part = ' '.join(part.split()[2:])
            question = part
        elif part.startswith('Ответ'):
            part = part.replace('\n', ' ').lstrip(' Ответ:').rstrip('.')
            answer = part
        if question and answer:
            questions_and_answers[question] = answer
    print(questions_and_answers)
    return questions_and_answers



create_dict_with_questions()























# pprint(questions_and_answers)








