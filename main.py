import requests
import json
from environs import Env
from itertools import count
from terminaltables import AsciiTable


def get_vacancy_info_headhunter(profession):
    api_url = "https://api.hh.ru/vacancies/?"
    page_response = []
    for page in count(0):
        payload = {
            "period": 20,
            "text": profession,
            "area": 1,
            "page": page,
            "per_page": 20,
        }
        response = requests.get(api_url, params=payload)
        response.raise_for_status()
        page_response.append(response.json())

        if page > page_response[0]["pages"]:
            break

    return page_response


def get_vacancy_info_superjob(profession):
    env = Env()
    env.read_env()
    access_token = env.str("SUPERJOB_ACCESS_TOKEN")
    secret_key = env.str("SUPERJOB_SECRET_KEY")
    code = env.str("SUPERJOB_CODE")
    api_url = "https://api.superjob.ru/2.0/vacancies/"
    page_response = []
    counts = 10
    headers = {
        "Host": "api.superjob.ru",
        "X-Api-App-Id": secret_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {access_token}",
    }
    for page in count(0):
        params = {
            "page": page,
            "count": counts,
            "keyword": profession,
            "town": "Москва",
            "id_parent": 33,
            "key": 48,
        }

        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        page_response.append(response.json())

        if page > page_response[0]["total"] / counts:
            break
    return page_response


def predict_rub_salary_for_HeadHunter(vacancy):
    if vacancy["currency"] != "RUR":
        return None
    if not vacancy["from"]:
        return vacancy["to"] * 0.8
    if not vacancy["to"]:
        return vacancy["from"] * 1.2
    return (vacancy["from"] + vacancy["to"]) / 2


def predict_rub_salary_for_superJob(vacancy):
    if vacancy["currency"] != "rub":
        return None
    if not vacancy["payment_from"]:
        return vacancy["payment_to"] * 0.8
    if not vacancy["payment_to"]:
        return vacancy["payment_from"] * 1.2
    return (vacancy["payment_from"] + vacancy["payment_to"]) / 2


def compare_result_to_table(result_list, title):
    table_data = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата",
        ]
    ]
    for key, value in result_list.items():
        vacancy_info = [key]
        vacancy_info.extend(value.values())
        table_data.append(vacancy_info)
    table = AsciiTable(table_data, title=title)
    return table.table


def compare_superjob_vacancies():
    result_api_request = {}
    professions = [
        'программист python',
        'программист java',
        'программист javascript',
        'программист php',
        'программист c++',
        'программист css',
        'программист c#',
        'программист c',
        'программист go',
        'программист ruby',
    ]

    for profession in professions:
        vacancy_pages = get_vacancy_info_superjob(profession)
        vacancies_found = vacancy_pages[0]["total"]
        vacancies_processed = 0
        salary_list = []
        for vacancy_page in vacancy_pages:
            if not vacancy_page["objects"]:
                continue
            for vacancy in vacancy_page["objects"]:
                salary = predict_rub_salary_for_superJob(vacancy)
                if (
                    vacancy["payment_from"] or vacancy["payment_to"]
                ) and salary != None:
                    vacancies_processed += 1
                    salary_list.append(int(salary))
        if not vacancies_processed:
            continue
        average_salary = sum(salary_list) / vacancies_processed

        result_api_request.update(
            {
                profession: {
                    "vacancies_found": vacancies_found,
                    "vacancies_processed": vacancies_processed,
                    "average_salary": int(average_salary),
                }
            }
        )

    return result_api_request


def compare_hh_vacancies():
    result_api_request = {}
    professions = [
        "программист python",
        "программист java",
        "программист javascript",
        "программист php",
        "программист c++",
        "программист css",
        "программист c#",
        "программист c",
        "программист go",
        "программист ruby",
    ]

    for profession in professions:
        vacancy_pages = get_vacancy_info_headhunter(profession)
        vacancies_found = vacancy_pages[0]["found"]
        vacancies_processed = 0
        salary_list = []
        for vacancy_page in vacancy_pages:
            for vacancy in vacancy_page["items"]:
                if not vacancy["salary"]:
                    continue
                vacancies_processed += 1
                salary = predict_rub_salary_for_HeadHunter(vacancy["salary"])
                if salary:
                    salary_list.append(int(salary))
        average_salary = sum(salary_list) / vacancies_processed
        result_api_request.update(
            {
                profession: {
                    "vacancies_found": vacancies_found,
                    "vacancies_processed": vacancies_processed,
                    "average_salary": int(average_salary),
                }
            }
        )

    return result_api_request


def main():
    print(compare_result_to_table(compare_superjob_vacancies(), "SuperJob Moscow"))
    print(compare_result_to_table(compare_hh_vacancies(),'HeadHunter Moscow'))


if __name__ == "__main__":
    main()
