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
    api_url = "https://api.hh.ru/vacancies"
    hh_region_id = 1
    hh_days_since_publication = 20
    collected_vacancies = []
    for page in count(0):
        payload = {
            "period": hh_days_since_publication,
            "text": profession,
            "area": hh_region_id,
            "page": page,
            "per_page": 100,
        }
        response = requests.get(api_url, params=payload)

        response.raise_for_status()
        vacancies = response.json()
        vacancies_found = vacancies.get("found",0)
        collected_vacancies.extend(vacancies.get('items'))
        if page >= vacancies.get("pages")-1:
            break
    return collected_vacancies, vacancies_found


def fetch_superjob_vacancies(profession, secret_key):
    api_url = "https://api.superjob.ru/2.0/vacancies"
    collected_vacancies = []
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
        total_vacancies = vacancies["total"]
        if vacancies["objects"]:
            collected_vacancies.extend(vacancies["objects"])

        if not vacancies["more"]:
            break
    return collected_vacancies, total_vacancies


def predict_rub_salary(salary_from, salary_to):
    if not salary_from:
        return salary_to * 0.8
    if not salary_to:
        return salary_from * 1.2
    return (salary_from + salary_to) / 2


def get_superjob_salary_stats(secret_key):
    average_salaries_by_vacancy = {}

    for profession in PROFESSIONS:
        collected_vacancies, vacancies_found = fetch_superjob_vacancies(
            profession, secret_key
        )
        rub_salaries = []
        for vacancy in collected_vacancies:
            if vacancy['payment_from'] or vacancy['payment_to'] and vacancy['currency'] == 'rub':
                salary = predict_rub_salary(vacancy['payment_from'], vacancy['payment_to'])
                rub_salaries.append(int(salary))
        vacancies_processed = len(rub_salaries)
        if vacancies_processed > 0:
            average_salary = sum(rub_salaries) / vacancies_processed
        else:
            average_salary = 0
        average_salaries_by_vacancy[profession] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": int(average_salary),
        }

    return average_salaries_by_vacancy


def get_hh_salary_stats():
    average_salaries_by_vacancy = {}

    for profession in PROFESSIONS:
        collected_vacancies, vacancies_found = fetch_hh_vacancies(profession)
        rub_salaries = []
        for vacancy in collected_vacancies:  
            if not vacancy["salary"]:
                continue
            if vacancy["salary"]["currency"] == "RUR":
                salary = predict_rub_salary(
                    vacancy["salary"]["from"], vacancy["salary"]["to"]
                )
                rub_salaries.append(int(salary))
        vacancies_processed = len(rub_salaries)
        if vacancies_processed > 0:
            average_salary = sum(rub_salaries) / vacancies_processed
        else:
            average_salary = 0
        average_salaries_by_vacancy[profession] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": int(average_salary),
        }

    return average_salaries_by_vacancy


def build_salary_table(aggregated_vacancy_stats, title):
    table_data = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата",
        ]
    ]
    for vacancy_name, vacancy_stats in aggregated_vacancy_stats.items():
        row = [vacancy_name]
        row.extend(vacancy_stats.values())
        table_data.append(row)
    table = AsciiTable(table_data, title=title)
    return table.table


def main():
    env = Env()
    env.read_env()
    secret_key = env.str("SUPERJOB_SECRET_KEY")
    print(build_salary_table(get_superjob_salary_stats(secret_key), "SuperJob Moscow"))
    print(build_salary_table(get_hh_salary_stats(), "HeadHunter Moscow"))


if __name__ == "__main__":
    main()
