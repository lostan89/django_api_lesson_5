import requests
import json
from environs import Env
from itertools import count
from terminaltables import AsciiTable

PROFESSIONS = [
    "python",
    "java",
    "javascript",
    "php",
    "c++",
    "css",
    "c#",
    "c",
    "go",
    "ruby",
]


def fetch_hh_vacancies(profession):
    api_url = "https://api.hh.ru/vacancies/?"
    page_response_with_vacancies = []
    for page in count(0):
        payload = {
            "period": 20,
            "text": profession,
            "area": 1,
            "page": page,
            "per_page": 100,
        }
        response = requests.get(api_url, params=payload)

        response.raise_for_status()
        vacancies = response.json()
        page_response_with_vacancies.append(vacancies)

        if page > page_response_with_vacancies[0]["pages"]:
            break

    return page_response_with_vacancies


def fetch_superjob_vacancies(profession, secret_key):
    api_url = "https://api.superjob.ru/2.0/vacancies/"
    page_response_with_vacancies = []
    vacancies_per_page = 10
    catalog_vacancies_id = 33
    vacancies_id = 48
    headers = {
        "Host": "api.superjob.ru",
        "X-Api-App-Id": secret_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    for page in count(0):
        params = {
            "page": page,
            "count": vacancies_per_page,
            "keyword": profession,
            "town": "Москва",
            "id_parent": catalog_vacancies_id,
            "key": vacancies_id,
        }
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()
        total = vacancies["total"]
        if vacancies["objects"]:
            page_response_with_vacancies.append(vacancies["objects"])

        if not vacancies["more"]:
            break
    return page_response_with_vacancies, total


def predict_rub_salary(salary_from, salary_to):
    if not salary_from:
        return salary_to * 0.8
    if not salary_to:
        return salary_from * 1.2
    return (salary_from + salary_to) / 2


def get_superjob_salary_stats()(secret_key):
    average_salaries_by_vacancy = {}

    for profession in PROFESSIONS:
        vacancy_pages, vacancies_found = fetch_superjob_vacancies(
            profession, secret_key
        )
        rub_salaries = []
        for vacancy_page in vacancy_pages:
            for vacancy in vacancy_page:
                if (vacancy["payment_from"] or vacancy["payment_to"]) and vacancy[
                    "currency"
                ] == "rub":
                    salary = predict_rub_salary(
                        vacancy["payment_from"], vacancy["payment_to"]
                    )
                    rub_salaries.append(int(salary))
        if not rub_salaries:
            continue
        vacancies_processed = len(rub_salaries)
        average_salary = sum(rub_salaries) / vacancies_processed

        average_salaries_by_vacancy[profession] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": int(average_salary),
        }

    return average_salaries_by_vacancy


def get_hh_salary_stats():
    average_salaries_by_vacancy = {}

    for profession in PROFESSIONS:
        vacancy_pages = fetch_hh_vacancies(profession)
        vacancies_found = vacancy_pages[0]["found"]
        rub_salaries = []
        for vacancy_page in vacancy_pages:
            for vacancy in vacancy_page["items"]:
                if not vacancy["salary"]:
                    continue
                if vacancy["salary"]["currency"] == "RUR":
                    salary = predict_rub_salary(
                        vacancy["salary"]["from"], vacancy["salary"]["to"]
                    )
                    rub_salaries.append(int(salary))
        if not rub_salaries:
            continue
        vacancies_processed = len(rub_salaries)
        average_salary = sum(rub_salaries) / vacancies_processed
        average_salaries_by_vacancy[profession] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": int(average_salary),
        }

    return average_salaries_by_vacancy


def compare_result_to_table(result, title):
    table_data = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата",
        ]
    ]
    for key, value in result.items():
        average_salaries_by_vacancy = [key]
        average_salaries_by_vacancy.extend(value.values())
        table_data.append(average_salaries_by_vacancy)
    table = AsciiTable(table_data, title=title)
    return table.table


def main():
    env = Env()
    env.read_env()
    secret_key = env.str("SUPERJOB_SECRET_KEY")
    print(compare_result_to_table(get_superjob_salary_stats(secret_key), "SuperJob Moscow"))
    print(compare_result_to_table(get_hh_salary_stats(), "HeadHunter Moscow"))


if __name__ == "__main__":
    main()
