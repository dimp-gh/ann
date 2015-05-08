# -*- coding: utf-8 -*-
import csv
import json
from collections import namedtuple, OrderedDict
from random import random, shuffle

import utils

DatasetField = namedtuple('DatasetField', 'name, pretty_name, valid_range')

fields = [
    DatasetField('WBC', 'Лейкоциты', (0.0, 50.0)),
    DatasetField('RBC', 'Эритроциты', (0.0, 10.0)),
    DatasetField('HGB', 'Гемоглобин', (10.0, 300.0)),
    DatasetField('HCT', 'Гематокрит', (0.0, 1.0)),
    DatasetField('MCV', 'Средний объём эритроцита', (0.0, 200.0)),
    DatasetField('MCH', 'Среднее содержание гемоглобина в эритроците', (1.0, 300.0)),
    DatasetField('MCHC', 'Средняя концентрация гемоглобина в эритроците', (100.0, 700.0)),
    DatasetField('PLT', 'Тромбоциты', (0.0, 800.0)),
    DatasetField('LYM%', 'Относительное содержание лимфоцитов', (0.0, 1.0)),
    DatasetField('MXD%', 'Относительное содержание смеси моноцитов, базофилов и эозинофилов', (0.0, 1.0)),
    DatasetField('NEUT%', 'Относительное содержание нейтрофилов', (0.0, 1.0)),
    DatasetField('LYM#', 'Абсолютное содержание лимфоцитов', (0.0, 50.0)),
    DatasetField('MXD#', 'Абсолютное содержание свеми моноцитов, базофилов и эозинофилов', (0.0, 5.0)),
    DatasetField('NEUT#', 'Абсолютное содержание нейтрофилов', (0.0, 100.0)),
    DatasetField('RDW-SD', 'Относительная ширина распределения эритроцитов по объёму', (30.0, 100.0)),
    DatasetField('RDW-CV', 'Относительная ширина распределения эритроцитов по объёму', (0.0, 1.0)),
    DatasetField('PDW', 'Относительная ширина распределения тромбоцитов по объёму', (5.0, 30.0)),
    DatasetField('MPV', 'Средний объем тромбоцитов', (1.0, 15.0)),
    DatasetField('P-LCR', 'Коэффициент больших тромбоцитов', (0.0, 1.0)),
]
field_map = OrderedDict((field.name, field) for field in fields)


def random_float(left, right):
    return left + (right - left) * random()


def make_average_value(field_name):
    field = field_map[field_name]
    min, max = field.valid_range
    center = (min + max) / 2.0
    delta = (max - min) / 100.0
    return random_float(center - delta, center + delta)


def parse_dirty_dataset(path):
    rows = []
    with open(path) as csvfile:
        for row in csv.DictReader(csvfile):
            record = {}
            for field_name, value in row.items():
                if field_name in field_map:
                    value = value.strip().replace(',', '.')
                    if utils.isfloat(value):
                        value = float(value)
                    elif value == '-' or value == '':
                        value = make_average_value(field_name)
                record[field_name] = value
            rows.append(record)
    return rows


def check_dataset(dataset):
    "check dataset for range errors"
    for row in dataset:
        for field_name, value in row.items():
            if field_name in field_map:
                field = field_map[field_name]
                min, max = field.valid_range
                if not (min <= value <= max):
                    print "Record '%s' doesn't fit into ranges in field '%s' (%s </= %s </= %s)" % (row['ФИО'], field_name, min, value, max)
                    return False
    return True


def get_diagnoses(dataset):
    return set(row['Диагноз'] for row in dataset)


def form_dataset(csv_component_paths):
    dataset = []
    for csvpath in csv_component_paths:
        part = parse_dirty_dataset(csvpath)
        dataset.extend(part)

    shuffle(dataset)

    return dataset


def write_dataset_csv(dataset, path):
    with open(path, 'w') as csvfile:
        fieldnames = dataset[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)


def write_dataset_json(dataset, path):
    dataset_j = {}
    dataset_j['fields'] = [
        dict(name=f.name,
             type='float',
             prettyName=f.pretty_name,
             validRange=dict(min=f.valid_range[0], max=f.valid_range[1]))
        for f in fields
    ] + [
        dict(name=tf,
             type='text',
             prettyName=tf)
        for tf in ['ФИО', 'Диагноз', 'Год', '№ карты']
    ]

    dataset_j['dataset'] = dataset

    with open(path, 'w') as jsonfile:
        jsonfile.write(json.dumps(dataset_j, indent=4, ensure_ascii=False))


def main():
    csvs = [
        'peritonitis.csv',
        'appendicitis.csv',
        'hepatitis.csv',
    ]
    dataset = form_dataset(csvs)
    check_dataset(dataset)
    write_dataset_csv(dataset, 'dataset.csv')
    write_dataset_json(dataset, 'dataset.json')


if __name__ == '__main__':
    main()
